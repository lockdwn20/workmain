"""
Formats action dicts as human-readable confirmation prompts and classifies
user replies as confirmations or rejections. Does not send messages —
returns formatted strings or Block Kit payloads for the surface to transmit.

Sprint 2: plain conversational text. Sprint 3: Block Kit upgrade.
"""

import json

_CONFIRMATIONS = frozenset({
    "yes", "y", "yep", "yeah", "yup",
    "confirm", "confirmed", "ok", "okay",
    "sure", "correct", "done", "looks good",
    "looks correct", "right", "affirmative",
})

_REJECTIONS = frozenset({
    "no", "n", "nope", "nah",
    "cancel", "abort", "stop",
    "never mind", "nevermind",
})


class ConfirmationGate:
    """Formats action dicts as plain-text confirmation prompts.

    Stateless — safe to share across requests.
    """

    def format_prompt(self, action: dict) -> str:
        """Return a plain-text confirmation prompt for the given action.

        Args:
            action: Structured action dict from IntentParser.parse().

        Returns:
            Human-readable confirmation string ending with "(yes/no)".
        """
        action_type = action.get("action", "")

        if action_type == "create_time_entry":
            mins = int(action.get("duration_minutes", 0))
            desc = action.get("description", "")
            start_time = action.get("start_time", "")
            hrs = mins // 60
            rem = mins % 60
            if hrs and rem:
                dur = f"{hrs}h {rem}m"
            elif hrs:
                dur = f"{hrs}h"
            else:
                dur = f"{rem}m"
            preview = desc[:120] + ("…" if len(desc) > 120 else "")
            time_suffix = f" at {start_time}" if start_time else ""
            return f"I'll log {dur} for '{preview}'{time_suffix}. Confirm? (yes/no)"

        if action_type == "create_note":
            content = action.get("content", "")
            preview = content[:80] + ("…" if len(content) > 80 else "")
            return f"I'll save a note: '{preview}'. Confirm? (yes/no)"

        if action_type == "update_task":
            status = action.get("status", "completed")
            desc = action.get("task_description", "")
            return f"I'll mark '{desc}' as {status}. Confirm? (yes/no)"

        if action_type == "defer_task":
            desc = action.get("task_description", "")
            return f"I'll defer '{desc}' to tomorrow. Confirm? (yes/no)"

        if action_type == "confirm_report":
            rtype = action.get("report_type", "report").replace("_", " ")
            return f"I'll mark the {rtype} as confirmed. Confirm? (yes/no)"

        if action_type == "correct_report":
            rtype = action.get("report_type", "report").replace("_", " ")
            correction = action.get("correction", "")
            preview = correction[:80] + ("…" if len(correction) > 80 else "")
            return f"I'll apply this correction to the {rtype}: '{preview}'. Confirm? (yes/no)"

        if action_type == "deduplicate_task":
            dup = action.get("task_description", "")
            canonical = action.get("canonical_description", "")
            return f"I'll mark '{dup}' as a duplicate of '{canonical}' and dismiss it. Confirm? (yes/no)"

        if action_type == "write_correction_note":
            note = action.get("note", "")
            preview = note[:80] + ("…" if len(note) > 80 else "")
            return f"I'll add correction note: '{preview}'. Confirm? (yes/no)"

        return f"I'll execute '{action_type}'. Confirm? (yes/no)"

    def format_blocks(self, action: dict) -> list:
        """Return a Block Kit payload for confirming the given action.

        Section block contains the description text (120-char truncation,
        same as format_prompt). Actions block contains Approve and Reject buttons.

        Args:
            action: Structured action dict from IntentParser.parse().

        Returns:
            List of Block Kit block dicts.
        """
        prompt = self.format_prompt(action)
        description = prompt
        if description.endswith("(yes/no)"):
            description = description[: -len("(yes/no)")].rstrip()

        return [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": description},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve"},
                        "style": "primary",
                        "action_id": "wm_approve",
                        "value": json.dumps(action),
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject"},
                        "style": "danger",
                        "action_id": "wm_reject",
                        "value": "reject",
                    },
                ],
            },
        ]

    def is_confirmation(self, text: str) -> bool:
        """Return True if text is an affirmative reply.

        Args:
            text: Raw user reply text.
        """
        return text.lower().strip() in _CONFIRMATIONS

    def is_rejection(self, text: str) -> bool:
        """Return True if text is a negative reply.

        Args:
            text: Raw user reply text.
        """
        return text.lower().strip() in _REJECTIONS
