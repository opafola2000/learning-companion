"""Lightweight SQLite column migrations for existing databases."""

from sqlalchemy import inspect, text


MIGRATIONS: dict[str, list[tuple[str, str]]] = {
    "curricula": [
        ("blueprint_version", "VARCHAR"),
        ("exam_code", "VARCHAR"),
        ("validation_status", "VARCHAR DEFAULT 'pending'"),
        ("sources", "JSON"),
        ("objectives", "JSON"),
        ("is_stale", "VARCHAR DEFAULT 'false'"),
    ],
    "topics": [
        ("objective_ids", "JSON"),
        ("source_urls", "JSON"),
        ("validation_status", "VARCHAR DEFAULT 'pending'"),
    ],
    "resources": [
        ("source_domain", "VARCHAR"),
        ("trust_tier", "VARCHAR DEFAULT 'unknown'"),
        ("citation_snippet", "TEXT"),
    ],
    "quizzes": [
        ("blueprint_version", "VARCHAR"),
        ("exam_code", "VARCHAR"),
        ("validation_status", "VARCHAR DEFAULT 'pending'"),
        ("is_stale", "VARCHAR DEFAULT 'false'"),
    ],
    "questions": [
        ("objective_id", "VARCHAR"),
        ("source_reference", "VARCHAR"),
        ("citation_snippet", "TEXT"),
    ],
    "topic_masteries": [
        ("next_review_at", "DATETIME"),
        ("ease_factor", "FLOAT DEFAULT 2.5"),
        ("interval_days", "INTEGER DEFAULT 1"),
    ],
}


def run_migrations(engine) -> None:
    if engine.dialect.name != "sqlite":
        return
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, columns in MIGRATIONS.items():
            if table not in existing_tables:
                continue
            existing_cols = {col["name"] for col in inspector.get_columns(table)}
            for col_name, col_type in columns:
                if col_name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
