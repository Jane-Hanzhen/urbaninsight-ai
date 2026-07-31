from __future__ import annotations

import os
import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.main import LOCAL_CORS_ORIGINS, configured_cors_origins
from scripts.prepare_private_data import decode_private_data


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


class PrivateDataPreparationTests(unittest.TestCase):
    def test_decodes_private_data_and_creates_parent_directory(self) -> None:
        csv_content = b"Region,LAD code\nLondon,E09000001\n"
        encoded_data = base64.b64encode(csv_content).decode("ascii")

        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "data" / "indicators.csv"
            result = decode_private_data(encoded_data, destination)

            self.assertEqual(result, destination.resolve())
            self.assertEqual(destination.read_bytes(), csv_content)

    def test_accepts_wrapped_base64(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "indicators.csv"
            decode_private_data("YQ==\n", destination)

            self.assertEqual(destination.read_bytes(), b"a")

    def test_rejects_invalid_base64_without_creating_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "indicators.csv"

            with self.assertRaisesRegex(ValueError, "not valid Base64"):
                decode_private_data("not-base64!", destination)

            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
