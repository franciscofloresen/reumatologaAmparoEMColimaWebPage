"""
Google Calendar Helper Module
Shared utility for creating, updating, and deleting Google Calendar events
from reservation data. Manages OAuth2 tokens via AWS SSM Parameter Store.
"""
import json
import os
import boto3
from datetime import datetime, timedelta

# Google API imports (from Lambda Layer)
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import base64
from email.message import EmailMessage

ssm = boto3.client('ssm')

# Cache credentials across Lambda invocations
_cached_credentials = None
_cached_service = None

# Consultation duration in minutes
CONSULTATION_DURATION = 30

# Event colors in Google Calendar (colorId)
# 1=Lavender, 2=Sage, 3=Grape, 4=Flamingo, 5=Banana,
# 6=Tangerine, 7=Peacock, 8=Graphite, 9=Blueberry, 10=Basil, 11=Tomato
COLOR_MAP = {
    'confirmed': '2',    # Sage (green)
    'completed': '9',    # Blueberry (blue)
    'cancelled': '11',   # Tomato (red)
    'pending': '5',      # Banana (yellow)
}

CONSULTATION_LABELS = {
    'primera-vez': 'Primera Vez',
    'seguimiento': 'Seguimiento',
    'urgente': 'Urgente',
}

LOCATION = 'Avenida la Paz 46 - 2, 28017 Colima COL, México'


def _get_ssm_param(name):
    """Retrieve a parameter from SSM Parameter Store."""
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response['Parameter']['Value']


def _get_credentials():
    """Build and cache Google OAuth2 credentials from SSM-stored tokens."""
    global _cached_credentials

    if _cached_credentials and _cached_credentials.valid:
        return _cached_credentials

    client_id = _get_ssm_param('/reumatologia-app/google-client-id')
    client_secret = _get_ssm_param('/reumatologia-app/google-client-secret')
    refresh_token = _get_ssm_param('/reumatologia-app/google-refresh-token')

    _cached_credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri='https://oauth2.googleapis.com/token',
    )

    # Force a token refresh
    _cached_credentials.refresh(Request())

    return _cached_credentials


def get_calendar_service():
    """Build and return an authenticated Google Calendar API service."""
    global _cached_service

    if _cached_service:
        try:
            creds = _get_credentials()
            if creds.valid:
                return _cached_service
        except Exception:
            _cached_service = None

    creds = _get_credentials()
    _cached_service = build('calendar', 'v3', credentials=creds, cache_discovery=False)
    return _cached_service


def get_calendar_id():
    """Get the target Google Calendar ID."""
    return 'primary'


def create_calendar_event(reservation):
    """
    Create a Google Calendar event from a reservation dict.
    Returns the Google Calendar event ID, or None on failure.
    """
    try:
        service = get_calendar_service()
        calendar_id = get_calendar_id()

        consultation_type = CONSULTATION_LABELS.get(
            reservation.get('consultationType', ''), reservation.get('consultationType', '')
        )

        # Build event start/end times
        date_str = reservation['preferredDate']
        time_str = reservation['preferredTime']
        start_dt = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
        end_dt = start_dt + timedelta(minutes=CONSULTATION_DURATION)

        # Build description with metadata tag for sync
        description_lines = [
            f"[WEB] ID: {reservation['reservationId']}",
            f"Teléfono: {reservation.get('phone', 'N/A')}",
            f"Email: {reservation.get('email', 'No proporcionado')}",
            f"Tipo: {consultation_type}",
        ]
        if reservation.get('reason'):
            description_lines.append(f"Motivo: {reservation['reason']}")
        description_lines.append(f"\nEstado: {reservation.get('status', 'confirmed')}")

        event_body = {
            'summary': f"Cita: {reservation['firstName']} {reservation['lastName']} ({consultation_type})",
            'location': LOCATION,
            'description': '\n'.join(description_lines),
            'start': {
                'dateTime': start_dt.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'America/Mexico_City',
            },
            'end': {
                'dateTime': end_dt.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'America/Mexico_City',
            },
            'colorId': COLOR_MAP.get(reservation.get('status', 'confirmed'), '2'),
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 60},
                    {'method': 'popup', 'minutes': 15},
                ],
            },
        }

        event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        print(f"Calendar event created: {event.get('id')}")
        return event.get('id')

    except Exception as e:
        print(f"Error creating calendar event: {str(e)}")
        return None


def update_calendar_event(event_id, updates, reservation=None):
    """
    Update an existing Google Calendar event.
    'updates' is a dict that may contain: status, preferredDate, preferredTime, etc.
    'reservation' is the full current reservation data (optional, for rebuilding description).
    Returns True on success, False on failure.
    """
    try:
        service = get_calendar_service()
        calendar_id = get_calendar_id()

        # Fetch the current event
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        # Update color based on status
        new_status = updates.get('status')
        if new_status:
            event['colorId'] = COLOR_MAP.get(new_status, '2')

            # Update description with new status
            desc = event.get('description', '')
            if 'Estado:' in desc:
                lines = desc.split('\n')
                lines = [l if not l.startswith('Estado:') else f"Estado: {new_status}" for l in lines]
                event['description'] = '\n'.join(lines)

        # Update time if changed
        new_date = updates.get('preferredDate')
        new_time = updates.get('preferredTime')
        if new_date or new_time:
            current_start = event['start'].get('dateTime', '')
            if current_start:
                current_dt = datetime.fromisoformat(current_start.replace('Z', '+00:00'))
                date_str = new_date or current_dt.strftime('%Y-%m-%d')
                time_str = new_time or current_dt.strftime('%H:%M')
            else:
                date_str = new_date or ''
                time_str = new_time or '00:00'

            start_dt = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
            end_dt = start_dt + timedelta(minutes=CONSULTATION_DURATION)

            event['start'] = {
                'dateTime': start_dt.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'America/Mexico_City',
            }
            event['end'] = {
                'dateTime': end_dt.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'America/Mexico_City',
            }

        # Update name if changed
        first = updates.get('firstName')
        last = updates.get('lastName')
        if first or last:
            res = reservation or {}
            f_name = first or res.get('firstName', '')
            l_name = last or res.get('lastName', '')
            c_type = CONSULTATION_LABELS.get(
                updates.get('consultationType', res.get('consultationType', '')), ''
            )
            if f_name and l_name:
                event['summary'] = f"Cita: {f_name} {l_name} ({c_type})"

        service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
        print(f"Calendar event updated: {event_id}")
        return True

    except Exception as e:
        print(f"Error updating calendar event: {str(e)}")
        return False


def delete_calendar_event(event_id):
    """
    Delete a Google Calendar event.
    Returns True on success, False on failure.
    """
    try:
        service = get_calendar_service()
        calendar_id = get_calendar_id()
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        print(f"Calendar event deleted: {event_id}")
        return True

    except Exception as e:
        print(f"Error deleting calendar event: {str(e)}")
        return False


def get_recent_changes(sync_token=None):
    """
    Get recent calendar changes using incremental sync.
    Returns (events_list, next_sync_token).
    On first call (no sync_token), returns all future events.
    """
    try:
        service = get_calendar_service()
        calendar_id = get_calendar_id()

        kwargs = {
            'calendarId': calendar_id,
            'singleEvents': True,
            'showDeleted': True,
        }

        if sync_token:
            kwargs['syncToken'] = sync_token
        else:
            # First sync: only get future events
            kwargs['timeMin'] = datetime.utcnow().isoformat() + 'Z'
            kwargs['orderBy'] = 'startTime'

        all_events = []
        page_token = None

        while True:
            if page_token:
                kwargs['pageToken'] = page_token

            try:
                result = service.events().list(**kwargs).execute()
            except Exception as e:
                if 'Sync token' in str(e) or '410' in str(e):
                    # Sync token invalidated, do full sync
                    print("Sync token expired, performing full sync")
                    return get_recent_changes(sync_token=None)
                raise

            all_events.extend(result.get('items', []))
            page_token = result.get('nextPageToken')
            if not page_token:
                break

        next_sync_token = result.get('nextSyncToken')
        return all_events, next_sync_token

    except Exception as e:
        print(f"Error getting calendar changes: {str(e)}")
        return [], sync_token


def parse_reservation_id_from_event(event):
    """
    Extract reservationId from a calendar event's description.
    Returns the ID if found (web-originated event), or None (calendar-originated).
    """
    description = event.get('description', '')
    for line in description.split('\n'):
        if line.strip().startswith('[WEB] ID:'):
            return line.split('[WEB] ID:')[1].strip()
    return None


def is_web_originated(event):
    """Check if an event was created from the web reservation system."""
    description = event.get('description', '')
    return '[WEB]' in description


def send_email(to_email, subject, body_html):
    """
    Send an email using the Gmail API.
    """
    try:
        if not to_email:
            return False

        creds = _get_credentials()
        service = build('gmail', 'v1', credentials=creds, cache_discovery=False)

        message = EmailMessage()
        message.set_content(body_html, subtype='html')
        message['To'] = to_email
        message['From'] = 'citas.draenriquez@gmail.com'
        message['Subject'] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}

        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        print(f"Email sent successfully to {to_email}. Message Id: {send_message['id']}")
        return True

    except Exception as e:
        print(f"Error sending email to {to_email}: {str(e)}")
        return False
