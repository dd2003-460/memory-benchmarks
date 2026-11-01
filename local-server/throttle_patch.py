"""Monkey-patch: make mem0's LLM calls retry with longer backoff on 5xx.

The stock openai client retries 2x with <1s backoff — too aggressive for a
shared vLLM endpoint that returns transient 502s under concurrent load.

Patches both the sync and async client classes, guarding against
re-entrancy (uvicorn may import twice / reload).
"""
import logging
import time

import openai
from openai import AsyncOpenAI, OpenAI
from openai.resources.chat.completions import AsyncCompletions, Completions

logger = logging.getLogger("mem0-server")

_MAX_ATTEMPTS = 8
_BACKOFF_BASE = 2.0  # seconds; doubles each retry, capped at 30s
_BACKOFF_CAP = 30.0


def _is_transient(exc: Exception) -> bool:
    """5xx / connection errors are transient; 4xx (auth, bad request) are not."""
    if isinstance(exc, (openai.APIConnectionError, openai.APITimeoutError)):
        return True
    status = getattr(exc, "status_code", None)
    return status is not None and status >= 500


def _patch_sync(cls):
    if getattr(cls, "_mb_patched", False):
        return
    orig = cls.create

    def create(self, *args, **kwargs):
        attempt = 0
        while True:
            try:
                return orig(self, *args, **kwargs)
            except Exception as e:  # noqa: BLE001
                attempt += 1
                if attempt >= _MAX_ATTEMPTS or not _is_transient(e):
                    raise
                delay = min(_BACKOFF_BASE * (2 ** (attempt - 1)), _BACKOFF_CAP)
                logger.warning(
                    "Transient LLM error (%s), retry %d/%d in %.1fs",
                    e.__class__.__name__, attempt, _MAX_ATTEMPTS - 1, delay,
                )
                time.sleep(delay)

    cls.create = create
    cls._mb_patched = True


def _patch_async(cls):
    import asyncio

    if getattr(cls, "_mb_patched", False):
        return
    orig = cls.create

    async def create(self, *args, **kwargs):
        attempt = 0
        while True:
            try:
                return await orig(self, *args, **kwargs)
            except Exception as e:  # noqa: BLE001
                attempt += 1
                if attempt >= _MAX_ATTEMPTS or not _is_transient(e):
                    raise
                delay = min(_BACKOFF_BASE * (2 ** (attempt - 1)), _BACKOFF_CAP)
                logger.warning(
                    "Transient LLM error (%s), retry %d/%d in %.1fs",
                    e.__class__.__name__, attempt, _MAX_ATTEMPTS - 1, delay,
                )
                await asyncio.sleep(delay)

    cls.create = create
    cls._mb_patched = True


def apply():
    _patch_sync(Completions)
    _patch_async(AsyncCompletions)
    logger.info("LLM retry patch applied (max %d attempts, backoff %.0f-%.0fs)",
                _MAX_ATTEMPTS, _BACKOFF_BASE, _BACKOFF_CAP)
