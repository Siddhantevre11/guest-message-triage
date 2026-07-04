import sys

from dotenv import load_dotenv

from backend.config import MissingConfigError, validate_environment


def load_environment():
    load_dotenv()
    try:
        validate_environment()
    except MissingConfigError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
