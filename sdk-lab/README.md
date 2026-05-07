# Huefy Python SDK Lab

Verifies the core email contract through the real `HuefyEmailClient` without sending live email.

## Run

```bash
python3 sdk-lab/run.py
```

from `sdks/python/`.

## Scenarios

1. Initialization
2. Single email contract
3. Bulk email contract
4. Validation rejects invalid single recipient
5. Validation rejects invalid bulk request
6. Health check path
7. Cleanup

## Notes

- The lab injects a local stub HTTP client.
- It verifies request shaping, parsed responses, and validation-before-transport behavior.
