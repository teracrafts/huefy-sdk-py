"""Package-level export regression tests."""

from __future__ import annotations

import importlib

from huefy.types import BulkEmailResult


def test_import_huefy_package_exports_public_symbols() -> None:
    package = importlib.import_module("huefy")

    assert package.HuefyClient is not None
    assert package.HuefyEmailClient is not None
    assert package.HuefyConfig is not None
    assert package.BulkEmailResult is BulkEmailResult


def test_bulk_email_result_backfills_success_from_status() -> None:
    result = BulkEmailResult.from_dict(
        {
            "email": "user@example.com",
            "status": "sent",
        }
    )

    assert result.email == "user@example.com"
    assert result.success is True
    assert result.error is None
