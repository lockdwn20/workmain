"""
WorkmAIn Email Repository
Email Repository v1.0
20260305

Data access layer for recipient management and report-template assignments.
Handles all CRUD operations for the recipients and report_recipients tables.

Version History:
- v1.0: Initial implementation (Phase 6 Gate 1)
"""

from typing import Optional

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

    def assign_recipient(
        self, recipient_id: int, report_type: str, role: str
    ) -> ReportRecipient:
        """
        Assign a recipient to a report template with a role (to/cc).
        Idempotent — returns existing assignment if already present.

        Args:
            recipient_id: Recipient primary key
            report_type: Template name
            role: 'to' or 'cc'

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
            email=recipient.email,
            recipient_type=role,
        )
        self.session.add(assignment)
        self.session.commit()
        self.session.refresh(assignment)
        return assignment

    def unassign_recipient(self, recipient_id: int, report_type: str) -> None:
        """
        Remove a recipient's assignment from a specific report template.
        The recipient identity record is not affected.

        Args:
            recipient_id: Recipient primary key
            report_type: Template name
        """
        assignment = (
            self.session.query(ReportRecipient)
            .filter(
                ReportRecipient.recipient_id == recipient_id,
                ReportRecipient.report_type == report_type,
            )
            .first()
        )
        if assignment:
            self.session.delete(assignment)
            self.session.commit()


def get_email_repository(session: Session) -> EmailRepository:
    """Factory function — consistent with other repository patterns."""
    return EmailRepository(session)
