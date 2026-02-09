import os
from functools import lru_cache

from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Settings(BaseModel):
    simple_password: str | None = os.environ.get("SIMPLE_PASSWORD")
    # Azure OpenAI (optional)
    azure_openai_api_key: str | None = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment_name: str | None = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1")
    azure_openai_api_version: str | None = os.getenv("AZURE_OPENAI_VERSION", "2024-12-01-preview")
    # Gemini (Vertex AI service account – optional; preferred if set)
    gemini_project_id: str | None = os.getenv("GEMINI_PROJECT_ID")
    gemini_client_email: str | None = os.getenv("GEMINI_CLIENT_EMAIL")
    gemini_private_key: str | None = os.getenv("GEMINI_PRIVATE_KEY")
    gemini_private_key_id: str | None = os.getenv("GEMINI_PRIVATE_KEY_ID")
    gemini_client_id: str | None = os.getenv("GEMINI_CLIENT_ID")
    gemini_token_uri: str | None = os.getenv("GEMINI_TOKEN_URI", "https://oauth2.googleapis.com/token")
    gemini_auth_uri: str | None = os.getenv("GEMINI_AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
    gemini_auth_provider_x509_cert_url: str | None = os.getenv("GEMINI_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs")
    gemini_client_x509_cert_url: str | None = os.getenv("GEMINI_CLIENT_X509_CERT_URL")
    gemini_location: str | None = os.getenv("GEMINI_LOCATION")
    gemini_model: str | None = os.getenv("GEMINI_MODEL", "gemini-3-pro")
    # DB / infra
    mongo_uri: str | None = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")
    postgres_dsn: str | None = os.getenv("POSTGRES_DSN")
    redis_url: str | None = os.getenv("REDIS_URL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def check_password(token: str | None) -> bool:
    settings = get_settings()
    if not settings.simple_password:
        # If no password configured, treat as open (for local dev only).
        return True
    return token == settings.simple_password

