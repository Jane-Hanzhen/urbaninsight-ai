from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from app.database import BACKEND_DIR, get_database_path, resolve_database_path


class DatabasePathTests(unittest.TestCase):
    def test_default_path_is_backend_database(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_database_path(), BACKEND_DIR / "urban_insight.db")

    def test_relative_path_is_independent_of_working_directory(self) -> None:
        expected = BACKEND_DIR / "urban_insight.db"
        for working_directory in (BACKEND_DIR, BACKEND_DIR.parent):
            with self.subTest(working_directory=working_directory):
                with patch.dict(os.environ, {"URBANINSIGHT_DB_PATH": "urban_insight.db"}):
                    with patch("pathlib.Path.cwd", return_value=working_directory):
                        self.assertEqual(get_database_path(), expected)

    def test_root_style_backend_path_does_not_duplicate_backend_segment(self) -> None:
        self.assertEqual(
            resolve_database_path(Path("backend") / "urban_insight.db"),
            BACKEND_DIR / "urban_insight.db",
        )


if __name__ == "__main__":
    unittest.main()
