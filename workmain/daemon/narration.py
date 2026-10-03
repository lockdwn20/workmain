"""
Converts a list of Observation objects from the inspection engine into a
concise natural-language summary using the configured AI provider.

This is a single, non-streaming call. It is called only when observations
exist — if the inspection engine returns an empty list, narration is
skipped and the notification body is a standard "nothing flagged" message.

Uses the existing provider abstraction (workmain/ai/). Routes by its own
`application_functions.daemon_narration` entry in config/ai_settings.json.
"""

import logging
from typing import List

from workmain.daemon.models import Observation

logger = logging.getLogger(__name__)

NARRATION_SYSTEM_PROMPT = """
You are a concise work assistant summarizing a pre-flight check of
the user's workday data. You have been given a list of specific
observations about gaps or anomalies in their recorded notes and
time entries. Write a brief, direct, actionable summary in 3-5
sentences. Use plain language. Do not use bullet points.
Do not add observations not in the provided list.
"""


def narrate(observations: List[Observation]) -> str:
    """Convert a list of Observation objects into a natural-language summary.

    Returns a plain-text string for use in the notification body.
    If observations is empty, returns a standard "all clear" message
    without making an AI call.

    Args:
        observations: Output of InspectionEngine.run()

    Returns:
        Plain-text notification body string.
    """
    if not observations:
        return "Pre-flight check complete. No gaps or anomalies flagged."

    observation_text = "\n".join(
        f"- [{o.type.value}] {o.message}" for o in observations
    )
    prompt = (
        f"Pre-flight observations for today:\n\n"
        f"{observation_text}\n\n"
        f"Write a brief summary for the user."
    )

    try:
        return _call_provider(prompt)
    except Exception as e:
        logger.warning("Narration cap or generation failure: %s", e)
        fallback = "Pre-flight check found the following:\n"
        fallback += "\n".join(f"• {o.message}" for o in observations)
        return fallback


def _call_provider(prompt: str) -> str:
    """Call the AI provider using the existing abstraction.

    Args:
        prompt: The user prompt to send.

    Returns:
        Generated text content from the provider.
    """
    from workmain.ai.base_provider import GenerationRequest
    from workmain.ai.provider_manager import get_provider_manager

    manager = get_provider_manager()

    request = GenerationRequest(
        prompt=prompt,
        max_tokens=manager.get_max_tokens('daemon_narration'),
        system_prompt=NARRATION_SYSTEM_PROMPT.strip(),
    )
    response, _ = manager.generate(
        request,
        report_type='daemon_narration',
    )
    return response.content
