"""
WorkmAIn Clockify Integration
Sync Engine
v1.0
20260115

Bidirectional sync between WorkmAIn and Clockify with conflict resolution.

Version History:
- v1.0: Initial implementation with push, pull, and interactive conflict resolution
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, time
from decimal import Decimal
from sqlalchemy.orm import Session

from .client import ClockifyClient
from workmain.database.models import TimeEntry, Meeting
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository


class SyncConflict:
    """Represents a sync conflict between local and Clockify entries."""
    
    def __init__(
        self,
        local_entry: TimeEntry,
        clockify_entry: Dict[str, Any],
        conflict_type: str
    ):
        self.local_entry = local_entry
        self.clockify_entry = clockify_entry
        self.conflict_type = conflict_type  # 'duplicate', 'modified', 'overlap'


class ClockifySync:
    """
    Handles bidirectional synchronization between WorkmAIn and Clockify.
    
    Features:
    - Push local entries to Clockify
    - Pull Clockify entries to local database
    - Interactive conflict resolution
    - Duplicate detection
    """
    
    def __init__(
        self,
        session: Session,
        client: Optional[ClockifyClient] = None
    ):
        """
        Initialize sync engine.
        
        Args:
            session: SQLAlchemy session for database access
            client: ClockifyClient instance (creates new if None)
        """
        self.session = session
        self.client = client or ClockifyClient()
        self.repo = TimeEntriesRepository(session)
    
    def push_entries(
        self,
        entries: Optional[List[TimeEntry]] = None,
        interactive: bool = True
    ) -> Dict[str, Any]:
        """
        Push local time entries to Clockify.
        
        Args:
            entries: Specific entries to push. If None, pushes all unsync'd entries.
            interactive: Whether to show progress and prompt on errors
            
        Returns:
            dict: Sync results with success/failure counts
        """
        # Get entries to sync
        if entries is None:
            entries = self.repo.get_unsynced_entries()
        
        results = {
            'total': len(entries),
            'successful': 0,
            'failed': 0,
            'failures': []
        }
        
        for i, entry in enumerate(entries, 1):
            if interactive:
                print(f"[{i}/{results['total']}] Syncing: {entry.description[:50]}...")
            
            try:
                # Get project ID if linked
                project_id = None
                if entry.project_id:
                    project_id = self._get_clockify_project_id(entry.project_id)
                
                # Create in Clockify
                clockify_entry = self.client.create_time_entry(
                    description=entry.description,
                    start_time=datetime.combine(entry.entry_date, entry.entry_time),
                    duration_hours=entry.duration_hours,
                    project_id=project_id,
                    tags=entry.tags
                )
                
                # Update local entry with Clockify ID
                entry.clockify_id = clockify_entry['id']
                entry.synced_at = datetime.now()
                self.session.commit()
                
                results['successful'] += 1
                
                if interactive:
                    print(f"  ✓ Synced (Clockify ID: {clockify_entry['id'][:8]}...)")
                
            except Exception as e:
                results['failed'] += 1
                results['failures'].append({
                    'entry_id': entry.id,
                    'description': entry.description,
                    'error': str(e)
                })
                
                if interactive:
                    print(f"  ✗ Failed: {str(e)}")
                
                # Continue with next entry
                continue
        
        return results
    
    def pull_entries(
        self,
        start_date: date,
        end_date: Optional[date] = None,
        interactive: bool = True
    ) -> Dict[str, Any]:
        """
        Pull time entries from Clockify to local database.
        
        Args:
            start_date: Start date for pull
            end_date: End date for pull (defaults to start_date)
            interactive: Whether to show progress and prompt for conflicts
            
        Returns:
            dict: Pull results with counts of imported/skipped/conflicted
        """
        if not end_date:
            end_date = start_date
        
        # Fetch from Clockify
        clockify_entries = self.client.get_time_entries(start_date, end_date)
        
        results = {
            'total': len(clockify_entries),
            'imported': 0,
            'skipped': 0,
            'conflicts': 0
        }
        
        for clockify_entry in clockify_entries:
            # Check if already exists locally
            existing = self.repo.get_by_clockify_id(clockify_entry['id'])
            
            if existing:
                results['skipped'] += 1
                continue
            
            # Check for potential conflicts (same time/date)
            conflict = self._detect_conflict(clockify_entry)
            
            if conflict and interactive:
                resolution = self._resolve_conflict_interactive(conflict)
                
                if resolution == 'skip':
                    results['skipped'] += 1
                    continue
                elif resolution == 'keep_both':
                    # Import as new entry
                    pass
                elif resolution == 'link':
                    # Link existing entry to Clockify ID
                    conflict.local_entry.clockify_id = clockify_entry['id']
                    conflict.local_entry.synced_at = datetime.now()
                    self.session.commit()
                    results['conflicts'] += 1
                    continue
            
            # Import entry
            try:
                self._import_clockify_entry(clockify_entry)
                results['imported'] += 1
            except Exception as e:
                print(f"Failed to import entry: {str(e)}")
                results['skipped'] += 1
        
        return results
    
    def _detect_conflict(
        self,
        clockify_entry: Dict[str, Any]
    ) -> Optional[SyncConflict]:
        """
        Detect if Clockify entry conflicts with local entry.
        
        Args:
            clockify_entry: Entry from Clockify API
            
        Returns:
            SyncConflict if conflict found, None otherwise
        """
        # Parse Clockify entry time
        start_str = clockify_entry['timeInterval']['start']
        start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        entry_date = start_dt.date()
        entry_time = start_dt.time()
        
        # Check for overlapping local entries
        local_entries = self.repo.get_by_date(entry_date)
        
        for local_entry in local_entries:
            # Skip if already linked
            if local_entry.clockify_id:
                continue
            
            # Check for time overlap
            if local_entry.entry_time == entry_time:
                return SyncConflict(
                    local_entry=local_entry,
                    clockify_entry=clockify_entry,
                    conflict_type='duplicate'
                )
        
        return None
    
    def _resolve_conflict_interactive(
        self,
        conflict: SyncConflict
    ) -> str:
        """
        Prompt user to resolve sync conflict.
        
        Args:
            conflict: SyncConflict object
            
        Returns:
            str: Resolution choice ('skip', 'keep_both', 'link')
        """
        print("\n" + "="*60)
        print("SYNC CONFLICT DETECTED")
        print("="*60)
        
        # Show local entry
        local = conflict.local_entry
        print(f"\nLocal Entry (ID: {local.id}):")
        print(f"  Date: {local.entry_date}")
        print(f"  Time: {local.entry_time}")
        print(f"  Duration: {local.duration_hours}h")
        print(f"  Description: {local.description}")
        
        # Show Clockify entry
        clockify = conflict.clockify_entry
        start_str = clockify['timeInterval']['start']
        end_str = clockify['timeInterval']['end']
        start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        duration = (end_dt - start_dt).total_seconds() / 3600
        
        print(f"\nClockify Entry (ID: {clockify['id'][:8]}...):")
        print(f"  Date: {start_dt.date()}")
        print(f"  Time: {start_dt.time()}")
        print(f"  Duration: {duration:.2f}h")
        print(f"  Description: {clockify.get('description', 'N/A')}")
        
        # Prompt for resolution
        print("\nOptions:")
        print("  1. Link (treat as same entry, update local with Clockify ID)")
        print("  2. Keep both (import Clockify entry as separate)")
        print("  3. Skip (don't import this Clockify entry)")
        
        while True:
            choice = input("\nChoice (1-3): ").strip()
            
            if choice == '1':
                return 'link'
            elif choice == '2':
                return 'keep_both'
            elif choice == '3':
                return 'skip'
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    
    def _import_clockify_entry(self, clockify_entry: Dict[str, Any]) -> TimeEntry:
        """
        Import a Clockify entry into local database.
        
        Args:
            clockify_entry: Entry data from Clockify API
            
        Returns:
            TimeEntry: Created local entry
        """
        # Parse time data
        start_str = clockify_entry['timeInterval']['start']
        end_str = clockify_entry['timeInterval']['end']
        start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        
        # Calculate duration
        duration_seconds = (end_dt - start_dt).total_seconds()
        duration_hours = Decimal(str(duration_seconds / 3600))
        
        # Create local entry
        entry = self.repo.create(
            description=clockify_entry.get('description', 'Imported from Clockify'),
            duration_hours=duration_hours,
            entry_date=start_dt.date(),
            entry_time=start_dt.time(),
            clockify_id=clockify_entry['id'],
            tags=clockify_entry.get('tags', [])
        )
        
        entry.synced_at = datetime.now()
        self.session.commit()
        
        return entry
    
    def _get_clockify_project_id(self, local_project_id: int) -> Optional[str]:
        """
        Get Clockify project ID from local project ID.
        
        Args:
            local_project_id: Local project ID
            
        Returns:
            str: Clockify project ID if found
        """
        from workmain.database.models import Project
        
        project = self.session.query(Project).filter(
            Project.id == local_project_id
        ).first()
        
        return project.clockify_project_id if project else None
