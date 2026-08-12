# PHASE6_DISCOVERY_RESULTS.md

**Discovery Task:** PHASE6_DISCOVERY_TASK v1.0
**Date:** 2026-03-04
**Python Version:** Python 3.12.3
**icalendar:** Newly installed — v7.0.3

---

## Task 1 — Meetings Table Schema

```
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'meetings'
ORDER BY ordinal_position;
```

| column_name         | data_type                   | is_nullable | column_default                        |
|---------------------|-----------------------------|-------------|---------------------------------------|
| id                  | integer                     | NO          | nextval('meetings_id_seq'::regclass)  |
| outlook_id          | character varying           | YES         | None                                  |
| outlook_recurring_id| character varying           | YES         | None                                  |
| title               | character varying           | NO          | None                                  |
| start_time          | timestamp without time zone | NO          | None                                  |
| end_time            | timestamp without time zone | NO          | None                                  |
| attendees           | ARRAY                       | YES         | None                                  |
| is_recurring        | boolean                     | YES         | false                                 |
| notes_captured      | boolean                     | YES         | false                                 |
| reminder_sent       | boolean                     | YES         | false                                 |
| created_at          | timestamp without time zone | YES         | now()                                 |
| condensed_summary   | text                        | YES         | None                                  |
| condensed_at        | timestamp without time zone | YES         | None                                  |

**Total columns:** 13

---

## Task 2 — ICS Field Discovery

Script run against `/tmp/sample.ics`.

```
--- EVENT ---
  CLASS: vText(b'PUBLIC')
  DTEND: vDDDTypes(2026-03-04 09:00:00-06:00, Parameters({'TZID': 'Central Standard Time'}))
  DTSTAMP: vDDDTypes(2026-03-04 19:45:05+00:00, Parameters({}))
  DTSTART: vDDDTypes(2026-03-04 08:45:00-06:00, Parameters({'TZID': 'Central Standard Time'}))
  RRULE: vRecur({'FREQ': ['WEEKLY'], 'COUNT': [18], 'BYDAY': ['TU', 'WE', 'TH', 'FR']})
  SEQUENCE: 0
  SUMMARY: vText(b'Copy: CSIRT Daily touchpoint')
  TRANSP: vText(b'OPAQUE')
  UID: vText(b'AAAAAD2ybyshQsREoRb0X9v1LusHAJDFDPTAQVZHrRcyOf6AV2IAAESTZDEAAJDFDPTAQVZHrRcyOf6AV2IAAESTfBMAAA==')
  X-MICROSOFT-CDO-BUSYSTATUS: vText(b'BUSY')

--- EVENT ---
  CLASS: vText(b'PUBLIC')
  DTEND: vDDDTypes(2026-03-09 09:30:00-05:00, Parameters({'TZID': 'Central Standard Time'}))
  DTSTAMP: vDDDTypes(2026-03-04 19:45:05+00:00, Parameters({}))
  DTSTART: vDDDTypes(2026-03-09 09:00:00-05:00, Parameters({'TZID': 'Central Standard Time'}))
  RRULE: vRecur({'FREQ': ['WEEKLY'], 'COUNT': [4], 'BYDAY': ['MO']})
  SEQUENCE: 0
  SUMMARY: vText(b'Copy: CSIRT Daily touchpoint')
  TRANSP: vText(b'OPAQUE')
  UID: vText(b'AAAAAD2ybyshQsREoRb0X9v1LusHAJDFDPTAQVZHrRcyOf6AV2IAAESTZDEAAJDFDPTAQVZHrRcyOf6AV2IAAESTfBQAAA==')
  X-MICROSOFT-CDO-BUSYSTATUS: vText(b'BUSY')

--- EVENT ---
  CLASS: vText(b'PUBLIC')
  DTEND: vDDDTypes(2026-03-09 15:00:00-05:00, Parameters({'TZID': 'Central Standard Time'}))
  DTSTAMP: vDDDTypes(2026-03-04 19:45:05+00:00, Parameters({}))
  DTSTART: vDDDTypes(2026-03-09 14:00:00-05:00, Parameters({'TZID': 'Central Standard Time'}))
  RRULE: vRecur({'FREQ': ['WEEKLY'], 'COUNT': [4], 'BYDAY': ['MO']})
  SEQUENCE: 0
  SUMMARY: vText(b'Copy: DE Weekly Standup and Vulnerability Review')
  TRANSP: vText(b'OPAQUE')
  UID: vText(b'AAAAAD2ybyshQsREoRb0X9v1LusHAJDFDPTAQVZHrRcyOf6AV2IAAESTZDEAAJDFDPTAQVZHrRcyOf6AV2IAAESTfBUAAA==')
  X-MICROSOFT-CDO-BUSYSTATUS: vText(b'BUSY')

--- EVENT ---
  CLASS: vText(b'PUBLIC')
  DTEND: vDDDTypes(2026-03-05 15:30:00-06:00, Parameters({'TZID': 'Central Standard Time'}))
  DTSTAMP: vDDDTypes(2026-03-04 19:45:05+00:00, Parameters({}))
  DTSTART: vDDDTypes(2026-03-05 15:00:00-06:00, Parameters({'TZID': 'Central Standard Time'}))
  RRULE: vRecur({'FREQ': ['WEEKLY'], 'COUNT': [5], 'BYDAY': ['TH']})
  SEQUENCE: 0
  SUMMARY: vText(b'Copy: Weekly IPS Review')
  TRANSP: vText(b'OPAQUE')
  UID: vText(b'AAAAAD2ybyshQsREoRb0X9v1LusHAJDFDPTAQVZHrRcyOf6AV2IAAESTZDEAAJDFDPTAQVZHrRcyOf6AV2IAAESTfBYAAA==')
  X-MICROSOFT-CDO-BUSYSTATUS: vText(b'BUSY')

--- EVENT ---
  CLASS: vText(b'PUBLIC')
  DTEND: vDDDTypes(2026-03-05 15:00:00-06:00, Parameters({'TZID': 'Central Standard Time'}))
  DTSTAMP: vDDDTypes(2026-03-04 19:45:05+00:00, Parameters({}))
  DTSTART: vDDDTypes(2026-03-05 14:00:00-06:00, Parameters({'TZID': 'Central Standard Time'}))
  SEQUENCE: 0
  SUMMARY: vText(b'Copy: The Hive 5 - Connections update from On Prem to SaaS - Part 2')
  TRANSP: vText(b'OPAQUE')
  UID: vText(b'AAAAAD2ybyshQsREoRb0X9v1LusHAJDFDPTAQVZHrRcyOf6AV2IAAESTZDEAAJDFDPTAQVZHrRcyOf6AV2IAAESTfBcAAA==')
  X-MICROSOFT-CDO-BUSYSTATUS: vText(b'TENTATIVE')

--- EVENT ---
  CLASS: vText(b'PUBLIC')
  DTEND: vDDDTypes(2026-03-06 10:30:00-06:00, Parameters({'TZID': 'Central Standard Time'}))
  DTSTAMP: vDDDTypes(2026-03-04 19:45:05+00:00, Parameters({}))
  DTSTART: vDDDTypes(2026-03-06 10:00:00-06:00, Parameters({'TZID': 'Central Standard Time'}))
  RRULE: vRecur({'FREQ': ['WEEKLY'], 'COUNT': [4], 'BYDAY': ['FR']})
  SEQUENCE: 0
  SUMMARY: vText(b'Copy: CSIRT - Policy Violation Weekly touchpoint')
  TRANSP: vText(b'OPAQUE')
  UID: vText(b'AAAAAD2ybyshQsREoRb0X9v1LusHAJDFDPTAQVZHrRcyOf6AV2IAAESTZDEAAJDFDPTAQVZHrRcyOf6AV2IAAESTfBgAAA==')
  X-MICROSOFT-CDO-BUSYSTATUS: vText(b'BUSY')

--- EVENT ---
  CLASS: vText(b'PUBLIC')
  DTEND: vDDDTypes(2026-03-06 11:00:00-06:00, Parameters({'TZID': 'Central Standard Time'}))
  DTSTAMP: vDDDTypes(2026-03-04 19:45:05+00:00, Parameters({}))
  DTSTART: vDDDTypes(2026-03-06 10:30:00-06:00, Parameters({'TZID': 'Central Standard Time'}))
  SEQUENCE: 0
  SUMMARY: vText(b'Copy: Dev file DLP Working Group')
  TRANSP: vText(b'OPAQUE')
  UID: vText(b'AAAAAD2ybyshQsREoRb0X9v1LusHAJDFDPTAQVZHrRcyOf6AV2IAAESTZDEAAJDFDPTAQVZHrRcyOf6AV2IAAESTfBkAAA==')
  X-MICROSOFT-CDO-BUSYSTATUS: vText(b'BUSY')

--- EVENT ---
  CLASS: vText(b'PUBLIC')
  DTEND: vDDDTypes(2026-03-05 15:00:00-06:00, Parameters({'TZID': 'Central Standard Time'}))
  DTSTAMP: vDDDTypes(2026-03-04 19:45:05+00:00, Parameters({}))
  DTSTART: vDDDTypes(2026-03-05 13:30:00-06:00, Parameters({'TZID': 'Central Standard Time'}))
  RRULE: vRecur({'FREQ': ['WEEKLY'], 'COUNT': [3], 'INTERVAL': [2], 'BYDAY': ['TH'], 'WKST': ['SU']})
  SEQUENCE: 0
  SUMMARY: vText(b'Copy: Hour of Learning (Optional)')
  TRANSP: vText(b'OPAQUE')
  UID: vText(b'AAAAAD2ybyshQsREoRb0X9v1LusHAJDFDPTAQVZHrRcyOf6AV2IAAESTZDEAAJDFDPTAQVZHrRcyOf6AV2IAAESTfBsAAA==')
  X-MICROSOFT-CDO-BUSYSTATUS: vText(b'TENTATIVE')

--- EVENT ---
  CLASS: vText(b'PUBLIC')
  DTEND: vDDDTypes(2026-03-05 09:30:00-08:00, Parameters({'TZID': 'Pacific Standard Time'}))
  DTSTAMP: vDDDTypes(2026-03-04 19:45:05+00:00, Parameters({}))
  DTSTART: vDDDTypes(2026-03-05 09:00:00-08:00, Parameters({'TZID': 'Pacific Standard Time'}))
  SEQUENCE: 0
  SUMMARY: vText(b'Copy: Lunch and Learn Discussion')
  TRANSP: vText(b'OPAQUE')
  UID: vText(b'AAAAAD2ybyshQsREoRb0X9v1LusHAJDFDPTAQVZHrRcyOf6AV2IAAESTZDEAAJDFDPTAQVZHrRcyOf6AV2IAAESTfBwAAA==')
  X-MICROSOFT-CDO-BUSYSTATUS: vText(b'BUSY')

--- EVENT ---
  CLASS: vText(b'PUBLIC')
  DTEND: vDDDTypes(2026-03-04 12:00:00-06:00, Parameters({'TZID': 'Central Standard Time'}))
  DTSTAMP: vDDDTypes(2026-03-04 19:45:05+00:00, Parameters({}))
  DTSTART: vDDDTypes(2026-03-04 11:00:00-06:00, Parameters({'TZID': 'Central Standard Time'}))
  RRULE: vRecur({'FREQ': ['WEEKLY'], 'COUNT': [3], 'INTERVAL': [2], 'BYDAY': ['WE'], 'WKST': ['SU']})
  SEQUENCE: 0
  SUMMARY: vText(b'Copy: All CSIRT - Biweekly Projects')
  TRANSP: vText(b'OPAQUE')
  UID: vText(b'AAAAAD2ybyshQsREoRb0X9v1LusHAJDFDPTAQVZHrRcyOf6AV2IAAESTZDEAAJDFDPTAQVZHrRcyOf6AV2IAAESTfB0AAA==')
  X-MICROSOFT-CDO-BUSYSTATUS: vText(b'BUSY')

--- EVENT ---
  CLASS: vText(b'PUBLIC')
  DTEND: vDDDTypes(2026-03-11 12:00:00-05:00, Parameters({'TZID': 'Central Standard Time'}))
  DTSTAMP: vDDDTypes(2026-03-04 19:45:05+00:00, Parameters({}))
  DTSTART: vDDDTypes(2026-03-11 11:00:00-05:00, Parameters({'TZID': 'Central Standard Time'}))
  RRULE: vRecur({'FREQ': ['WEEKLY'], 'COUNT': [2], 'INTERVAL': [2], 'BYDAY': ['WE'], 'WKST': ['SU']})
  SEQUENCE: 0
  SUMMARY: vText(b'Copy: All CSIRT - Biweekly Cases / Investigations')
  TRANSP: vText(b'OPAQUE')
  UID: vText(b'AAAAAD2ybyshQsREoRb0X9v1LusHAJDFDPTAQVZHrRcyOf6AV2IAAESTZDEAAJDFDPTAQVZHrRcyOf6AV2IAAESTfB4AAA==')
  X-MICROSOFT-CDO-BUSYSTATUS: vText(b'BUSY')

--- EVENT ---
  CLASS: vText(b'PUBLIC')
  DTEND: vDDDTypes(2026-03-12 17:00:00-04:00, Parameters({'TZID': 'Eastern Standard Time'}))
  DTSTAMP: vDDDTypes(2026-03-04 19:45:05+00:00, Parameters({}))
  DTSTART: vDDDTypes(2026-03-12 16:30:00-04:00, Parameters({'TZID': 'Eastern Standard Time'}))
  SEQUENCE: 0
  SUMMARY: vText(b'Copy: Splunk Follow Up: GMF and Slower ')
  TRANSP: vText(b'OPAQUE')
  UID: vText(b'AAAAAD2ybyshQsREoRb0X9v1LusHAJDFDPTAQVZHrRcyOf6AV2IAAESTZDEAAJDFDPTAQVZHrRcyOf6AV2IAAESTfB8AAA==')
  X-MICROSOFT-CDO-BUSYSTATUS: vText(b'BUSY')

--- EVENT ---
  CLASS: vText(b'PUBLIC')
  DTEND: vDDDTypes(2026-03-20 15:00:00-05:00, Parameters({'TZID': 'Central Standard Time'}))
  DTSTAMP: vDDDTypes(2026-03-04 19:45:05+00:00, Parameters({}))
  DTSTART: vDDDTypes(2026-03-20 14:00:00-05:00, Parameters({'TZID': 'Central Standard Time'}))
  RRULE: vRecur({'FREQ': ['MONTHLY'], 'COUNT': [1], 'BYDAY': ['FR'], 'BYSETPOS': [3]})
  SEQUENCE: 0
  SUMMARY: vText(b'Copy: Monthly - CSIRT & TIE - Alert discussion')
  TRANSP: vText(b'OPAQUE')
  UID: vText(b'AAAAAD2ybyshQsREoRb0X9v1LusHAJDFDPTAQVZHrRcyOf6AV2IAAESTZDEAAJDFDPTAQVZHrRcyOf6AV2IAAESTfCAAAA==')
  X-MICROSOFT-CDO-BUSYSTATUS: vText(b'BUSY')
```

**Total events in file:** 13

---

## Task 3 — Existing Meetings in Database

```
SELECT COUNT(*) as total_meetings,
       COUNT(outlook_recurring_id) as has_recurring_id,
       COUNT(outlook_event_id) as has_event_id
FROM meetings;
```

**ERROR:** Column `outlook_event_id` does not exist — query failed as expected.

Fallback queries run separately:

```
SELECT COUNT(*) as total_meetings FROM meetings;
SELECT COUNT(outlook_recurring_id) as has_recurring_id FROM meetings;
```

| metric               | value |
|----------------------|-------|
| total_meetings       | 49    |
| has_recurring_id     | 21    |
| has_event_id         | N/A — column does not exist |

---

## Environment Notes

- **icalendar:** Newly installed — v7.0.3 (was not present in venv)
- **Python version:** Python 3.12.3
- **Installation command:** `pip install icalendar --break-system-packages`
