"""
WorkmAIn Email Repository
Email Repository v1.2
20260610

Data access layer for recipient management and report-template assignments.
Handles all CRUD operations for the recipients and report_recipients tables.

Version History:
- v1.0: Initial implementation (Phase 6 Gate 1)
- v1.1: Phase 11.5 Gate 3 — assign_recipient() and unassign_recipient() accept
        client_id for ambient client scoping; list_for_client() added for
        client-aware recipient resolution (global + client-scoped merged)
- v1.2: Phase 13 DB Schema Sprint Gate 1 — H-2: remove email= write from
        assign_recipient() create path (column dropped in migration 020)
"""

from typing import Optional, List

from sqlalchemy.orm import Session

from workmain.database.models import Recipient, ReportRecipient


class EmailRepository:
    """
    Repository for email recipient and assignment operations.

    Provides methods for:
    - Managing recipient identity records (add, remove, lookup)
    - Assigning/unassigning recipients to report templates and roles
    - Querying assignments for draft generation
    """

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------
    # Recipient identity methods
    # ------------------------------------------------------------------

    def get_all_recipients(self) -> list[Recipient]:
        """Return all recipients ordered by ID."""
        return self.session.query(Recipient).order_by(Recipient.id).all()

    def get_recipient_by_id(self, id: int) -> Optional[Recipient]:
        """Return recipient by primary key, or None if not found."""
        return self.session.query(Recipient).filter(Recipient.id == id).first()

    def get_recipient_by_email(self, email: str) -> Optional[Recipient]:
        """Return recipient by email address, or None if not found."""
        return self.session.query(Recipient).filter(
            Recipient.email == email.lower().strip()
        ).first()

    def add_recipient(self, email: str) -> Recipient:
        """
        Add a new recipient. Returns existing record if email already exists.

        Args:
            email: Email address (normalised to lowercase)

        Returns:
            Recipient record (new or existing)
        """
        email = email.lower().strip()
        existing = self.get_recipient_by_email(email)
        if existing:
            return existing

        recipient = Recipient(email=email)
        self.session.add(recipient)
        self.session.commit()
        self.session.refresh(recipient)
        return recipient

    def remove_recipient(self, id: int) -> None:
        """
        Remove recipient by ID. Cascades to all report_recipients assignments.

        Args:
            id: Recipient primary key
        """
        recipient = self.get_recipient_by_id(id)
        if recipient:
            self.session.delete(recipient)
            self.session.commit()

    # ------------------------------------------------------------------
    # Assignment methods
    # ------------------------------------------------------------------

    def get_assignments_for_template(self, report_type: str) -> list[ReportRecipient]:
        """
        Return all recipient assignments for a given report template.

        Args:
            report_type: Template name (e.g. 'daily_internal', 'weekly_client')

        Returns:
            List of ReportRecipient records with recipient relationship loaded
        """
        return (
            self.session.query(ReportRecipient)
            .filter(ReportRecipient.report_type == report_type)
            .join(ReportRecipient.recipient)
            .order_by(ReportRecipient.recipient_type, Recipient.email)
            .all()
        )

    def list_for_client(
        self,
        template_name: str,
        client_id: Optional[int],
    ) -> List[ReportRecipient]:
        """
        Return recipients for template in client-aware priority order.

        Returns ALL of:
        - Global recipients (client_id IS NULL) for this template
        - Client-scoped recipients (client_id = client_id) for this template

        If client_id is None (internal mode): global recipients only.

        Caller deduplicates by email address if the same address appears
        in both global and client-scoped sets.

        Args:
            template_name: Report template name (maps to report_type column).
            client_id: Active client ID, or None for internal/global mode.

        Returns:
            List of ReportRecipient records.
        """
        query = self.session.query(ReportRecipient).filter(
            ReportRecipient.report_type == template_name
        )
        if client_id is not None:
            query = query.filter(
                (ReportRecipient.client_id == None) |  # noqa: E711
                (ReportRecipient.client_id == client_id)
            )
        else:
            query = query.filter(ReportRecipient.client_id == None)  # noqa: E711
        return query.all()

    def assign_recipient(
        self,
        recipient_id: int,
        report_type: str,
        role: str,
        client_id: Optional[int] = None,
    ) -> ReportRecipient:
        """
        Assign a recipient to a report template with a role (to/cc).

        Idempotent for the (recipient_id, report_type, client_id) combination —
        updates role if the assignment already exists at the same scope.

        Args:
            recipient_id: Recipient primary key
            report_type: Template name
            role: 'to' or 'cc'
            client_id: Active client ID (None = global assignment)

        Returns:
            ReportRecipient record (new or existing)
        """
        recipient = self.get_recipient_by_id(recipient_id)
        if not recipient:
            raise ValueError(f"Recipient ID {recipient_id} not found")

        existing = (
            self.session.query(ReportRecipient)
            .filter(
                ReportRecipient.recipient_id == recipient_id,
                ReportRecipient.report_type == report_type,
                ReportRecipient.client_id == client_id,
            )
            .first()
        )
        if existing:
            if existing.recipient_type != role:
                existing.recipient_type = role
                self.session.commit()
            return existing

        assignment = ReportRecipient(
            recipient_id=recipient_id,
            report_type=report_type,
            recipient_type=role,
            client_id=client_id,
        )
        self.session.add(assignment)
        self.session.commit()
        self.session.refresh(assignment)
        return assignment

    def unassign_recipient(
        self,
        recipient_id: int,
        report_type: str,
        client_id: Optional[int] = None,
    ) -> None:
        """
        Remove a recipient's assignment from a specific report template at the
        specified client scope.

        Filters by client_id to ensure only the correct record is removed —
        prevents accidentally deleting a global record when a client-scoped
        one was intended, and vice versa.

        Args:
            recipient_id: Recipient primary key
            report_type: Template name
            client_id: Client scope to target (None = global assignment)
        """
        assignment = (
            self.session.query(ReportRecipient)
            .filter(
                ReportRecipient.recipient_id == recipient_id,
                ReportRecipient.report_type == report_type,
                ReportRecipient.client_id == client_id,
            )
            .first()
        )
        if assignment:
            self.session.delete(assignment)
            self.session.commit()


def get_email_repository(session: Session) -> EmailRepository:
    """Factory function — consistent with other repository patterns."""
    return EmailRepository(session)
