"""Configuration classes for the Huefy SDK."""

from typing import Optional

from pydantic import BaseModel, Field, validator


class RetryConfig(BaseModel):
    """Configuration for retry behavior.

    This class defines how the client should handle retries for failed requests,
    including the maximum number of retries, delays between attempts, and exponential backoff.

    Attributes:
        enabled: Whether retries are enabled
        max_retries: Maximum number of retry attempts
        backoff_factor: Factor for exponential backoff delay calculation
        max_delay: Maximum delay between retries in seconds

    Example:
        >>> retry_config = RetryConfig(
        ...     enabled=True,
        ...     max_retries=3,
        ...     backoff_factor=0.5,
        ...     max_delay=30.0
        ... )
    """

    enabled: bool = Field(default=True, description="Whether retries are enabled")
    max_retries: int = Field(
        default=3, ge=0, description="Maximum number of retry attempts"
    )
    backoff_factor: float = Field(
        default=0.5, ge=0.0, description="Factor for exponential backoff delay calculation"
    )
    max_delay: float = Field(
        default=30.0, gt=0.0, description="Maximum delay between retries in seconds"
    )

    @validator("max_retries")
    def validate_max_retries(cls, v: int) -> int:
        """Validate max_retries is non-negative."""
        if v < 0:
            raise ValueError("max_retries must be >= 0")
        return v

    @validator("backoff_factor")
    def validate_backoff_factor(cls, v: float) -> float:
        """Validate backoff_factor is non-negative."""
        if v < 0.0:
            raise ValueError("backoff_factor must be >= 0.0")
        return v

    @classmethod
    def disabled(cls) -> "RetryConfig":
        """Create a disabled retry configuration.

        Returns:
            RetryConfig: A retry configuration with retries disabled
        """
        return cls(enabled=False)


class HuefyConfig(BaseModel):
    """Configuration for the Huefy client.

    This class provides configuration options for customizing the behavior
    of the HuefyClient, including timeouts, retry settings, and API endpoint.

    Attributes:
        base_url: Custom base URL (overrides local setting)
        connect_timeout: Connection timeout in seconds
        read_timeout: Read timeout in seconds
        retry_config: Retry configuration
        local: Use local development endpoints (default: False, uses production)

    Example:
        >>> config = HuefyConfig(
        ...     connect_timeout=10.0,
        ...     read_timeout=30.0,
        ...     retry_config=RetryConfig(
        ...         max_retries=5,
        ...         backoff_factor=1.0
        ...     )
        ... )
        >>> client = HuefyClient("api-key", config)

        # For local development
        >>> local_config = HuefyConfig(local=True)
        >>> client = HuefyClient("api-key", local_config)
    """

    # Production endpoints (default)
    PRODUCTION_HTTP_ENDPOINT: str = "https://api.huefy.dev/api/v1/sdk"
    LOCAL_HTTP_ENDPOINT: str = "http://localhost:8080/api/v1/sdk"

    base_url: Optional[str] = Field(
        default=None, description="Custom base URL (overrides local setting)"
    )
    connect_timeout: float = Field(
        default=10.0, gt=0.0, description="Connection timeout in seconds"
    )
    read_timeout: float = Field(
        default=30.0, gt=0.0, description="Read timeout in seconds"
    )
    retry_config: RetryConfig = Field(
        default_factory=RetryConfig, description="Retry configuration"
    )
    local: bool = Field(
        default=False, description="Use local development endpoints"
    )

    def get_http_endpoint(self) -> str:
        """Get the HTTP endpoint based on configuration.

        Returns:
            str: The HTTP endpoint URL
        """
        if self.base_url:
            return self.base_url.rstrip("/")
        return self.LOCAL_HTTP_ENDPOINT if self.local else self.PRODUCTION_HTTP_ENDPOINT

    @validator("base_url")
    def validate_base_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize base URL."""
        if v is None:
            return v
        if not v.strip():
            return None
        # Remove trailing slash for consistency
        return v.rstrip("/")

    @validator("connect_timeout")
    def validate_connect_timeout(cls, v: float) -> float:
        """Validate connect_timeout is positive."""
        if v <= 0.0:
            raise ValueError("connect_timeout must be > 0.0")
        return v

    @validator("read_timeout")
    def validate_read_timeout(cls, v: float) -> float:
        """Validate read_timeout is positive."""
        if v <= 0.0:
            raise ValueError("read_timeout must be > 0.0")
        return v

    class Config:
        """Pydantic config."""

        validate_assignment = True
        extra = "forbid"