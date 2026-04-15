"""
LLM client wrapper
Unified OpenAI-compatible API calls
"""

import json
import re
import threading
from typing import Optional, Dict, Any, List
from openai import OpenAI

from ..config import Config
from .logger import get_logger

_cost_logger = get_logger('mirofish.llm.cost')

# Approximate prices in USD per 1M tokens (input, output). OpenRouter-style slugs.
# Unknown models fall back to (0, 0) — tokens still logged, cost shown as "n/a".
# Update as pricing changes; this is a rough running estimate, not an invoice.
_PRICE_TABLE: Dict[str, tuple] = {
    # Anthropic
    "anthropic/claude-haiku-4-5": (1.00, 5.00),
    "anthropic/claude-sonnet-4-5": (3.00, 15.00),
    "anthropic/claude-opus-4-5": (15.00, 75.00),
    # Google
    "google/gemini-2.0-flash-001": (0.10, 0.40),
    "google/gemini-2.5-flash": (0.30, 2.50),
    # DeepSeek
    "deepseek/deepseek-chat": (0.14, 0.28),
    "deepseek/deepseek-chat-v3": (0.14, 0.28),
    # OpenAI
    "openai/gpt-4o-mini": (0.15, 0.60),
    "openai/gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    # Meta
    "meta-llama/llama-3.3-70b-instruct": (0.13, 0.40),
}

# Process-wide running totals. Thread-safe, reset on process restart.
_TOTALS_LOCK = threading.Lock()
_TOTALS = {"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "calls": 0}


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    in_price, out_price = _PRICE_TABLE.get(model, (0.0, 0.0))
    return (prompt_tokens * in_price + completion_tokens * out_price) / 1_000_000


def get_cost_totals() -> Dict[str, Any]:
    """Return a copy of the running LLM spend totals since process start."""
    with _TOTALS_LOCK:
        return dict(_TOTALS)


class LLMClient:
    """LLM client"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME

        if not self.api_key:
            raise ValueError("LLM_API_KEY is not configured")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Send a chat request.

        Args:
            messages: List of messages
            temperature: Temperature parameter
            max_tokens: Maximum number of tokens
            response_format: Response format (e.g., JSON mode)

        Returns:
            Model response text
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)

        # Token & cost accounting. usage may be absent on some proxies; treat as best-effort.
        try:
            usage = getattr(response, "usage", None)
            if usage is not None:
                pt = int(getattr(usage, "prompt_tokens", 0) or 0)
                ct = int(getattr(usage, "completion_tokens", 0) or 0)
                cost = _estimate_cost(self.model, pt, ct)
                cost_str = f"${cost:.6f}" if self.model in _PRICE_TABLE else "n/a"
                with _TOTALS_LOCK:
                    _TOTALS["prompt_tokens"] += pt
                    _TOTALS["completion_tokens"] += ct
                    _TOTALS["cost_usd"] += cost
                    _TOTALS["calls"] += 1
                    running = dict(_TOTALS)
                _cost_logger.info(
                    "llm_call model=%s in=%d out=%d cost=%s | run_totals calls=%d in=%d out=%d cost=$%.4f",
                    self.model, pt, ct, cost_str,
                    running["calls"], running["prompt_tokens"],
                    running["completion_tokens"], running["cost_usd"],
                )
        except Exception as e:
            _cost_logger.debug("cost accounting skipped: %s", e)

        content = response.choices[0].message.content
        # Some models (e.g., MiniMax M2.5) may include <think> reasoning content that needs to be removed
        content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
        return content

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Send a chat request and return JSON.

        Args:
            messages: List of messages
            temperature: Temperature parameter
            max_tokens: Maximum number of tokens

        Returns:
            Parsed JSON object
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        # Clean up markdown code block markers
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON returned by LLM: {cleaned_response}")
