from __future__ import annotations

import json
from typing import Any

from .database import database_connection


def list_boroughs() -> list[dict[str, Any]]:
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, region, geometry_reference, created_at
            FROM boroughs
            ORDER BY name
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_borough(borough_id: str) -> dict[str, Any] | None:
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, region, geometry_reference, created_at
            FROM boroughs
            WHERE id = ?
            """,
            (borough_id,),
        ).fetchone()
    return dict(row) if row else None


def get_indicators(borough_id: str) -> dict[str, Any] | None:
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT
                borough_id,
                gdhi_per_head_gbp,
                business_density_per_1000,
                house_price_earnings_ratio_reverse,
                police_mean,
                convenient_service_mean,
                cultural_mean,
                medical_mean,
                bus_mean,
                ndvi_mean,
                wet_mean,
                landscape_index,
                household_waste_recycling_rate_pct,
                updated_at
            FROM indicators
            WHERE borough_id = ?
            """,
            (borough_id,),
        ).fetchone()
    return dict(row) if row else None


def get_analysis_result(borough_id: str) -> dict[str, Any] | None:
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT
                borough_id,
                overall_score,
                regional_rank,
                economic_score,
                social_score,
                ecological_score,
                contribution_json,
                updated_at
            FROM analysis_results
            WHERE borough_id = ?
            """,
            (borough_id,),
        ).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["contribution_json"] = json.loads(result["contribution_json"])
    return result
