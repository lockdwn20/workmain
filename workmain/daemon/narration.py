"""
WorkmAIn Daemon Narration Layer
narration.py v1.1
20260603

Converts a list of Observation objects from the inspection engine into a
concise natural-language summary using the configured AI provider.

This is a single, non-streaming call. It is called only when observations
exist — if the inspection engine returns an empty list, narration is
skipped and the notification body is a standard "nothing flagged" message.

Uses the existing provider abstraction (workmain/ai/). Uses the default
provider configured for daily_internal reports unless overridden.
Max tokens: 200. This is a brief summary, not a full report.

Version History:
- v1.0: Phase 10 Gate 4 initial implementation
- v1.1: Provider Foundation Sprint — remove get_claude_client/get_gemini_client imports
        and register_provider() calls; ProviderManager instantiates from registry
"""

from typing import List, Optional

from workmain.daemon.models import Observation

NARRATION_SYSTEM_PROMPT = """
You are a concise work assistant summarizing a pre-flight check of
the user's workday data. You have been given a list of specific
observations about gaps or anomalies in their recorded notes and
time entries. Write a brief, direct, actionable summary in 3-5
sentences. Use plain language. Do not use bullet points.
Do not add observations not in the provided list.
"""


def narrate(observations: List[Observation],
            provider: Optional[str] = None) -> str:
    """Convert a list of Observation objects into a natural-language summary.

    Returns a plain-text string for use in the notification body.
    If observations is empty, returns a standard "all clear" message
    without making an AI call.

    Args:
        observations: Output of InspectionEngine.run()
        provider: Override the default provider name. If None, uses the
                  daily_internal default from provider config.

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
        return _call_provider(prompt, provider, max_tokens=200, temperature=0.3)
    except Exception:
        fallback = "Pre-flight check found the following:\n"
        fallback += "\n".join(f"• {o.message}" for o in observations)
        return fallback


def _call_provider(prompt: str, provider: Optional[str],
                   max_tokens: int, temperature: float) -> str:
    """Call the AI provider using the existing abstraction.

    Registers Claude and Gemini clients on the shared provider manager
    singleton following the same pattern as ReportGenerator.__init__.

    Args:
        prompt: The user prompt to send.
        provider: Optional provider name override ('claude', 'gemini').
        max_tokens: Maximum tokens for the response.
        temperature: Sampling temperature.

    Returns:
        Generated text content from the provider.
    """
    from workmain.ai.base_provider import GenerationRequest, ProviderType
    from workmain.ai.provider_manager import get_provider_manager

    provider_override = None
    if provider:
        try:
            provider_override = ProviderType(provider.lower())
        except ValueError:
            pass

    manager = get_provider_manager()

    request = GenerationRequest(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        system_prompt=NARRATION_SYSTEM_PROMPT.strip(),
    )
    response, _ = manager.generate(
        request,
        report_type='daily_internal',
        provider_override=provider_override,
    )
    return response.content
