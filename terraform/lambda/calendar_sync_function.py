import json
import boto3
import os
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
import gcal_helper

dynamodb = boto3.resource('dynamodb')
ssm = boto3.client('ssm')
DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
SYNC_TOKEN_PARAM = '/reumatologia-app/google-sync-token'

# Map Google Calendar colors to our statuses
COLOR_TO_STATUS = {
    '2': 'confirmed',   # Sage (green)
    '9': 'completed',   # Blueberry (blue)
    '11': 'cancelled',  # Tomato (red)
    '5': 'pending',     # Banana (yellow)
}

def get_sync_token():
    try:
        response = ssm.get_parameter(Name=SYNC_TOKEN_PARAM)
        return response['Parameter']['Value']
    except Exception:
        return None

def save_sync_token(token):
    try:
        ssm.put_parameter(
            Name=SYNC_TOKEN_PARAM,
            Value=token,
            Type='String',
            Overwrite=True
        )
    except Exception as e:
        print(f"Error saving sync token: {e}")

def parse_calendar_datetime(dt_dict):
    """Parse Google Calendar datetime object to our date/time format."""
    if 'dateTime' in dt_dict:
        # Format: 2026-03-16T16:30:00-06:00
        dt = datetime.fromisoformat(dt_dict['dateTime'])
        return dt.strftime('%Y-%m-%d'), dt.strftime('%H:%M')
    elif 'date' in dt_dict:
        # All-day event
        return dt_dict['date'], '00:00'
    return None, None

def lambda_handler(event, context):
    print("Starting Calendar Sync...")
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    # 1. Get last sync token
    sync_token = get_sync_token()
    
    # 2. Get changes from Google Calendar
    events, next_sync_token = gcal_helper.get_recent_changes(sync_token)
    
    if not events:
        print("No changes found in Google Calendar.")
    else:
        print(f"Found {len(events)} changed events.")
        
    # 3. Process each changed event
    for cal_event in events:
        event_id = cal_event.get('id')
        status = cal_event.get('status') # 'confirmed' or 'cancelled' in GCal terms
        
        # Check if this event originated from our web app
        reservation_id = gcal_helper.parse_reservation_id_from_event(cal_event)
        
        if reservation_id:
            # EVENT ORIGINATED FROM WEB APP
            if status == 'cancelled':
                # Event was deleted in Google Calendar
                print(f"Web event deleted in GCal. Cancelling reservation {reservation_id}")
                table.update_item(
                    Key={'reservationId': reservation_id},
                    UpdateExpression='SET #s = :status',
                    ExpressionAttributeNames={'#s': 'status'},
                    ExpressionAttributeValues={':status': 'cancelled'}
                )
            else:
                # Event was updated in Google Calendar (time changed)
                date_str, time_str = parse_calendar_datetime(cal_event['start'])
                color_id = cal_event.get('colorId')
                new_status = COLOR_TO_STATUS.get(color_id, 'confirmed')
                
                print(f"Updating reservation {reservation_id} with time {date_str} {time_str} and status {new_status}")
                table.update_item(
                    Key={'reservationId': reservation_id},
                    UpdateExpression='SET preferredDate = :d, preferredTime = :t, #s = :status',
                    ExpressionAttributeNames={'#s': 'status'},
                    ExpressionAttributeValues={
                        ':d': date_str,
                        ':t': time_str,
                        ':status': new_status
                    }
                )
        else:
            # EVENT ORIGINATED FROM GOOGLE CALENDAR
            # Check if we already have it in DynamoDB
            response = table.query(
                IndexName='CalendarEventIndex',
                KeyConditionExpression=Key('calendarEventId').eq(event_id)
            )
            items = response.get('Items', [])
            
            if status == 'cancelled':
                # Deleted in GCal
                if items:
                    print(f"GCal event deleted. Cancelling reservation {items[0]['reservationId']}")
                    table.update_item(
                        Key={'reservationId': items[0]['reservationId']},
                        UpdateExpression='SET #s = :status',
                        ExpressionAttributeNames={'#s': 'status'},
                        ExpressionAttributeValues={':status': 'cancelled'}
                    )
            else:
                # Created or Updated in GCal
                date_str, time_str = parse_calendar_datetime(cal_event['start'])
                
                if items:
                    # Update existing
                    print(f"GCal event updated. Syncing to DynamoDB {items[0]['reservationId']}")
                    color_id = cal_event.get('colorId')
                    new_status = COLOR_TO_STATUS.get(color_id, 'confirmed')
                    
                    table.update_item(
                        Key={'reservationId': items[0]['reservationId']},
                        UpdateExpression='SET preferredDate = :d, preferredTime = :t, #s = :status',
                        ExpressionAttributeNames={'#s': 'status'},
                        ExpressionAttributeValues={
                            ':d': date_str,
                            ':t': time_str,
                            ':status': new_status
                        }
                    )
                else:
                    # Create new reservation in DynamoDB
                    # Extract name from summary (e.g. "Cita: Juan Perez" -> "Juan", "Perez")
                    summary = cal_event.get('summary', 'Cita de Calendario')
                    name_parts = summary.replace('Cita:', '').strip().split(' ', 1)
                    first_name = name_parts[0] if len(name_parts) > 0 else 'Cita'
                    last_name = name_parts[1] if len(name_parts) > 1 else 'Manual'
                    
                    # Generate a reservation ID
                    new_res_id = f"GCAL-{date_str.replace('-','')}-{time_str.replace(':','')}"
                    
                    print(f"New GCal event found. Creating reservation {new_res_id}")
                    reservation = {
                        'reservationId': new_res_id,
                        'firstName': first_name,
                        'lastName': last_name,
                        'phone': 'Agregado en Calendario',
                        'email': '',
                        'preferredDate': date_str,
                        'preferredTime': time_str,
                        'consultationType': 'Consulta General',
                        'reason': cal_event.get('description', ''),
                        'status': 'confirmed',
                        'createdAt': datetime.utcnow().isoformat(),
                        'calendarEventId': event_id
                    }
                    table.put_item(Item=reservation)
                    
                    # Add [WEB] tag so we know it's synced if it gets updated again
                    gcal_helper.update_calendar_event(event_id, {}, reservation=reservation)
    
    # 4. Save new sync token
    if next_sync_token and next_sync_token != sync_token:
        save_sync_token(next_sync_token)
        print("Sync token updated.")
        
    return {
        'statusCode': 200,
        'body': json.dumps({'message': f"Synced {len(events)} events"})
    }
