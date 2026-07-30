from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.database import database_connection, initialize_database  # noqa: E402

EXPECTED_COLUMNS = [
    "Region",
    "LAD code",
    "Region name",
    "GDHI per head of population (pounds)",
    "Business Density per 1,000 Population (firms)",
    "Average House Price/Earnings ratio_reverse",
    "police_mean",
    "Convenient_service_mean",
    "cultural_mean",
    "meandical_mean",
    "bus_new_mean",
    "ndvi_mean",
    "wet_mean",
    "landscape_index",
    "Household Waste Recycling Rates (%)",
]

BOROUGH_UPSERT_SQL = """
INSERT INTO boroughs (id, name, region, geometry_reference)
VALUES (?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    name = excluded.name,
    region = excluded.region,
    geometry_reference = excluded.geometry_reference
"""

INDICATOR_UPSERT_SQL = """
INSERT INTO indicators (
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
    household_waste_recycling_rate_pct
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(borough_id) DO UPDATE SET
    gdhi_per_head_gbp = excluded.gdhi_per_head_gbp,
    business_density_per_1000 = excluded.business_density_per_1000,
    house_price_earnings_ratio_reverse = excluded.house_price_earnings_ratio_reverse,
    police_mean = excluded.police_mean,
    convenient_service_mean = excluded.convenient_service_mean,
    cultural_mean = excluded.cultural_mean,
    medical_mean = excluded.medical_mean,
    bus_mean = excluded.bus_mean,
    ndvi_mean = excluded.ndvi_mean,
    wet_mean = excluded.wet_mean,
    landscape_index = excluded.landscape_index,
    household_waste_recycling_rate_pct = excluded.household_waste_recycling_rate_pct,
    updated_at = CURRENT_TIMESTAMP
"""


def parse_numeric(value: str, column: str, row_number: int) -> float:
    cleaned = value.strip().replace(",", "")
    if not cleaned:
        raise ValueError(f"Row {row_number}: {column!r} is empty")
    try:
        return float(cleaned)
    except ValueError as error:
        raise ValueError(
            f"Row {row_number}: {column!r} is not numeric: {value!r}"
        ) from error


def import_csv(csv_path: Path, database_path: Path) -> int:
    initialize_database(database_path)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(
                "CSV columns do not match the inspected London indicator schema.\n"
                f"Expected: {EXPECTED_COLUMNS}\n"
                f"Received: {reader.fieldnames}"
            )
        rows = list(reader)

    seen_ids: set[str] = set()
    with database_connection(database_path) as connection:
        for row_number, row in enumerate(rows, start=2):
            borough_id = row["LAD code"].strip()
            borough_name = row["Region name"].strip()
            region = row["Region"].strip()
            if not borough_id or not borough_name or not region:
                raise ValueError(f"Row {row_number}: borough identity fields cannot be empty")
            if borough_id in seen_ids:
                raise ValueError(f"Row {row_number}: duplicate LAD code {borough_id}")
            seen_ids.add(borough_id)

            geometry_reference = f"/data/london_boroughs.geojson#{borough_name}"
            connection.execute(
                BOROUGH_UPSERT_SQL,
                (borough_id, borough_name, region, geometry_reference),
            )
            connection.execute(
                INDICATOR_UPSERT_SQL,
                (
                    borough_id,
                    parse_numeric(row["GDHI per head of population (pounds)"], "GDHI", row_number),
                    parse_numeric(row["Business Density per 1,000 Population (firms)"], "Business Density", row_number),
                    parse_numeric(row["Average House Price/Earnings ratio_reverse"], "House Price/Earnings ratio_reverse", row_number),
                    parse_numeric(row["police_mean"], "police_mean", row_number),
                    parse_numeric(row["Convenient_service_mean"], "Convenient_service_mean", row_number),
                    parse_numeric(row["cultural_mean"], "cultural_mean", row_number),
                    parse_numeric(row["meandical_mean"], "meandical_mean", row_number),
                    parse_numeric(row["bus_new_mean"], "bus_new_mean", row_number),
                    parse_numeric(row["ndvi_mean"], "ndvi_mean", row_number),
                    parse_numeric(row["wet_mean"], "wet_mean", row_number),
                    parse_numeric(row["landscape_index"], "landscape_index", row_number),
                    parse_numeric(row["Household Waste Recycling Rates (%)"], "Recycling Rate", row_number),
                ),
            )
        connection.commit()

    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import London indicators into SQLite")
    parser.add_argument(
        "--csv",
        type=Path,
        default=PROJECT_DIR / "data" / "london_indicators.csv",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=BACKEND_DIR / "urban_insight.db",
    )
    arguments = parser.parse_args()
    imported_count = import_csv(arguments.csv.resolve(), arguments.database.resolve())
    print(f"Imported {imported_count} borough indicator rows into {arguments.database.resolve()}")


if __name__ == "__main__":
    main()
