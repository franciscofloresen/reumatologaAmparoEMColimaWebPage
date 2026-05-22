import json
import boto3
import os
from boto3.dynamodb.conditions import Attr
import gcal_helper

dynamodb = boto3.resource('dynamodb')
DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']

def lambda_handler(event, context):
    try:
        http_method = event['requestContext']['http']['method']
        path = event['rawPath']
        
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        # GET /appointments - List all appointments
        if http_method == 'GET' and path == '/appointments':
            response = table.scan()
            items = response.get('Items', [])
            
            # Filter out zombie records (e.g. from sync script deletions)
            valid_items = [item for item in items if 'preferredDate' in item]
            
            # Sort by date, newest first
            valid_items.sort(key=lambda x: f"{x.get('preferredDate', '')} {x.get('preferredTime', '')}", reverse=True)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(valid_items, default=str)
            }
        
        # PUT /appointments/{id} - Update appointment status
        elif http_method == 'PUT' and '/appointments/' in path:
            reservation_id = path.split('/')[-1]
            body = json.loads(event.get('body', '{}'))
            new_status = body.get('status')
            
            if not new_status:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Status is required'})
                }
            
            # Get item first to find calendarEventId
            response = table.get_item(Key={'reservationId': reservation_id})
            item = response.get('Item')
            
            table.update_item(
                Key={'reservationId': reservation_id},
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': new_status}
            )
            
            # Sync to Google Calendar
            if item and item.get('calendarEventId'):
                try:
                    gcal_helper.update_calendar_event(item['calendarEventId'], {'status': new_status})
                except Exception as e:
                    print(f"Error updating calendar event: {str(e)}")
                    
            # Send update email to patient
            if item and item.get('email'):
                email_html = f"""
                <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                    <div style="background-color: #f59e0b; color: white; padding: 20px; text-align: center;">
                        <h2 style="margin: 0;">Actualización de Cita</h2>
                    </div>
                    <div style="padding: 20px;">
                        <p>Estimado/a <strong>{item.get('firstName', '')} {item.get('lastName', '')}</strong>,</p>
                        <p>El estado de su cita ha sido actualizado a: <strong>{new_status.upper()}</strong></p>
                        <p>Si tiene alguna duda, por favor contáctenos.</p>
                        <p style="margin-top: 30px;">Saludos cordiales,<br><strong>Dra. María Amparo Enríquez Maldonado</strong></p>
                    </div>
                </div>
                """
                gcal_helper.send_email(item['email'], "Actualización de Cita - Dra. Enríquez", email_html)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'message': 'Status updated successfully'})
            }
        
        # DELETE /appointments/{id} - Delete appointment
        elif http_method == 'DELETE' and '/appointments/' in path:
            reservation_id = path.split('/')[-1]
            
            # Get item first to find calendarEventId
            response = table.get_item(Key={'reservationId': reservation_id})
            item = response.get('Item')
            
            table.delete_item(Key={'reservationId': reservation_id})
            
            # Sync to Google Calendar
            if item and item.get('calendarEventId'):
                try:
                    gcal_helper.delete_calendar_event(item['calendarEventId'])
                except Exception as e:
                    print(f"Error deleting calendar event: {str(e)}")

            # Send cancellation email to patient
            if item and item.get('email'):
                email_html = f"""
                <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                    <div style="background-color: #dc2626; color: white; padding: 20px; text-align: center;">
                        <h2 style="margin: 0;">Cancelación de Cita</h2>
                    </div>
                    <div style="padding: 20px;">
                        <p>Estimado/a <strong>{item.get('firstName', '')} {item.get('lastName', '')}</strong>,</p>
                        <p>Le informamos que su cita programada para el <strong>{item.get('preferredDate', '')}</strong> a las <strong>{item.get('preferredTime', '')}</strong> ha sido cancelada.</p>
                        <p>Puede programar una nueva cita a través de nuestro sitio web cuando lo desee.</p>
                        <p style="margin-top: 30px;">Saludos cordiales,<br><strong>Dra. María Amparo Enríquez Maldonado</strong></p>
                    </div>
                </div>
                """
                gcal_helper.send_email(item['email'], "Cancelación de Cita - Dra. Enríquez", email_html)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'message': 'Reservation deleted successfully'})
            }
        
        # GET /testimonies - List all testimonies
        elif http_method == 'GET' and path == '/testimonies':
            test_table = dynamodb.Table(os.environ['TESTIMONIES_TABLE'])
            response = test_table.scan()
            items = response.get('Items', [])
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(items, default=str)
            }
            
        # POST /testimonies - Create new testimony
        elif http_method == 'POST' and path == '/testimonies':
            test_table = dynamodb.Table(os.environ['TESTIMONIES_TABLE'])
            body = json.loads(event.get('body', '{}'))
            test_table.put_item(Item=body)
            return {
                'statusCode': 201,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'message': 'Testimony created'})
            }
            
        # PUT /testimonies/{id} - Update testimony
        elif http_method == 'PUT' and '/testimonies/' in path:
            test_id = path.split('/')[-1]
            test_table = dynamodb.Table(os.environ['TESTIMONIES_TABLE'])
            body = json.loads(event.get('body', '{}'))
            body['id'] = test_id
            test_table.put_item(Item=body)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'message': 'Testimony updated'})
            }
            
        # DELETE /testimonies/{id} - Delete testimony
        elif http_method == 'DELETE' and '/testimonies/' in path:
            test_id = path.split('/')[-1]
            test_table = dynamodb.Table(os.environ['TESTIMONIES_TABLE'])
            test_table.delete_item(Key={'id': test_id})
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'message': 'Testimony deleted'})
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Internal server error'})
        }
