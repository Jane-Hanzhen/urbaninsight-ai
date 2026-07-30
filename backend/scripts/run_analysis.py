from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from analysis import AnalysisEngine  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PCA-weighted TOPSIS analysis")
    parser.add_argument(
        "--database",
        type=Path,
        default=BACKEND_DIR / "urban_insight.db",
    )
    arguments = parser.parse_args()
    summary = AnalysisEngine(arguments.database.resolve()).run()
    print(
        "Analyzed "
        f"{summary.borough_count} boroughs across {summary.indicator_count} indicators; "
        f"PCA retained {summary.pca_components} components "
        f"({summary.explained_variance:.2%} explained variance). "
        f"Top borough: {summary.top_borough_id} ({summary.top_score:.2f})."
    )


if __name__ == "__main__":
    main()
