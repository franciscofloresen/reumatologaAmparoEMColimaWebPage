import json
import boto3
import os
from datetime import datetime, time
from decimal import Decimal
import gcal_helper

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

# Available time slots by day of week (0=Monday, 6=Sunday)
AVAILABLE_SLOTS = {
    0: [('16:30', '18:00')],  # Monday
    1: [('18:30', '19:30')],  # Tuesday
    2: [('16:30', '18:00')],  # Wednesday
    3: [('18:30', '19:30')],  # Thursday
    4: [('17:00', '19:30')],  # Friday
    5: [('11:00', '13:30')],  # Saturday
    6: []  # Sunday - Not available
}

DAY_NAMES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

def is_time_available(date_str, time_str):
    """Check if the requested time slot is within available hours"""
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    day_of_week = date_obj.weekday()
    
    # Check if day is available
    if day_of_week not in AVAILABLE_SLOTS or not AVAILABLE_SLOTS[day_of_week]:
        return False, f"{DAY_NAMES[day_of_week]} no está disponible"
    
    # Parse requested time
    req_time = datetime.strptime(time_str, '%H:%M').time()
    
    # Check if time falls within any available slot
    for start_str, end_str in AVAILABLE_SLOTS[day_of_week]:
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
        
        if start_time <= req_time < end_time:
            return True, None
    
    # Build available times message
    slots = [f"{s}-{e}" for s, e in AVAILABLE_SLOTS[day_of_week]]
    return False, f"Horario no disponible. Horarios disponibles para {DAY_NAMES[day_of_week]}: {', '.join(slots)}"

def check_slot_conflict(table, date_str, time_str):
    """Check if there's already a reservation at this date/time"""
    response = table.scan(
        FilterExpression='preferredDate = :date AND preferredTime = :time AND #status <> :cancelled',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':date': date_str,
            ':time': time_str,
            ':cancelled': 'cancelled'
        }
    )
    return len(response.get('Items', [])) > 0

def handle_availability(event):
    query_params = event.get('queryStringParameters', {})
    date_str = query_params.get('date')
    if not date_str:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Missing date parameter'})
        }
        
    table = dynamodb.Table(DYNAMODB_TABLE)
    # Use the DateIndex to find all reservations for this date
    response = table.query(
        IndexName='DateIndex',
        KeyConditionExpression='preferredDate = :date',
        FilterExpression='#status <> :cancelled',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':date': date_str,
            ':cancelled': 'cancelled'
        }
    )
    
    booked_times = [item['preferredTime'] for item in response.get('Items', [])]
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'bookedTimes': booked_times})
    }

def lambda_handler(event, context):
    try:
        http_method = event.get('requestContext', {}).get('http', {}).get('method', 'POST')
        path = event.get('requestContext', {}).get('http', {}).get('path', '/reservations')
        
        if http_method == 'GET' and '/availability' in path:
            return handle_availability(event)
            
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'phone', 'preferredDate', 'preferredTime', 'consultationType']
        for field in required_fields:
            if field not in body or not body[field]:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': f'Campo requerido: {field}'})
                }
        
        date_str = body['preferredDate']
        time_str = body['preferredTime']
        
        # Validate date is not in the past
        req_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if req_date < datetime.now().date():
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'No se pueden hacer reservas en fechas pasadas'})
            }
        
        # Check if time slot is available for this day
        is_available, error_msg = is_time_available(date_str, time_str)
        if not is_available:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': error_msg})
            }
        
        # Check for conflicts
        table = dynamodb.Table(DYNAMODB_TABLE)
        if check_slot_conflict(table, date_str, time_str):
            return {
                'statusCode': 409,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Este horario ya está reservado. Por favor seleccione otro horario.'})
            }
        
        # Generate reservation ID
        reservation_id = f"{date_str}-{time_str.replace(':', '')}-{body['phone'][-4:]}"
        
        # Prepare reservation data
        reservation = {
            'reservationId': reservation_id,
            'firstName': body['firstName'],
            'lastName': body['lastName'],
            'phone': body['phone'],
            'email': body.get('email', ''),
            'preferredDate': date_str,
            'preferredTime': time_str,
            'consultationType': body['consultationType'],
            'reason': body.get('reason', ''),
            'status': 'confirmed',
            'createdAt': datetime.utcnow().isoformat()
        }
        
        # Save to DynamoDB
        table.put_item(Item=reservation)
        
        # Create Google Calendar event
        try:
            event_id = gcal_helper.create_calendar_event(reservation)
            if event_id:
                table.update_item(
                    Key={'reservationId': reservation_id},
                    UpdateExpression='SET calendarEventId = :eid',
                    ExpressionAttributeValues={':eid': event_id}
                )
        except Exception as e:
            print(f"Failed to create calendar event: {str(e)}")
            # Continue with reservation process even if calendar fails
        
        # Format date for display
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%d de %B de %Y')
        day_name = DAY_NAMES[date_obj.weekday()]
        
        # Email to doctor
        doctor_message = f"""
Nueva Reserva Confirmada

ID de Reserva: {reservation_id}
Paciente: {body['firstName']} {body['lastName']}
Teléfono: {body['phone']}
Email: {body.get('email', 'No proporcionado')}

Fecha: {day_name}, {formatted_date}
Hora: {time_str}
Tipo de Consulta: {body['consultationType']}
Motivo: {body.get('reason', 'No especificado')}

Estado: Confirmada
        """
        
        # Send to doctor via SNS topic
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='Nueva Reserva de Cita Confirmada',
            Message=doctor_message
        )
        
        # Email to patient directly (if email provided)
        patient_email = body.get('email', '').strip()
        if patient_email:
            patient_message_html = f"""
            <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                <div style="background-color: #2563eb; color: white; padding: 20px; text-align: center;">
                    <h2 style="margin: 0;">Confirmación de Cita</h2>
                </div>
                <div style="padding: 20px;">
                    <p>Estimado/a <strong>{body['firstName']} {body['lastName']}</strong>,</p>
                    <p>Su cita ha sido confirmada exitosamente.</p>
                    
                    <h3 style="color: #2563eb; border-bottom: 1px solid #e5e7eb; padding-bottom: 5px;">Detalles de su cita</h3>
                    <ul style="list-style-type: none; padding-left: 0;">
                        <li>📅 <strong>Fecha:</strong> {day_name}, {formatted_date}</li>
                        <li>⏰ <strong>Hora:</strong> {time_str}</li>
                        <li>🩺 <strong>Tipo:</strong> {body['consultationType']}</li>
                        <li>🔖 <strong>ID:</strong> {reservation_id}</li>
                    </ul>

                    <h3 style="color: #2563eb; border-bottom: 1px solid #e5e7eb; padding-bottom: 5px;">Ubicación</h3>
                    <p>Avenida la Paz 46 - 2<br>28017 Colima COL, México</p>

                    <div style="background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 10px; margin-top: 20px;">
                        <strong>Importante:</strong>
                        <ul style="margin: 5px 0 0 0; padding-left: 20px;">
                            <li>Por favor llegue 10 minutos antes de su cita.</li>
                            <li>Traiga su identificación y estudios previos si los tiene.</li>
                            <li>Si necesita cancelar o reprogramar, contacte con anticipación.</li>
                        </ul>
                    </div>

                    <p style="margin-top: 30px;">Saludos cordiales,<br>
                    <strong>Dra. María Amparo Enríquez Maldonado</strong><br>
                    Reumatóloga</p>
                </div>
            </div>
            """
            
            try:
                # Send directly to patient email using Gmail API
                gcal_helper.send_email(
                    to_email=patient_email,
                    subject='Confirmación de Cita - Dra. Enríquez',
                    body_html=patient_message_html
                )
            except Exception as e:
                # Fallback to SNS if SES not configured
                print(f"SES error, using SNS fallback: {str(e)}")
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject=f'Confirmación de Cita para {body["firstName"]} {body["lastName"]}',
                    Message=f"ENVIAR A: {patient_email}\n\n{patient_message}"
                )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'message': 'Reserva confirmada exitosamente',
                'reservationId': reservation_id,
                'date': formatted_date,
                'time': time_str
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Error interno del servidor'})
        }
