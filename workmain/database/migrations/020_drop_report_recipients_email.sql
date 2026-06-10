-- 020_drop_report_recipients_email.sql
-- H-2: Drop dead denormalized email column from report_recipients
-- Column is written at creation time only; all read paths join through
-- Recipient.email. 0 rows ever read this column.
-- Prerequisite: grep confirmation that no code reads this column directly.

ALTER TABLE report_recipients DROP COLUMN email;
