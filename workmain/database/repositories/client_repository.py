"""
WorkmAIn
Client Repository v1.1
20260522

Data access layer for the clients table. set_active() is atomic —
updates clients.is_active and system_state.active_client_id in one
transaction.

Version History:
- v1.0: Phase 11 Gate 3 — CRUD, set_active (atomic), get_active, name validation
- v1.1: Phase 11.5 Gate 2 — update() accepts slack_channel kwarg
"""

from __future__ import annotations
from typing import List, Optional

from sqlalchemy.orm import Session

from workmain.database.models import Client
from workmain.database.repositories.system_state_repository import SystemStateRepository


class ClientRepository:
    """Repository for the clients table."""

    RESERVED_NAME = 'internal'

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_name(self, name: str) -> None:
        """Raise ValueError if name is reserved or already exists."""
        if name.strip().lower() == self.RESERVED_NAME:
            raise ValueError(
                "'internal' is a reserved keyword and cannot be used as a client name."
            )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, name: str) -> Client:
        """Create a new client record.

        Args:
            name: Client name. Must not be 'internal' (case-insensitive).

        Returns:
            Created Client object.

        Raises:
            ValueError: If name is reserved or already exists.
        """
        self._validate_name(name)
        if self.get_by_name(name) is not None:
            raise ValueError(f"A client named '{name}' already exists.")
        client = Client(name=name, is_active=False)
        self.session.add(client)
        self.session.commit()
        self.session.refresh(client)
        return client

    def get_by_id(self, client_id: int) -> Optional[Client]:
        """Return client by ID, or None if not found."""
        return self.session.query(Client).filter(Client.id == client_id).first()

    def get_by_name(self, name: str) -> Optional[Client]:
        """Return client by name (case-insensitive), or None if not found."""
        from sqlalchemy import func
        return self.session.query(Client).filter(
            func.lower(Client.name) == name.strip().lower()
        ).first()

    def find_by_name_fuzzy(self, name: str) -> List[Client]:
        """Return clients whose names contain the search string (case-insensitive)."""
        from sqlalchemy import func
        return self.session.query(Client).filter(
            func.lower(Client.name).contains(name.strip().lower())
        ).order_by(Client.name).all()

    def list_all(self) -> List[Client]:
        """Return all clients ordered by name."""
        return self.session.query(Client).order_by(Client.name).all()

    def delete(self, client_id: int) -> bool:
        """Delete a client by ID. ON DELETE SET NULL handles data record unlinking.

        Returns:
            True if deleted, False if not found.
        """
        client = self.get_by_id(client_id)
        if client is None:
            return False
        self.session.delete(client)
        self.session.commit()
        return True

    def update(self, client_id: int, **kwargs) -> Optional[Client]:
        """Update client fields. Accepted kwargs: name, slack_channel.

        Raises:
            ValueError: If new name is reserved.
        """
        client = self.get_by_id(client_id)
        if client is None:
            return None
        if 'name' in kwargs:
            self._validate_name(kwargs['name'])
            client.name = kwargs['name']
        if 'slack_channel' in kwargs:
            client.slack_channel = kwargs['slack_channel']
        self.session.commit()
        self.session.refresh(client)
        return client

    # ------------------------------------------------------------------
    # Active client management (all atomic)
    # ------------------------------------------------------------------

    def set_active(self, client_id: int) -> Client:
        """Set a client as the active context. Atomic single transaction:
        1. Clear is_active on any currently active client.
        2. Set is_active=True on target client.
        3. Write active_client_id to system_state.

        Args:
            client_id: ID of the client to activate.

        Returns:
            The now-active Client object.

        Raises:
            ValueError: If client_id does not exist.
        """
        client = self.get_by_id(client_id)
        if client is None:
            raise ValueError(f"No client with ID {client_id}.")

        self.session.query(Client).filter(Client.is_active == True).update(
            {Client.is_active: False}, synchronize_session='fetch'
        )
        client.is_active = True
        SystemStateRepository(self.session).set_int('active_client_id', client_id)
        self.session.commit()
        self.session.refresh(client)
        return client

    def clear_active(self) -> None:
        """Clear active client context (internal mode). Atomic single transaction:
        1. Clear is_active on any currently active client.
        2. Delete active_client_id from system_state.
        """
        self.session.query(Client).filter(Client.is_active == True).update(
            {Client.is_active: False}, synchronize_session='fetch'
        )
        SystemStateRepository(self.session).delete('active_client_id')
        self.session.commit()

    def get_active(self) -> Optional[Client]:
        """Return the active client, or None if in internal mode.

        Fast path: reads active_client_id from system_state.
        Safety net: falls back to SELECT WHERE is_active=TRUE if key absent.
        """
        state_repo = SystemStateRepository(self.session)
        client_id = state_repo.get_int('active_client_id')
        if client_id is not None:
            client = self.get_by_id(client_id)
            if client is not None:
                return client
        return self.session.query(Client).filter(Client.is_active == True).first()
