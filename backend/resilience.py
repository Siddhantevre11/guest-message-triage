import time

from groq import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

TRANSIENT_ERRORS = (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError)


class RetriesExhaustedError(Exception):
    pass


def invoke_with_retry(chain, messages, max_attempts=3, backoff_seconds=1):
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return chain.invoke(messages)
        except TRANSIENT_ERRORS as e:
            last_error = e
            if attempt < max_attempts:
                time.sleep(backoff_seconds * attempt)
    raise RetriesExhaustedError(f"Exceeded {max_attempts} attempts") from last_error
