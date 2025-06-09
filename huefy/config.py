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
        base_url: Base URL for the Huefy API
        connect_timeout: Connection timeout in seconds
        read_timeout: Read timeout in seconds
        retry_config: Retry configuration

    Example:
        >>> config = HuefyConfig(
        ...     base_url="https://api.huefy.com",
        ...     connect_timeout=10.0,
        ...     read_timeout=30.0,
        ...     retry_config=RetryConfig(
        ...         max_retries=5,
        ...         backoff_factor=1.0
        ...     )
        ... )
        >>> client = HuefyClient("api-key", config)
    """

    base_url: str = Field(
        default="https://api.huefy.com", description="Base URL for the Huefy API"
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

    @validator("base_url")
    def validate_base_url(cls, v: str) -> str:
        """Validate and normalize base URL."""
        if not v or not v.strip():
            raise ValueError("base_url cannot be empty")
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