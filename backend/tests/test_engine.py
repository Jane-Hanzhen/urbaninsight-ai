from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import numpy as np

from analysis import AnalysisEngine
from app.database import database_connection, initialize_database


class AnalysisEngineTests(unittest.TestCase):
    def test_standardization_centers_and_scales_columns(self) -> None:
        matrix = np.asarray([[1.0, 20.0], [2.0, 30.0], [3.0, 40.0]])
        standardized = AnalysisEngine._standardize(matrix)
        np.testing.assert_allclose(np.mean(standardized, axis=0), [0.0, 0.0], atol=1e-12)
        np.testing.assert_allclose(np.std(standardized, axis=0), [1.0, 1.0])

    def test_topsis_prefers_the_stronger_benefit_alternative(self) -> None:
        matrix = np.asarray([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])
        scores = AnalysisEngine._topsis(matrix, np.asarray([0.5, 0.5]))
        self.assertLess(scores[0], scores[1])
        self.assertLess(scores[1], scores[2])

    def test_full_run_persists_ranked_results_and_contributions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "analysis.db"
            initialize_database(database_path)
            with database_connection(database_path) as connection:
                for index in range(1, 5):
                    borough_id = f"B{index}"
                    connection.execute(
                        "INSERT INTO boroughs (id, name, region) VALUES (?, ?, 'London')",
                        (borough_id, f"Borough {index}"),
                    )
                    values = [float(index * factor + factor % 3) for factor in range(1, 13)]
                    connection.execute(
                        """
                        INSERT INTO indicators VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
                        )
                        """,
                        (borough_id, *values),
                    )
                connection.commit()

            summary = AnalysisEngine(database_path).run()
            self.assertEqual(summary.borough_count, 4)

            connection = sqlite3.connect(database_path)
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT * FROM analysis_results ORDER BY regional_rank"
            ).fetchall()
            connection.close()

            self.assertEqual(len(rows), 4)
            self.assertEqual([row["regional_rank"] for row in rows], [1, 2, 3, 4])
            for row in rows:
                contribution = json.loads(row["contribution_json"])
                self.assertAlmostEqual(sum(contribution["dimensions"].values()), 100)


if __name__ == "__main__":
    unittest.main()
