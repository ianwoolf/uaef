# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Pluggable judge client abstraction for UAEF's LLM-judge metrics.

``JudgeClient`` is the Protocol every LLM-judge call site in
``uaef.metrics`` goes through (``get_judge_client().invoke(...)``). The
default implementation (:class:`DefaultBedrockJudgeClient`) wraps the shared
:class:`uaef.llm_judge.bedrock_client.BedrockClient`, which owns retry,
error handling, and request formatting. Swap in a custom backend with
``set_judge_client()``.

Note: ``invoke`` takes already-built prompt text. Prompt assembly, injection
defenses, and response validation stay in ``uaef.metrics.utils``
(``build_judge_system_prompt`` / ``build_claude_judge_body`` /
``validate_judge_response`` / ``validate_provenance``) and remain mandatory
at every metric call site — this layer only transports the request.
"""

from typing import Dict, Optional, Protocol, Tuple, runtime_checkable

from uaef.config import get_config
from uaef.llm_judge.bedrock_client import BedrockClient
from uaef.logging import get_logger

logger = get_logger(__name__)


@runtime_checkable
class JudgeClient(Protocol):
    """Minimal interface an LLM-judge backend must provide."""

    def invoke(
        self,
        system: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> Tuple[str, Dict]:
        """Send a judge request and return ``(response_text, metadata)``.

        Args:
            system: The trusted rubric/instructions (already passed through
                ``build_judge_system_prompt``) for the model's system field.
            prompt: The user-turn message (untrusted content already wrapped
                via ``wrap_untrusted``).
            max_tokens: Max tokens for the judge response.
            temperature: Sampling temperature (judge scoring uses 0.0).

        Returns:
            ``(response_text, metadata)`` — response text as str, metadata
            dict (e.g. token ``usage``).
        """


class DefaultBedrockJudgeClient:
    """Default JudgeClient backed by Bedrock via the shared BedrockClient.

    Reads model ID and AWS settings from global config and delegates to
    ``BedrockClient.invoke_model`` (which adds retry/error handling).
    """

    def __init__(self, bedrock: Optional[BedrockClient] = None):
        self._bedrock = bedrock or BedrockClient()

    def invoke(
        self,
        system: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> Tuple[str, Dict]:
        config = get_config()
        return self._bedrock.invoke_model(
            model_id=config.llm_judge.model_id,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
        )


# ------------------------------------------------------------------
# Global instance
# ------------------------------------------------------------------

_judge_client: Optional[JudgeClient] = None


def get_judge_client() -> JudgeClient:
    """Get the global judge client, lazily creating the default Bedrock one."""
    global _judge_client
    if _judge_client is None:
        _judge_client = DefaultBedrockJudgeClient()
    return _judge_client


def set_judge_client(client: JudgeClient) -> None:
    """Replace the global judge client backend."""
    global _judge_client
    _judge_client = client
