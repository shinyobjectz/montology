"""montology-ontology: a repo's vocabulary as a queryable database."""

from .db import (add, check, collide, collisions, connect, db_path, doctrines,
                 overloads, record_run, rename_word, renames, rule, token_add,
                 tokens, words)
from .seed import seed

__all__ = ["add", "check", "collide", "collisions", "connect", "db_path",
           "doctrines", "overloads", "record_run", "rename_word", "renames",
           "rule", "seed", "token_add", "tokens", "words"]
