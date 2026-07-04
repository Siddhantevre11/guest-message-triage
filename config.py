import os

REQUIRED_ENV_VARS = ["GROQ_API_KEY"]


class MissingConfigError(Exception):
    pass


def validate_environment():
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        raise MissingConfigError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            f"Copy .env.example to .env and set them."
        )
