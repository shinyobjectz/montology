"""montology-ontology: a repo's vocabulary as a queryable database."""

from .db import (add, check, connect, db_path, doctrines, overloads,
                 record_run, rule, words)
from .seed import seed

__all__ = ["add", "check", "connect", "db_path", "doctrines", "overloads",
           "record_run", "rule", "seed", "words"]
