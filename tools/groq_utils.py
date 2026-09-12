import os
import time
from typing import Any
from dotenv import load_dotenv
from groq import Groq, RateLimitError, APIStatusError, NotFoundError

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
PRIMARY_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "openai/gpt-oss-20b")


def create_chat_completion(*, messages: list[dict[str, str]], model: str | None = None, stream: bool = False, **kwargs) -> Any:
    """Create a Groq chat completion with automatic fallback on rate limit or missing models.

    Behavior:
    - If `model` is None, the client default is used.
    - On `RateLimitError`, retries with `FALLBACK_MODEL` then without explicit model.
    - On `APIStatusError` with 429-like messages, same retry logic.
    - On `NotFoundError` for model, retries without explicit model.
    """
    # Determine initial model to use
    if model is None:
        model_to_use = PRIMARY_MODEL
    else:
        model_to_use = model

    # Build call options; only include model if specified
    opts = {"messages": messages, "stream": stream, **kwargs}
    if model_to_use:
        opts["model"] = model_to_use

    try:
        return client.chat.completions.create(**opts)
    except RateLimitError as error:
        # Try fallback model, then without explicit model
        if model_to_use and model_to_use != FALLBACK_MODEL:
            print(f"⚠️ Rate limit hit for {model_to_use}; retrying with fallback {FALLBACK_MODEL}")
            return create_chat_completion(messages=messages, model=FALLBACK_MODEL, stream=stream, **kwargs)
        if model_to_use and model_to_use == FALLBACK_MODEL:
            print(f"⚠️ Rate limit on fallback {FALLBACK_MODEL}; retrying without explicit model")
            return create_chat_completion(messages=messages, model=None, stream=stream, **kwargs)
        raise
    except APIStatusError as error:
        message = str(error).lower()
        status = getattr(error, "status_code", None)
        if status == 429 or "rate limit" in message or "tokens" in message:
            if model_to_use and model_to_use != FALLBACK_MODEL:
                print(f"⚠️ API status 429 for {model_to_use}; retrying with fallback {FALLBACK_MODEL}")
                return create_chat_completion(messages=messages, model=FALLBACK_MODEL, stream=stream, **kwargs)
            if model_to_use:
                print(f"⚠️ API status 429 for {model_to_use}; retrying without explicit model")
                return create_chat_completion(messages=messages, model=None, stream=stream, **kwargs)
        raise
    except NotFoundError as error:
        # Model not found — retry without explicit model
        if model_to_use:
            print(f"⚠️ Model {model_to_use} not found; retrying without explicit model")
            return create_chat_completion(messages=messages, model=None, stream=stream, **kwargs)
        raise
