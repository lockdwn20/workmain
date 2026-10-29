"""
Service layer for client records and the active client context. Shared by the
clients CLI group. Functions take a session and return frozen dataclasses;
none opens, commits or rolls back a session.

A client is targeted by a numeric ID or a case-insensitive exact name. The
active client drives attribution of notes, time entries and reports, and
'internal' is the reserved name for no client.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from workmain.database.models import Client
from workmain.database.repositories.client_repository import ClientRepository
from workmain.services.exceptions import (
    ActiveClientDeleteError,
    ClientNotFoundError,
    InvalidClientNameError,
)
from workmain.services.results import Page


@dataclass(frozen=True)
class ClientRow:
    """A client as a collection shows it."""

    client_id: int
    name: str
    is_active: bool


@dataclass(frozen=True)
class ClientDetail:
    """A client as a record shows it."""

    client_id: int
    name: str
    is_active: bool
    created_at: Optional[datetime]


@dataclass(frozen=True)
class LinkedTotals:
    """The rows linked to a client, by table."""

    meetings: int
    notes: int
    projects: int
    report_recipients: int
    reports: int
    time_entries: int


@dataclass(frozen=True)
class DeletePreview:
    """What deleting a client will do, and the question that asks for it."""

    filters: Tuple[Tuple[str, object], ...]
    client: ClientRow
    totals: LinkedTotals
    question: str


@dataclass(frozen=True)
class StatusTotals:
    """The active client's name and ID; 'internal' and None when none is set."""

    client: str
    client_id: Optional[int]


@dataclass(frozen=True)
class ClientStatus:
    """The active client context."""

    filters: Tuple[Tuple[str, object], ...]
    totals: StatusTotals


def _row(client: Client) -> ClientRow:
    return ClientRow(client_id=client.id, name=client.name, is_active=client.is_active)


def _resolve(repo: ClientRepository, identifier: str) -> Optional[Client]:
    """Resolve a client by numeric ID or name (case-insensitive)."""
    if identifier.isdigit():
        return repo.get_by_id(int(identifier))
    return repo.get_by_name(identifier)


def _not_found(repo: ClientRepository, identifier: str) -> ClientNotFoundError:
    """Build the not-found error, with fuzzy suggestions for a name."""
    message = f"Client '{identifier}' not found."
    suggestions = [] if identifier.isdigit() else repo.find_by_name_fuzzy(identifier)
    if suggestions:
        listed = ", ".join(f"{c.name} (#{c.id})" for c in suggestions)
        message += f" Did you mean: {listed}?"
    return ClientNotFoundError(message)


def list_clients(session: Session) -> Page[ClientRow]:
    """Every client, ordered by name."""
    rows = tuple(_row(c) for c in ClientRepository(session).list_all())
    return Page(rows=rows, total=len(rows), filters=())


def get_client(session: Session, identifier: str) -> ClientDetail:
    """One client, by ID or name.

    Raises:
        ClientNotFoundError: If the identifier matches no client.
    """
    repo = ClientRepository(session)
    client = _resolve(repo, identifier)
    if client is None:
        raise _not_found(repo, identifier)
    return ClientDetail(
        client_id=client.id,
        name=client.name,
        is_active=client.is_active,
        created_at=client.created_at,
    )


def add_client(session: Session, name: str) -> ClientRow:
    """Create a client.

    Raises:
        InvalidClientNameError: If the name is reserved or already taken.
    """
    try:
        client = ClientRepository(session).create(name)
    except ValueError as e:
        raise InvalidClientNameError(str(e)) from e
    return _row(client)


def preview_delete(session: Session, identifier: str, force: bool) -> DeletePreview:
    """What deleting a client will do.

    Raises:
        ClientNotFoundError: If the identifier matches no client.
        ActiveClientDeleteError: If the client is active and force is false.
    """
    repo = ClientRepository(session)
    client = _resolve(repo, identifier)
    if client is None:
        raise _not_found(repo, identifier)
    if client.is_active and not force:
        raise ActiveClientDeleteError(
            f"Client '{client.name}' is currently active. Use --force to delete."
        )
    totals = LinkedTotals(**repo.count_linked_records(client.id))
    question = (
        f"Delete client '{client.name}' (ID: {client.id})? "
        f"Its {totals.notes} notes, {totals.time_entries} time entries, "
        f"{totals.meetings} meetings, {totals.reports} reports, "
        f"{totals.projects} projects and {totals.report_recipients} report recipients "
        f"will lose their client."
    )
    return DeletePreview(
        filters=(("client", client.name), ("id", client.id)),
        client=_row(client),
        totals=totals,
        question=question,
    )


def delete_client(session: Session, client_id: int) -> ClientRow:
    """Delete a client, clearing the active context first when it is active.

    Raises:
        ClientNotFoundError: If no client has the ID.
    """
    repo = ClientRepository(session)
    client = repo.get_by_id(client_id)
    if client is None:
        raise ClientNotFoundError(f"Client '{client_id}' not found.")
    row = _row(client)
    if row.is_active:
        repo.clear_active()
    repo.delete(client_id)
    return row


def get_status(session: Session) -> ClientStatus:
    """The active client, or internal when none is set."""
    client = ClientRepository(session).get_active()
    if client is None:
        totals = StatusTotals(client="internal", client_id=None)
    else:
        totals = StatusTotals(client=client.name, client_id=client.id)
    return ClientStatus(filters=(), totals=totals)


def set_active(session: Session, name: str) -> ClientStatus:
    """Make a client active by name, or clear the context with 'internal'.

    Raises:
        ClientNotFoundError: If the name matches no client.
    """
    repo = ClientRepository(session)
    if name.strip().lower() == ClientRepository.RESERVED_NAME:
        repo.clear_active()
    else:
        client = repo.get_by_name(name)
        if client is None:
            raise _not_found(repo, name)
        repo.set_active(client.id)
    return get_status(session)


def format_active_marker(b: bool) -> str:
    """The Active column's cell: a mark for the active client, else empty."""
    return "●" if b else ""


def format_yes_no(b: bool) -> str:
    """A boolean as Yes or No."""
    return "Yes" if b else "No"
