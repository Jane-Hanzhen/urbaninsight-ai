from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
DEFAULT_DATABASE_PATH = (BACKEND_DIR / "urban_insight.db").resolve()

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS boroughs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    region TEXT NOT NULL,
    geometry_reference TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS indicators (
    borough_id TEXT PRIMARY KEY,
    gdhi_per_head_gbp REAL NOT NULL,
    business_density_per_1000 REAL NOT NULL,
    house_price_earnings_ratio_reverse REAL NOT NULL,
    police_mean REAL NOT NULL,
    convenient_service_mean REAL NOT NULL,
    cultural_mean REAL NOT NULL,
    medical_mean REAL NOT NULL,
    bus_mean REAL NOT NULL,
    ndvi_mean REAL NOT NULL,
    wet_mean REAL NOT NULL,
    landscape_index REAL NOT NULL,
    household_waste_recycling_rate_pct REAL NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (borough_id) REFERENCES boroughs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS analysis_results (
    borough_id TEXT PRIMARY KEY,
    overall_score REAL,
    regional_rank INTEGER,
    economic_score REAL,
    social_score REAL,
    ecological_score REAL,
    contribution_json TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (borough_id) REFERENCES boroughs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_boroughs_name ON boroughs(name);
"""


def get_database_path() -> Path:
    configured_path = os.getenv("URBANINSIGHT_DB_PATH")
    return resolve_database_path(configured_path) if configured_path else DEFAULT_DATABASE_PATH


def resolve_database_path(database_path: str | Path) -> Path:
    path = Path(database_path).expanduser()
    if path.is_absolute():
        return path.resolve()

    # Accept both "urban_insight.db" and "backend/urban_insight.db" while
    # anchoring them to the project layout instead of the process cwd.
    if path.parts and path.parts[0] == BACKEND_DIR.name:
        return (PROJECT_ROOT / path).resolve()
    return (BACKEND_DIR / path).resolve()


def connect(database_path: Path | None = None) -> sqlite3.Connection:
    path = resolve_database_path(database_path) if database_path else get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def database_connection(database_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    connection = connect(database_path)
    try:
        yield connection
    finally:
        connection.close()


def initialize_database(database_path: Path | None = None) -> Path:
    path = resolve_database_path(database_path) if database_path else get_database_path()
    with database_connection(path) as connection:
        connection.executescript(SCHEMA_SQL)
        connection.commit()
    return path
