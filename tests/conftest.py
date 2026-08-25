"""Shared pytest setup for local, environment-backed graph smoke tests."""

from dotenv import load_dotenv

# Load repository-local provider configuration before test modules evaluate skip markers.
# The .env file is gitignored; no secret is copied into test output or committed artifacts.
load_dotenv()
