"""montology-ontology: a repo's vocabulary as a queryable database."""

from .db import (POS, RIGIDITY, TREE_WIDE, add, amend, amendments, check,
                 collide, collisions, connect, db_path, doctrines, except_add,
                 except_drop, exceptions, genera, genus_add, genus_chain,
                 genus_drop, inherited, overloads, record_run, rename_word,
                 renames, rigidity_set, route_add, route_drafts, route_drop,
                 routes, rule, token_add, tokens, words)
from .proposals import (changes, close as close_proposal, decide, merge,
                        preview, proposals, propose)
from .questions import answer, ask, coverage, harvest, questions
from .relations import drafts as relation_drafts_from_code
from .relations import relate, relations, render_drafts, unrelate
from .intents import apply as apply_intent
from .intents import catalogue as intent_catalogue
from .chains import analyse as route_analyse
from .chains import render as render_routes
from .seed import seed
from .semantics import audit as semantic_audit
from .semantics import near_pairs
from .semantics import similar as semantic_similar
from .ingest import (INGESTERS, ingest as ingest_source, ingested,
                     source_citation)
from .sources import (SOURCES, by_group as sources_by_group,
                      groups as source_groups, render as render_sources)
# tier 2, aliased apart from tier 1 on purpose: `harvest` already belongs to
# the questions in this namespace, and `search_index` sitting beside
# `render_sources` is the tier split showing up where a caller has to choose.
from .index import (Harvest, IndexEntry, harvest as harvest_index,
                    render_harvest, render_search,
                    search as search_index)
from .upstream import pinned_upstream, pull

__all__ = ["POS", "RIGIDITY", "TREE_WIDE", "add", "answer", "apply_intent", "ask", "relate", "relations", "unrelate",
           "relation_drafts_from_code", "render_drafts", "changes", "coverage", "harvest", "questions", "close_proposal", "decide", "intent_catalogue",
           "merge", "preview", "proposals", "propose", "amend", "amendments", "check", "collide", "collisions", "connect", "db_path",
           "doctrines", "except_add", "except_drop", "exceptions", "genera", "genus_add", "genus_chain",
           "genus_drop", "inherited", "rigidity_set",
           "overloads", "record_run", "rename_word", "renames",
           "INGESTERS", "ingest_source", "ingested", "source_citation",
           "pinned_upstream", "pull", "route_analyse", "render_routes", "route_add", "route_drafts", "route_drop", "routes", "rule", "seed", "near_pairs", "semantic_audit", "semantic_similar", "SOURCES", "sources_by_group", "source_groups", "render_sources", "Harvest", "IndexEntry", "harvest_index", "render_harvest", "render_search", "search_index", "token_add", "tokens", "words"]
