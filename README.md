# Huefy Python SDK

The official Python SDK for the Huefy email sending platform. Send template-based emails with support for multiple providers, automatic retries, and comprehensive error handling.

## Installation

### PyPI

Install the SDK using pip:

```bash
pip install huefy
```

### Development Installation

For development with optional dependencies:

```bash
pip install huefy[dev]
```

For async support:

```bash
pip install huefy[async]
```

## Quick Start

```python
from huefy import HuefyClient

# Create client
client = HuefyClient("your-api-key")

# Send email
response = client.send_email(
    template_key="welcome-email",
    recipient="john@example.com",
    data={
        "name": "John Doe",
        "company": "Acme Corp"
    }
)

print(f"Email sent: {response.message_id}")

# Clean up
client.close()
```

### Using Context Manager

```python
from huefy import HuefyClient

with HuefyClient("your-api-key") as client:
    response = client.send_email(
        template_key="welcome-email",
        recipient="john@example.com",
        data={"name": "John Doe"}
    )
    print(f"Email sent: {response.message_id}")
# Client automatically closed
```

## Features

- ✅ **Template-based emails** - Send emails using predefined templates
- ✅ **Multiple providers** - Support for SES, SendGrid, Mailgun, Mailchimp
- ✅ **Automatic retries** - Configurable retry logic with exponential backoff
- ✅ **Error handling** - Comprehensive exception types for different failure scenarios
- ✅ **Bulk emails** - Send multiple emails in a single request
- ✅ **Health checks** - Monitor API health status
- ✅ **Type hints** - Full type annotations for better IDE support
- ✅ **Pydantic models** - Data validation and serialization
- ✅ **Context manager** - Automatic resource cleanup
- ✅ **Python 3.8+** - Compatible with Python 3.8 and later versions

## Configuration

### Basic Configuration

```python
from huefy import HuefyClient

client = HuefyClient("your-api-key")
```

### Advanced Configuration

```python
from huefy import HuefyClient, HuefyConfig, RetryConfig

config = HuefyConfig(
    base_url="https://api.huefy.com",
    connect_timeout=10.0,
    read_timeout=30.0,
    retry_config=RetryConfig(
        enabled=True,
        max_retries=5,
        backoff_factor=1.0,
        max_delay=30.0
    )
)

client = HuefyClient("your-api-key", config)
```

## API Reference

### Client Creation

#### `HuefyClient(api_key: str, config: Optional[HuefyConfig] = None)`

Creates a new Huefy client with the provided API key and optional configuration.

**Parameters:**
- `api_key` (str): The Huefy API key
- `config` (HuefyConfig, optional): Client configuration

**Raises:**
- `ValueError`: If api_key is None or empty

### Email Operations

#### `send_email(template_key: str, recipient: str, data: Dict[str, Any], provider: Optional[EmailProvider] = None) -> SendEmailResponse`

Sends a single email using a template.

```python
from huefy import EmailProvider

response = client.send_email(
    template_key="welcome-email",
    recipient="john@example.com",
    data={
        "name": "John Doe",
        "company": "Acme Corp"
    },
    provider=EmailProvider.SENDGRID  # Optional
)
```

#### `send_bulk_emails(requests: List[SendEmailRequest]) -> BulkEmailResponse`

Sends multiple emails in a single request.

```python
from huefy import SendEmailRequest

requests = [
    SendEmailRequest(
        template_key="welcome-email",
        recipient="john@example.com",
        data={"name": "John Doe"}
    ),
    SendEmailRequest(
        template_key="welcome-email",
        recipient="jane@example.com",
        data={"name": "Jane Doe"}
    )
]

response = client.send_bulk_emails(requests)
```

#### `health_check() -> HealthResponse`

Checks the API health status.

```python
health = client.health_check()
print(f"API Status: {health.status}")
```

### Resource Management

#### `close() -> None`

Closes the HTTP session and releases resources.

```python
client.close()
```

#### Context Manager Support

```python
with HuefyClient("api-key") as client:
    # Use client
    pass
# Automatically closed
```

## Error Handling

The SDK provides specific exception types for different failure scenarios:

```python
from huefy import (
    HuefyError,
    AuthenticationError,
    TemplateNotFoundError,
    RateLimitError,
    ProviderError,
    NetworkError,
    ValidationError
)

try:
    response = client.send_email(
        template_key="welcome-email",
        recipient="john@example.com",
        data={"name": "John Doe"}
    )
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except TemplateNotFoundError as e:
    print(f"Template '{e.template_key}' not found")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except ProviderError as e:
    print(f"Provider {e.provider} error: {e.provider_code}")
except NetworkError as e:
    print(f"Network error: {e}")
except ValidationError as e:
    print(f"Validation error: {e}")
except HuefyError as e:
    print(f"Huefy error: {e}")
```

### Exception Types

- `AuthenticationError` - Invalid API key or authentication failure
- `TemplateNotFoundError` - Specified template doesn't exist
- `InvalidTemplateDataError` - Template data validation failed
- `InvalidRecipientError` - Invalid recipient email address
- `ProviderError` - Email provider rejected the message
- `RateLimitError` - Rate limit exceeded
- `NetworkError` - Network connectivity issues
- `TimeoutError` - Request timeout
- `ValidationError` - Request validation failed
- `HuefyError` - Base exception for all SDK errors

## Models

### EmailProvider

Supported email providers:

```python
from huefy import EmailProvider

EmailProvider.SES        # Amazon SES
EmailProvider.SENDGRID   # SendGrid
EmailProvider.MAILGUN    # Mailgun
EmailProvider.MAILCHIMP  # Mailchimp Transactional
```

### SendEmailRequest

Email request model:

```python
from huefy import SendEmailRequest, EmailProvider

request = SendEmailRequest(
    template_key="welcome-email",
    recipient="john@example.com",
    data={"name": "John Doe"},
    provider=EmailProvider.SES  # Optional
)
```

### SendEmailResponse

Email response model:

```python
response = client.send_email(...)
print(f"Message ID: {response.message_id}")
print(f"Status: {response.status}")
print(f"Provider: {response.provider}")
print(f"Timestamp: {response.timestamp}")
```

## Configuration

### HuefyConfig

Client configuration:

```python
from huefy import HuefyConfig

config = HuefyConfig(
    base_url="https://api.huefy.com",     # API base URL
    connect_timeout=10.0,                 # Connection timeout in seconds
    read_timeout=30.0,                    # Read timeout in seconds
    retry_config=RetryConfig(...)         # Retry configuration
)
```

### RetryConfig

Retry behavior configuration:

```python
from huefy import RetryConfig

retry_config = RetryConfig(
    enabled=True,           # Enable retries
    max_retries=3,          # Maximum number of retries
    backoff_factor=0.5,     # Backoff factor for exponential delay
    max_delay=30.0          # Maximum delay between retries
)

# Disable retries
retry_config = RetryConfig.disabled()
```

Retries are automatically performed for:
- Network errors
- Timeout errors
- Rate limit errors (429)
- Server errors (5xx)

## Examples

### Basic Email Sending

```python
from huefy import HuefyClient

with HuefyClient("your-api-key") as client:
    response = client.send_email(
        template_key="welcome-email",
        recipient="user@example.com",
        data={
            "name": "John Doe",
            "company": "Acme Corp",
            "signup_date": "2024-01-01"
        }
    )
    print(f"Welcome email sent: {response.message_id}")
```

### Bulk Email Sending

```python
from huefy import HuefyClient, SendEmailRequest

# Prepare multiple email requests
requests = [
    SendEmailRequest(
        template_key="newsletter",
        recipient="john@example.com",
        data={"name": "John", "topic": "Product Updates"}
    ),
    SendEmailRequest(
        template_key="newsletter",
        recipient="jane@example.com",
        data={"name": "Jane", "topic": "Product Updates"}
    )
]

with HuefyClient("your-api-key") as client:
    response = client.send_bulk_emails(requests)
    
    successful = sum(1 for result in response.results if result.success)
    failed = len(response.results) - successful
    
    print(f"Bulk email completed: {successful} sent, {failed} failed")
```

### Error Handling with Specific Provider

```python
from huefy import (
    HuefyClient,
    EmailProvider,
    ProviderError,
    RateLimitError
)

with HuefyClient("your-api-key") as client:
    try:
        response = client.send_email(
            template_key="transactional-email",
            recipient="customer@example.com",
            data={"order_id": "12345", "amount": "$99.99"},
            provider=EmailProvider.SENDGRID
        )
        print(f"Order confirmation sent: {response.message_id}")
        
    except ProviderError as e:
        print(f"SendGrid error [{e.provider_code}]: {e.message}")
        # Maybe retry with different provider
        
    except RateLimitError as e:
        print(f"Rate limited. Retry after {e.retry_after} seconds")
        # Implement backoff logic
```

### Health Check Monitoring

```python
from huefy import HuefyClient, NetworkError

def check_api_health():
    try:
        with HuefyClient("your-api-key") as client:
            health = client.health_check()
            print(f"API Status: {health.status}")
            print(f"Timestamp: {health.timestamp}")
            if health.version:
                print(f"Version: {health.version}")
            return health.status == "healthy"
    except NetworkError:
        print("API is unreachable")
        return False
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

if check_api_health():
    print("✅ API is healthy")
else:
    print("❌ API is unhealthy")
```

## Testing

Run the test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=huefy --cov-report=html
```

Run specific test file:

```bash
pytest tests/test_client.py -v
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/huefy/huefy-sdk.git
cd huefy-sdk/sdks/python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

### Code Quality

Run code formatting:

```bash
black huefy tests
isort huefy tests
```

Run linting:

```bash
flake8 huefy tests
mypy huefy
```

### Building Distribution

```bash
python -m build
```

## Requirements

- Python 3.8 or later
- Valid Huefy API key

## Dependencies

- [requests](https://docs.python-requests.org/) - HTTP library
- [pydantic](https://docs.pydantic.dev/) - Data validation and settings management
- [typing-extensions](https://pypi.org/project/typing-extensions/) - Backport of newer typing features (Python < 3.10)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For support and questions:

- 📧 Email: support@huefy.com
- 📖 Documentation: https://docs.huefy.com
- 🐛 Issues: https://github.com/huefy/huefy-sdk/issues