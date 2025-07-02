#!/usr/bin/env python3
"""
Basic usage example for the Huefy Python SDK.

This example demonstrates:
1. Creating a Huefy client
2. Sending single emails
3. Sending bulk emails
4. Error handling
5. Health checks
6. Async operations
7. Custom configurations
"""

import asyncio
import os
import time
from typing import Dict, Any, List

from teracrafts_huefy import HuefyClient, AsyncHuefyClient
from teracrafts_huefy.models import EmailProvider, SendEmailRequest
from teracrafts_huefy.exceptions import (
    HuefyException,
    ValidationException,
    AuthenticationException,
    NetworkException,
    TimeoutException
)
from teracrafts_huefy.config import HuefyConfig, RetryConfig


# Helper data classes
class User:
    def __init__(self, name: str, email: str, company: str = None):
        self.name = name
        self.email = email
        self.company = company


def main():
    """Main function demonstrating various SDK features."""
    # Get API key from environment variable or use default
    api_key = os.getenv("HUEFY_API_KEY", "your-huefy-api-key")
    if api_key == "your-huefy-api-key":
        print("Warning: Using default API key. Set HUEFY_API_KEY environment variable.")

    try:
        # Example 1: Basic client creation and single email
        print("=== Basic Email Sending ===")
        basic_email_example(api_key)

        # Example 2: Bulk email sending
        print("\n=== Bulk Email Sending ===")
        bulk_email_example(api_key)

        # Example 3: Health check
        print("\n=== API Health Check ===")
        health_check_example(api_key)

        # Example 4: Using different email providers
        print("\n=== Multiple Email Providers ===")
        multiple_providers_example(api_key)

        # Example 5: Custom configuration
        print("\n=== Custom Configuration ===")
        custom_configuration_example(api_key)

        # Example 6: Context manager usage
        print("\n=== Context Manager Usage ===")
        context_manager_example(api_key)

        # Example 7: Error handling
        print("\n=== Error Handling Examples ===")
        error_handling_example(api_key)

        # Example 8: Async operations
        print("\n=== Async Operations ===")
        asyncio.run(async_operations_example(api_key))

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

    print("\n=== Python example completed ===")


def basic_email_example(api_key: str):
    """Demonstrate basic email sending."""
    client = HuefyClient(api_key)

    email_data = {
        "name": "John Doe",
        "company": "Acme Corporation",
        "activation_link": "https://app.example.com/activate/abc123",
        "support_email": "support@example.com"
    }

    try:
        response = client.send_email(
            template_key="welcome-email",
            recipient="john@example.com",
            data=email_data,
            provider=EmailProvider.SENDGRID
        )

        print("✅ Email sent successfully!")
        print(f"Message ID: {response.message_id}")
        print(f"Provider: {response.provider.value}")
        print(f"Status: {response.status}")

    except HuefyException as e:
        print(f"❌ Failed to send email: {e}")


def bulk_email_example(api_key: str):
    """Demonstrate bulk email sending."""
    client = HuefyClient(api_key)

    users = [
        User("Alice Johnson", "alice@example.com", "Tech Corp"),
        User("Bob Smith", "bob@example.com", "Startup Inc"),
        User("Carol Davis", "carol@example.com")
    ]

    requests = []
    for user in users:
        user_data = {
            "name": user.name,
            "company": user.company or "Your Organization",
            "activation_link": f"https://app.example.com/activate/{int(time.time())}",
            "support_email": "support@example.com"
        }

        request = SendEmailRequest(
            template_key="welcome-email",
            recipient=user.email,
            data=user_data,
            provider=EmailProvider.SENDGRID
        )
        requests.append(request)

    try:
        response = client.send_bulk_emails(requests)

        print("✅ Bulk email operation completed!")
        print(f"Total emails: {response.total_emails}")
        print(f"Successful: {response.successful_emails}")
        print(f"Failed: {response.failed_emails}")
        print(f"Success rate: {response.success_rate:.1f}%")

        if response.failed_emails > 0:
            print("❌ Failed emails:")
            for result in response.failed_results:
                print(f"  - {result.get('recipient', 'Unknown')}: {result.get('error', 'Unknown error')}")

    except HuefyException as e:
        print(f"❌ Failed to send bulk emails: {e}")


def health_check_example(api_key: str):
    """Demonstrate health check."""
    client = HuefyClient(api_key)

    try:
        health = client.health_check()

        if health.status.lower() == "healthy":
            print("✅ API is healthy")
        elif health.status.lower() == "degraded":
            print("⚠️ API is degraded")
        else:
            print("❌ API is unhealthy")

        print(f"Version: {health.version}")
        print(f"Uptime: {health.uptime // 3600} hours")
        print(f"Timestamp: {health.timestamp}")

    except HuefyException as e:
        print(f"❌ Health check failed: {e}")


def multiple_providers_example(api_key: str):
    """Demonstrate using different email providers."""
    client = HuefyClient(api_key)

    providers = [
        EmailProvider.SENDGRID,
        EmailProvider.MAILGUN,
        EmailProvider.SES,
        EmailProvider.MAILCHIMP
    ]

    test_data = {
        "message": "Testing provider functionality",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    for provider in providers:
        try:
            response = client.send_email(
                template_key="test-template",
                recipient="test@example.com",
                data=test_data,
                provider=provider
            )
            print(f"✅ {provider.value}: {response.message_id}")

        except HuefyException as e:
            print(f"❌ {provider.value}: {e}")


def custom_configuration_example(api_key: str):
    """Demonstrate custom configuration."""
    retry_config = RetryConfig(
        max_retries=5,
        base_delay=2.0,
        max_delay=60.0
    )

    config = HuefyConfig(
        base_url="https://api.huefy.com",
        timeout=45.0,
        retry_config=retry_config
    )

    client = HuefyClient(api_key, config)

    email_data = {
        "username": "johndoe",
        "reset_link": "https://app.example.com/reset/xyz789",
        "expires_at": "2024-01-02 15:30:00"
    }

    try:
        response = client.send_email(
            template_key="password-reset",
            recipient="user@example.com",
            data=email_data,
            provider=EmailProvider.MAILGUN
        )
        print(f"✅ Password reset email sent: {response.message_id}")

    except HuefyException as e:
        print(f"❌ Failed to send password reset email: {e}")


def context_manager_example(api_key: str):
    """Demonstrate context manager usage."""
    config = HuefyConfig(timeout=30.0)

    # Using client as context manager
    with HuefyClient(api_key, config) as client:
        email_data = {
            "user_name": "Context Manager User",
            "message": "This email was sent using context manager"
        }

        try:
            response = client.send_email(
                template_key="context-test",
                recipient="context@example.com",
                data=email_data,
                provider=EmailProvider.SES
            )
            print(f"✅ Context manager email sent: {response.message_id}")

        except HuefyException as e:
            print(f"❌ Context manager email failed: {e}")


def error_handling_example(api_key: str):
    """Demonstrate comprehensive error handling."""
    client = HuefyClient(api_key)

    # Example 1: Validation error
    try:
        response = client.send_email(
            template_key="",  # Invalid empty template key
            recipient="test@example.com",
            data={"message": "Test"}
        )
    except ValidationException as e:
        print(f"Validation Error: {e.message}")
        if hasattr(e, 'field') and e.field:
            print(f"Field: {e.field}")
    except HuefyException as e:
        print(f"Unexpected error: {e}")

    # Example 2: Invalid email address
    try:
        response = client.send_email(
            template_key="test-template",
            recipient="invalid-email-address",
            data={"message": "Test"}
        )
    except ValidationException as e:
        print(f"Email validation error: {e.message}")
    except HuefyException as e:
        print(f"Unexpected error: {e}")

    # Example 3: Authentication error (using invalid API key)
    try:
        invalid_client = HuefyClient("invalid-api-key")
        response = invalid_client.send_email(
            template_key="test-template",
            recipient="test@example.com",
            data={"message": "Test"}
        )
    except AuthenticationException as e:
        print(f"Authentication Error: {e.message}")
        print("💡 Please check your API key configuration.")
    except HuefyException as e:
        print(f"Unexpected error: {e}")

    # Example 4: Timeout handling
    try:
        timeout_config = HuefyConfig(timeout=0.001)  # Very short timeout
        timeout_client = HuefyClient(api_key, timeout_config)
        
        response = timeout_client.send_email(
            template_key="test-template",
            recipient="timeout-test@example.com",
            data={"message": "This will timeout"}
        )
    except TimeoutException as e:
        print(f"Expected timeout occurred: {e.message}")
    except NetworkException as e:
        print(f"Network error: {e.message}")
    except HuefyException as e:
        print(f"Other error: {e}")


async def async_operations_example(api_key: str):
    """Demonstrate async operations."""
    config = HuefyConfig(timeout=30.0)
    
    async with AsyncHuefyClient(api_key, config) as client:
        email_data = {
            "name": "Async User",
            "message": "This email was sent asynchronously"
        }

        try:
            # Send single email asynchronously
            response = await client.send_email(
                template_key="async-test",
                recipient="async@example.com",
                data=email_data,
                provider=EmailProvider.SES
            )
            print(f"✅ Async email sent: {response.message_id}")

            # Send multiple emails concurrently
            tasks = []
            for i in range(3):
                task = client.send_email(
                    template_key="async-bulk-test",
                    recipient=f"async{i}@example.com",
                    data={"name": f"Async User {i}", "index": i},
                    provider=EmailProvider.SENDGRID
                )
                tasks.append(task)

            # Wait for all emails to complete
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = 0
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    print(f"❌ Async email {i} failed: {response}")
                else:
                    print(f"✅ Async email {i} sent: {response.message_id}")
                    successful += 1

            print(f"Async bulk operation: {successful}/{len(tasks)} successful")

        except HuefyException as e:
            print(f"❌ Async operation failed: {e}")


def handle_email_error(error: HuefyException, operation: str):
    """Helper function for error handling."""
    print(f"❌ {operation} failed: ", end="")

    if isinstance(error, ValidationException):
        print(f"Validation error - {error.message}")
        if hasattr(error, 'field') and error.field:
            print(f"Field: {error.field}")
    elif isinstance(error, AuthenticationException):
        print(f"Authentication error - {error.message}")
        print("💡 Please check your API key configuration.")
    elif isinstance(error, NetworkException):
        print(f"Network error - {error.message}")
        print("💡 Please check your network connection.")
    elif isinstance(error, TimeoutException):
        print(f"Timeout error - {error.message}")
        print("💡 Consider increasing timeout settings.")
    else:
        print(f"Unknown error - {error}")


def newsletter_example(api_key: str):
    """Example of sending a newsletter to multiple subscribers."""
    client = HuefyClient(api_key)

    subscribers = [
        {"name": "Newsletter Subscriber 1", "email": "subscriber1@example.com"},
        {"name": "Newsletter Subscriber 2", "email": "subscriber2@example.com"},
        {"name": "Newsletter Subscriber 3", "email": "subscriber3@example.com"}
    ]

    newsletter_data = {
        "newsletter_title": "Weekly Tech Updates",
        "unsubscribe_link": "https://app.example.com/unsubscribe",
        "articles": [
            {
                "title": "New Features Released",
                "summary": "Discover the latest features in our platform",
                "url": "https://blog.example.com/new-features"
            },
            {
                "title": "Performance Improvements",
                "summary": "Learn about our latest performance optimizations",
                "url": "https://blog.example.com/performance"
            }
        ]
    }

    requests = []
    for subscriber in subscribers:
        data = newsletter_data.copy()
        data["subscriber_name"] = subscriber["name"]

        request = SendEmailRequest(
            template_key="newsletter",
            recipient=subscriber["email"],
            data=data,
            provider=EmailProvider.MAILGUN
        )
        requests.append(request)

    try:
        response = client.send_bulk_emails(requests)
        print(f"✅ Newsletter sent to {response.successful_emails}/{response.total_emails} subscribers")

    except HuefyException as e:
        print(f"❌ Failed to send newsletter: {e}")


if __name__ == "__main__":
    main()