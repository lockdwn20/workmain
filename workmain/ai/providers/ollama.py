"""
Ollama local inference provider — Mistral 7B on Proxmox via REST API.
"""

import json
import urllib.request
import urllib.error

from workmain.ai.base_provider import (
    BaseProvider,
    ProviderUnavailableError,
    ProviderStatus,
    GenerationRequest,
    GenerationResponse,
    ProviderType,
)


class OllamaProvider(BaseProvider):
    """Ollama local inference provider — wraps POST /api/generate."""

    def __init__(self, config: dict):
        super().__init__(config)
        self._host = config.get("host", "localhost")
        self._port = config.get("port", 11434)
        self._model = config.get("model", "mistral")
        self._timeout = config.get("timeout", 30)

    def check_availability(self) -> ProviderStatus:
        """GET /api/tags and confirm configured model is listed."""
        try:
            url = f"http://{self._host}:{self._port}/api/tags"
            resp = urllib.request.urlopen(url, timeout=self._timeout)
            data = json.loads(resp.read())
            available = [m["name"] for m in data.get("models", [])]
            model_base = self._model.split(":")[0]
            if any(m.split(":")[0] == model_base for m in available):
                return ProviderStatus.AVAILABLE
            return ProviderStatus.UNAVAILABLE
        except Exception:
            return ProviderStatus.UNAVAILABLE

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """POST /api/generate with stream=false."""
        if self.check_availability() != ProviderStatus.AVAILABLE:
            raise ProviderUnavailableError(
                f"Ollama ({self._model}) unreachable at {self._host}:{self._port}"
            )

        # The workmain-intent Modelfile owns temperature, top_p, top_k, repeat_penalty.
        # Only num_predict (max_tokens) is sent per-request — it can legitimately vary
        # by call type. generation_options is reserved for explicit per-request overrides.
        options = {"num_predict": request.max_tokens or 512}
        if request.generation_options:
            options.update(request.generation_options)
        raw_mode = bool(options.pop("raw", False))
        json_format = options.pop("format", None)

        payload = {
            "model": self._model,
            "prompt": self._build_prompt(request),
            "stream": False,
            "keep_alive": -1,
            "options": options,
        }
        if raw_mode:
            payload["raw"] = True
        if json_format:
            payload["format"] = json_format

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"http://{self._host}:{self._port}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=self._timeout)
            result = json.loads(resp.read())
            response_text = result.get("response", "").strip()
            prompt_tokens = result.get("prompt_eval_count", 0)
            completion_tokens = result.get("eval_count", 0)

            return GenerationResponse(
                content=response_text,
                provider=ProviderType.OLLAMA,
                model=self._model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                tokens_used=prompt_tokens + completion_tokens,
                cost=0.0,
            )
        except urllib.error.URLError as e:
            raise ProviderUnavailableError(f"Ollama request failed: {e}") from e
        except TimeoutError as e:
            raise ProviderUnavailableError(
                f"Ollama generation timed out after {self._timeout}s"
            ) from e

    def _build_prompt(self, request: GenerationRequest) -> str:
        """Format prompt in Mistral [INST] instruction format."""
        if request.system_prompt:
            return f"[INST] {request.system_prompt}\n\n{request.prompt} [/INST]"
        return f"[INST] {request.prompt} [/INST]"

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Local model — no API cost."""
        return 0.0

    def validate_config(self) -> bool:
        """Returns True if host and port are configured."""
        return bool(self._host and self._port)

    def count_tokens(self, text: str) -> int:
        """Approximate token count (word-based heuristic)."""
        return len(text.split())

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def display_name(self) -> str:
        return "Ollama"

    @property
    def cost_structure(self) -> str:
        return "Local — no API cost"
