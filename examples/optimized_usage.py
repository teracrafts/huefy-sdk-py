"""
Example: Using Huefy Python SDK with Enhanced Architecture

This example demonstrates how the Python SDK automatically uses Huefy's
optimized architecture for enhanced security and performance.
"""

from teracrafts_huefy import HuefyClient, HuefyConfig, EmailProvider

# The SDK automatically uses Huefy's optimized architecture
# No additional configuration needed for standard usage

def main():
    # Create client - automatically uses secure optimized routing
    client = HuefyClient(
        api_key="your-api-key"
        # Configuration is automatically optimized
    )

    try:
        # The Python SDK automatically handles secure API communication
        # through the optimized proxy architecture
        response = client.send_email(
            template_key="welcome-email",
            recipient="john@example.com",
            data={
                "name": "John Doe",
                "company": "Acme Corp",
                "activation_link": "https://app.example.com/activate/12345"
            },
            provider=EmailProvider.SES
        )

        print("Email sent successfully!")
        print(f"Message ID: {response.message_id}")
        print(f"Provider used: {response.provider}")
        
        # Check API health through optimized routing
        health = client.health_check()
        print(f"API Health: {health.status}")
        
        # Send bulk emails efficiently
        bulk_response = client.send_bulk_emails([
            {
                "template_key": "welcome-email",
                "recipient": "user1@example.com",
                "data": {"name": "User 1"},
            },
            {
                "template_key": "welcome-email", 
                "recipient": "user2@example.com",
                "data": {"name": "User 2"},
                "provider": EmailProvider.SENDGRID
            }
        ])
        
        print(f"Bulk emails sent: {len(bulk_response.results)} emails")
        
    except Exception as error:
        print(f"Failed to send email: {error}")
        if hasattr(error, 'code'):
            print(f"Error code: {error.code}")

# Benefits of Huefy's optimized architecture:
# 1. Security: Enterprise-grade encryption and secure routing
# 2. Performance: Intelligent routing and caching optimizations  
# 3. Reliability: Built-in failover and redundancy systems
# 4. Consistency: Uniform behavior across all SDK languages

if __name__ == "__main__":
    main()