from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.main import LOCAL_CORS_ORIGINS, configured_cors_origins


class CORSConfigurationTests(unittest.TestCase):
    def test_local_origins_are_enabled_by_default(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(configured_cors_origins(), list(LOCAL_CORS_ORIGINS))

    def test_production_origins_are_added_and_deduplicated(self) -> None:
        with patch.dict(
            os.environ,
            {
                "BACKEND_CORS_ORIGINS": (
                    "https://urbaninsight-ai.vercel.app/, "
                    "https://preview.example.com, "
                    "https://urbaninsight-ai.vercel.app"
                )
            },
            clear=True,
        ):
            origins = configured_cors_origins()

        self.assertEqual(
            origins,
            [
                *LOCAL_CORS_ORIGINS,
                "https://urbaninsight-ai.vercel.app",
                "https://preview.example.com",
            ],
        )

    def test_wildcard_origin_is_rejected(self) -> None:
        with patch.dict(
            os.environ, {"BACKEND_CORS_ORIGINS": "*"}, clear=True
        ):
            with self.assertRaisesRegex(ValueError, "must not contain"):
                configured_cors_origins()

    def test_origin_with_path_is_rejected(self) -> None:
        with patch.dict(
            os.environ,
            {"BACKEND_CORS_ORIGINS": "https://example.com/api"},
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "without paths"):
                configured_cors_origins()


if __name__ == "__main__":
    unittest.main()
