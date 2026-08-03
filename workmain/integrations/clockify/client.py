"""
Clockify API client for time entry management and report retrieval.

API Documentation: https://docs.clockify.me
"""

import requests
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from decimal import Decimal

from .auth import ClockifyAuth


class ClockifyClient:
    """
    Clockify API client for time tracking operations.
    
    Handles:
    - Creating time entries
    - Fetching time entries
    - Downloading PDF reports
    - Workspace and project management
    """
    
    BASE_URL = "https://api.clockify.me/api/v1"
    REPORTS_URL = "https://reports.api.clockify.me/v1"
    
    def __init__(self, auth: Optional[ClockifyAuth] = None):
        """
        Initialize Clockify API client.
        
        Args:
            auth: ClockifyAuth instance. If None, creates new instance.
        """
        self.auth = auth or ClockifyAuth()
        self.workspace_id: Optional[str] = None
        self.user_id: Optional[str] = None
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test API connection and retrieve user info.
        
        Returns:
            dict: User information including workspace access
            
        Raises:
            requests.RequestException: If connection fails
        """
        url = f"{self.BASE_URL}/user"
        headers = self.auth.get_auth_headers()
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        user_data = response.json()
        self.user_id = user_data.get('id')
        
        # Get default workspace
        if user_data.get('defaultWorkspace'):
            self.workspace_id = user_data['defaultWorkspace']
        
        return {
            'connected': True,
            'user_id': self.user_id,
            'workspace_id': self.workspace_id,
            'email': user_data.get('email'),
            'name': user_data.get('name')
        }
    
    def get_workspace_id(self) -> str:
        """
        Get workspace ID, fetching if not cached.
        
        Returns:
            str: Workspace ID
        """
        if not self.workspace_id:
            self.test_connection()
        return self.workspace_id
    
    def create_time_entry(
        self,
        description: str,
        start_time: datetime,
        duration_hours: Decimal,
        project_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a time entry in Clockify.
        
        Args:
            description: Time entry description (from condensed summary)
            start_time: When the work started (datetime with date and time)
            duration_hours: Duration in hours (Decimal)
            project_id: Optional Clockify project ID
            tags: Optional list of tags
            
        Returns:
            dict: Created time entry data including Clockify ID
            
        Raises:
            requests.RequestException: If API request fails
        """
        workspace_id = self.get_workspace_id()
        url = f"{self.BASE_URL}/workspaces/{workspace_id}/time-entries"
        headers = self.auth.get_auth_headers()
        
        # Calculate end time
        duration_seconds = int(float(duration_hours) * 3600)
        end_time = start_time + timedelta(seconds=duration_seconds)
        
        # Format times for Clockify (ISO 8601 with Z suffix required)
        # Clockify API requires UTC times with 'Z' suffix
        # If start_time is naive (no tzinfo), assume local timezone and convert to UTC
        if start_time.tzinfo is None:
            # Localize to system timezone, then convert to UTC
            local_start = start_time.astimezone()
            local_end = end_time.astimezone()
            from datetime import timezone
            start_utc = local_start.astimezone(timezone.utc)
            end_utc = local_end.astimezone(timezone.utc)
        else:
            from datetime import timezone
            start_utc = start_time.astimezone(timezone.utc)
            end_utc = end_time.astimezone(timezone.utc)

        start_iso = start_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_iso = end_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        payload = {
            "start": start_iso,
            "end": end_iso,
            "description": description,
            "projectId": project_id,
            "tagIds": tags or []
        }
        
        response = requests.post(url, headers=headers, json=payload)
        if not response.ok:
            # Include Clockify's error message in the exception
            try:
                error_detail = response.json()
            except Exception:
                error_detail = response.text
            raise requests.exceptions.HTTPError(
                f"{response.status_code} {response.reason}: {error_detail}",
                response=response
            )

        return response.json()
    
    def get_time_entries(
        self,
        start_date: date,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch time entries for a date range.
        
        Args:
            start_date: Start date for query
            end_date: End date for query (default: same as start_date)
            
        Returns:
            list: Time entry data from Clockify
            
        Raises:
            requests.RequestException: If API request fails
        """
        workspace_id = self.get_workspace_id()
        user_id = self.user_id or self.test_connection()['user_id']
        
        url = f"{self.BASE_URL}/workspaces/{workspace_id}/user/{user_id}/time-entries"
        headers = self.auth.get_auth_headers()
        
        # Format dates
        if not end_date:
            end_date = start_date
        
        start_iso = f"{start_date.isoformat()}T00:00:00Z"
        end_iso = f"{end_date.isoformat()}T23:59:59Z"
        
        params = {
            "start": start_iso,
            "end": end_iso
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def download_pdf_report(
        self,
        start_date: date,
        end_date: date,
        output_path: str
    ) -> bool:
        """
        Download detailed PDF report from Clockify.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            output_path: Where to save the PDF file
            
        Returns:
            bool: True if download successful
            
        Raises:
            requests.RequestException: If download fails
        """
        workspace_id = self.get_workspace_id()
        url = f"{self.REPORTS_URL}/workspaces/{workspace_id}/reports/detailed"
        headers = self.auth.get_auth_headers()
        
        # Request PDF export
        payload = {
            "dateRangeStart": f"{start_date.isoformat()}T00:00:00.000Z",
            "dateRangeEnd": f"{end_date.isoformat()}T23:59:59.999Z",
            "detailedFilter": {
                "page": 1,
                "pageSize": 1000
            },
            "exportType": "PDF"
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # Save PDF
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return True
    
    def find_project_by_name(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a Clockify project by name.
        
        Args:
            project_name: Name of project to find
            
        Returns:
            dict: Project data if found, None otherwise
        """
        workspace_id = self.get_workspace_id()
        url = f"{self.BASE_URL}/workspaces/{workspace_id}/projects"
        headers = self.auth.get_auth_headers()
        
        params = {"name": project_name}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        projects = response.json()
        return projects[0] if projects else None


# Import timedelta for duration calculation
from datetime import timedelta
