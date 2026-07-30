from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.database import database_connection, get_database_path, initialize_database


@dataclass(frozen=True)
class IndicatorDefinition:
    column: str
    dimension: str


INDICATORS = (
    IndicatorDefinition("gdhi_per_head_gbp", "Economic"),
    IndicatorDefinition("business_density_per_1000", "Economic"),
    IndicatorDefinition("house_price_earnings_ratio_reverse", "Economic"),
    IndicatorDefinition("police_mean", "Social"),
    IndicatorDefinition("convenient_service_mean", "Social"),
    IndicatorDefinition("cultural_mean", "Social"),
    IndicatorDefinition("medical_mean", "Social"),
    IndicatorDefinition("bus_mean", "Social"),
    IndicatorDefinition("ndvi_mean", "Ecological"),
    IndicatorDefinition("wet_mean", "Ecological"),
    IndicatorDefinition("landscape_index", "Ecological"),
    IndicatorDefinition("household_waste_recycling_rate_pct", "Ecological"),
)
DIMENSIONS = ("Economic", "Social", "Ecological")


@dataclass(frozen=True)
class AnalysisRunSummary:
    borough_count: int
    indicator_count: int
    pca_components: int
    explained_variance: float
    top_borough_id: str
    top_score: float


@dataclass(frozen=True)
class PCAResult:
    components: np.ndarray
    explained_variance_ratio: np.ndarray

    @property
    def component_count(self) -> int:
        return self.components.shape[0]


class AnalysisEngine:
    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path or get_database_path()

    def run(self) -> AnalysisRunSummary:
        initialize_database(self.database_path)
        borough_ids, matrix = self._load_indicator_matrix()
        standardized = self._standardize(matrix)
        pca = self._fit_pca(standardized, explained_variance_threshold=0.85)
        weights = self._derive_pca_weights(pca)

        overall_scores = self._topsis(matrix, weights) * 100
        ranks = self._ordinal_ranks(overall_scores)
        dimension_scores = self._calculate_dimension_scores(matrix, weights)
        contributions = self._calculate_contributions(matrix, weights, pca)

        self._save_results(
            borough_ids,
            overall_scores,
            ranks,
            dimension_scores,
            contributions,
        )

        top_index = int(np.argmax(overall_scores))
        return AnalysisRunSummary(
            borough_count=len(borough_ids),
            indicator_count=len(INDICATORS),
            pca_components=pca.component_count,
            explained_variance=float(np.sum(pca.explained_variance_ratio)),
            top_borough_id=borough_ids[top_index],
            top_score=float(overall_scores[top_index]),
        )

    def _load_indicator_matrix(self) -> tuple[list[str], np.ndarray]:
        columns = ", ".join(definition.column for definition in INDICATORS)
        with database_connection(self.database_path) as connection:
            rows = connection.execute(
                f"SELECT borough_id, {columns} FROM indicators ORDER BY borough_id"
            ).fetchall()

        if len(rows) < 2:
            raise ValueError("Analysis requires indicator rows for at least two boroughs")

        borough_ids = [str(row["borough_id"]) for row in rows]
        matrix = np.asarray(
            [
                [float(row[definition.column]) for definition in INDICATORS]
                for row in rows
            ],
            dtype=float,
        )
        if not np.isfinite(matrix).all():
            raise ValueError("Indicator matrix contains missing or non-finite values")
        if np.any(np.ptp(matrix, axis=0) == 0):
            raise ValueError("Indicator matrix contains a constant indicator column")
        return borough_ids, matrix

    @staticmethod
    def _standardize(matrix: np.ndarray) -> np.ndarray:
        mean = np.mean(matrix, axis=0)
        standard_deviation = np.std(matrix, axis=0)
        if np.any(standard_deviation == 0):
            raise ValueError("Indicator matrix contains a constant indicator column")
        return (matrix - mean) / standard_deviation

    @staticmethod
    def _fit_pca(
        standardized: np.ndarray,
        explained_variance_threshold: float,
    ) -> PCAResult:
        _, singular_values, components = np.linalg.svd(
            standardized,
            full_matrices=False,
        )
        explained_variance = singular_values**2 / (standardized.shape[0] - 1)
        explained_variance_ratio = explained_variance / np.sum(explained_variance)
        component_count = int(
            np.searchsorted(
                np.cumsum(explained_variance_ratio),
                explained_variance_threshold,
            )
            + 1
        )
        return PCAResult(
            components=components[:component_count],
            explained_variance_ratio=explained_variance_ratio[:component_count],
        )

    @staticmethod
    def _derive_pca_weights(pca: PCAResult) -> np.ndarray:
        weighted_loadings = np.abs(pca.components).T @ pca.explained_variance_ratio
        total = float(np.sum(weighted_loadings))
        if total <= 0:
            raise ValueError("PCA did not produce usable indicator weights")
        return weighted_loadings / total

    @staticmethod
    def _min_max_scale(matrix: np.ndarray) -> np.ndarray:
        minimum = np.min(matrix, axis=0)
        spread = np.max(matrix, axis=0) - minimum
        return (matrix - minimum) / spread

    @classmethod
    def _topsis(cls, matrix: np.ndarray, weights: np.ndarray) -> np.ndarray:
        scaled = cls._min_max_scale(matrix)
        norms = np.linalg.norm(scaled, axis=0)
        normalized = np.divide(
            scaled,
            norms,
            out=np.zeros_like(scaled),
            where=norms != 0,
        )
        weighted = normalized * weights
        ideal_best = np.max(weighted, axis=0)
        ideal_worst = np.min(weighted, axis=0)
        distance_best = np.linalg.norm(weighted - ideal_best, axis=1)
        distance_worst = np.linalg.norm(weighted - ideal_worst, axis=1)
        distance_total = distance_best + distance_worst
        return np.divide(
            distance_worst,
            distance_total,
            out=np.zeros_like(distance_worst),
            where=distance_total != 0,
        )

    @staticmethod
    def _ordinal_ranks(scores: np.ndarray) -> np.ndarray:
        order = np.argsort(-scores, kind="stable")
        ranks = np.empty(len(scores), dtype=int)
        ranks[order] = np.arange(1, len(scores) + 1)
        return ranks

    @classmethod
    def _calculate_dimension_scores(
        cls,
        matrix: np.ndarray,
        weights: np.ndarray,
    ) -> dict[str, np.ndarray]:
        scores: dict[str, np.ndarray] = {}
        for dimension in DIMENSIONS:
            indices = [
                index
                for index, definition in enumerate(INDICATORS)
                if definition.dimension == dimension
            ]
            dimension_weights = weights[indices]
            dimension_weights = dimension_weights / np.sum(dimension_weights)
            scores[dimension] = cls._topsis(matrix[:, indices], dimension_weights) * 100
        return scores

    @classmethod
    def _calculate_contributions(
        cls,
        matrix: np.ndarray,
        weights: np.ndarray,
        pca: PCAResult,
    ) -> list[dict[str, object]]:
        weighted_values = cls._min_max_scale(matrix) * weights
        indicator_names = [definition.column for definition in INDICATORS]
        results: list[dict[str, object]] = []

        for row in weighted_values:
            total = float(np.sum(row))
            indicator_percentages = (
                row / total * 100 if total > 0 else weights / np.sum(weights) * 100
            )
            dimensions = {
                dimension: float(
                    np.sum(
                        [
                            indicator_percentages[index]
                            for index, definition in enumerate(INDICATORS)
                            if definition.dimension == dimension
                        ]
                    )
                )
                for dimension in DIMENSIONS
            }
            results.append(
                {
                    "dimensions": dimensions,
                    "indicators": dict(zip(indicator_names, indicator_percentages.tolist())),
                    "weights": dict(zip(indicator_names, weights.tolist())),
                    "pca": {
                        "components": pca.component_count,
                        "explained_variance_ratio": pca.explained_variance_ratio.tolist(),
                        "cumulative_explained_variance": float(
                            np.sum(pca.explained_variance_ratio)
                        ),
                    },
                }
            )
        return results

    def _save_results(
        self,
        borough_ids: list[str],
        overall_scores: np.ndarray,
        ranks: np.ndarray,
        dimension_scores: dict[str, np.ndarray],
        contributions: list[dict[str, object]],
    ) -> None:
        statement = """
        INSERT INTO analysis_results (
            borough_id,
            overall_score,
            regional_rank,
            economic_score,
            social_score,
            ecological_score,
            contribution_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(borough_id) DO UPDATE SET
            overall_score = excluded.overall_score,
            regional_rank = excluded.regional_rank,
            economic_score = excluded.economic_score,
            social_score = excluded.social_score,
            ecological_score = excluded.ecological_score,
            contribution_json = excluded.contribution_json,
            updated_at = CURRENT_TIMESTAMP
        """
        rows = [
            (
                borough_id,
                round(float(overall_scores[index]), 4),
                int(ranks[index]),
                round(float(dimension_scores["Economic"][index]), 4),
                round(float(dimension_scores["Social"][index]), 4),
                round(float(dimension_scores["Ecological"][index]), 4),
                json.dumps(contributions[index], separators=(",", ":")),
            )
            for index, borough_id in enumerate(borough_ids)
        ]

        with database_connection(self.database_path) as connection:
            connection.executemany(statement, rows)
            placeholders = ",".join("?" for _ in borough_ids)
            connection.execute(
                f"DELETE FROM analysis_results WHERE borough_id NOT IN ({placeholders})",
                borough_ids,
            )
            connection.commit()
