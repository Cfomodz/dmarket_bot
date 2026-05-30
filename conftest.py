import os

# Provide dummy credentials so config.py's import-time check doesn't abort unit tests.
# Real credentials in .env still take precedence (setdefault won't overwrite them).
os.environ.setdefault("DMARKET_PUBLIC_KEY", "test_public_key")
os.environ.setdefault("DMARKET_SECRET_KEY", "0" * 128)
