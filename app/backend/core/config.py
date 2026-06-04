import logging
import os
from typing import Any, Optional

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Application
    app_name: str = "FastAPI Modular Template"
    debug: bool = False
    version: str = "1.0.0"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    frontend_url: str = "http://localhost:3000"

    # Local development defaults. Production can override all of these with env vars.
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120

    # OpenAI-compatible model gateway
    app_ai_base_url: Optional[str] = None
    app_ai_key: Optional[str] = None
    app_ai_cheap_model: str = "gemini-2.5-flash-lite"
    app_ai_balanced_model: str = "gemini-2.5-flash"
    app_ai_premium_model: str = "gemini-2.5-pro"
    app_ocr_model: str = "gemini-2.5-flash-lite"
    app_ai_fast_model: str = "gemini-2.5-flash-lite"
    app_ai_classifier_model: Optional[str] = "gemini-2.5-flash-lite"
    app_ai_review_model: str = "gemini-2.5-flash"
    app_ai_pdf_model: str = "gemini-2.5-pro"
    app_ai_image_model: str = "gemini-2.5-flash-image"
    app_ai_request_timeout: int = 360
    app_ai_premium_requires_review: bool = True
    case_import_ai_classifier_enabled: bool = True

    # PDF/OCR extraction tuning
    pdf_ocr_dpi: int = 180
    pdf_ocr_max_pages: int = 40
    pdf_ocr_tesseract_lang: str = "chi_sim+eng"

    # Object storage. If omitted, local development falls back to local_storage_dir.
    oss_service_url: Optional[str] = None
    oss_api_key: Optional[str] = None
    local_storage_dir: str = "./local_storage"

    # Optional OIDC settings for production login
    oidc_client_id: Optional[str] = None
    oidc_client_secret: Optional[str] = None
    oidc_issuer_url: Optional[str] = None
    oidc_scope: str = "openid email profile"

    # AWS Lambda Configuration
    is_lambda: bool = False
    lambda_function_name: str = "fastapi-backend"
    aws_region: str = "us-east-1"

    @property
    def backend_url(self) -> str:
        """Generate backend URL from host and port."""
        if self.is_lambda:
            # In Lambda environment, return the API Gateway URL
            return os.environ.get(
                "PYTHON_BACKEND_URL", f"https://{self.lambda_function_name}.execute-api.{self.aws_region}.amazonaws.com"
            )
        else:
            # Use localhost for external callbacks instead of 0.0.0.0
            display_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
            return os.environ.get("PYTHON_BACKEND_URL", f"http://{display_host}:{self.port}")

    class Config:
        case_sensitive = False
        extra = "ignore"
        env_file = ".env"

    def __getattr__(self, name: str) -> Any:
        """
        Dynamically read attributes from environment variables.
        For example: settings.opapi_key reads from OPAPI_KEY environment variable.

        Args:
            name: Attribute name (e.g., 'opapi_key')

        Returns:
            Value from environment variable

        Raises:
            AttributeError: If attribute doesn't exist and not found in environment variables
        """
        # Convert attribute name to environment variable name (snake_case -> UPPER_CASE)
        env_var_name = name.upper()

        # Check if environment variable exists
        if env_var_name in os.environ:
            value = os.environ[env_var_name]
            # Cache the value in instance dict to avoid repeated lookups
            self.__dict__[name] = value
            logger.debug(f"Read dynamic attribute {name} from environment variable {env_var_name}")
            return value

        # If not found, raise AttributeError to maintain normal Python behavior
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


# Global settings instance
settings = Settings()
