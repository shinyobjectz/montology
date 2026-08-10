"""montology-warehouse: DuckDB as the standard analytical engine.

THE DIVISION OF LABOR IS DELIBERATE. SQLite remains the system of record
for the registries (ontology.db, zoo.db) — tiny, transactional, readable by
anything. DuckDB is where ANALYSIS happens: campaign exports, ad-platform
CSVs, scraped corpora, Parquet from anywhere — full SQL, columnar speed,
zero server, on the user's laptop. `connect()` attaches the registries
read-only through DuckDB's sqlite extension, so one query can join a
campaign table against the IAB taxonomy and the model shelf.

Real infrastructure, marketer-shaped: files go in, SQL comes out, and
nothing needs a server or an account.
"""

from .db import connect, load_file, query, warehouse_path

__all__ = ["connect", "load_file", "query", "warehouse_path"]
