import datetime
import structlog
from typing import Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.core.config import settings
from app.tools.base.tool import BaseTool

logger = structlog.get_logger()

SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarTool(BaseTool):
    def __init__(self):
        # In a real multi-tenant app, we would load credentials 
        # dynamically based on the tenant_id passed in execution context.
        # For MVP, we load a global Service Account.
        try:
            if settings.GOOGLE_SERVICE_ACCOUNT_JSON:
                self.creds = service_account.Credentials.from_service_account_info(
                    info=settings.GOOGLE_SERVICE_ACCOUNT_JSON, scopes=SCOPES
                )
            else:
                self.creds = None # handled gracefully later
        except Exception as e:
            logger.error("google_creds_error", error=str(e))
            self.creds = None

    @property
    def name(self) -> str:
        return "check_availability"

    @property
    def description(self) -> str:
        return "Checks the calendar for available slots on a given date."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "The date to check in YYYY-MM-DD format"
                }
            },
            "required": ["date"]
        }

    async def run(self, date: str) -> str:
        if not self.creds:
            return "I apologize, but I don't have access to the calendar right now."

        try:
            service = build('calendar', 'v3', credentials=self.creds)
            
            # Define start/end of day
            time_min = f"{date}T09:00:00Z"
            time_max = f"{date}T17:00:00Z"
            
            events_result = service.events().list(
                calendarId='primary', 
                timeMin=time_min, 
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])

            if not events:
                return f"The calendar is completely free on {date} between 9 AM and 5 PM."

            # Simple logic: List busy times
            busy_summary = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                # Extract HH:MM
                time_str = start.split('T')[1][:5] if 'T' in start else "All Day"
                busy_summary.append(f"{time_str} ({event.get('summary', 'Busy')})")
            
            return f"On {date}, there are meetings at: {', '.join(busy_summary)}. All other times are free."

        except Exception as e:
            logger.error("calendar_api_failed", error=str(e))
            return "I encountered an error checking the calendar."