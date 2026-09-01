"""sync renders the db; lint catches drift; init is minimal and merge-safe."""

import json
from pathlib import Path

import pytest


@pytest.fixture()
def ws(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    return tmp_path


def test_sync_renders_and_drift_fails(ws, onto_db):
    from montology_gen import lint, sync

    onto_db.add("thread", "a stateful session", kind="core", test="what a session is", pos="noun")
    assert sync().startswith("synced")
    skill = ws / ".claude" / "skills" / "words" / "SKILL.md"
    text = skill.read_text()
    assert "GENERATED" in text and "thread" in text and "monty onto check" in text
    assert lint()[-1].endswith("ok")

    onto_db.add("plan", "a proposal", kind="core", pos="noun")   # the db moves on…
    report = lint()
    assert any("STALE" in r and "monty sync" in r for r in report)  # …the gate bites
    sync()
    assert lint()[-1].endswith("ok")


def test_sync_renders_collisions_and_renames(ws, onto_db):
    from montology_gen import render_words_skill

    onto_db.collide("Artifact", "mellea", "a file out of the sandbox",
                    "WE MOVED — ours became Dossier")
    onto_db.add("output", "what a task produces", kind="core", pos="noun")
    onto_db.rename_word("output", "dossier", "one word for the deliverable")
    text = render_words_skill("t")
    assert "Collisions, ruled on" in text and "WE MOVED" in text
    assert "Renamed — what older material means" in text and "output" in text
    assert "**dossier**" in text


def test_empty_ontology_renders_the_method(ws):
    from montology_gen import render_words_skill

    text = render_words_skill("target")
    assert "No words yet" in text and "monty onto add" in text


def test_init_is_minimal_and_merge_safe(tmp_path, onto_db, monkeypatch, capsys):
    from montology_cli.init import init_command

    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    # the repo already has a CLAUDE.md and an .mcp.json — init must not clobber
    (tmp_path / ".git").mkdir()
    (tmp_path / "CLAUDE.md").write_text("# Their instructions\n\nTheir rules.\n")
    (tmp_path / ".mcp.json").write_text(json.dumps(
        {"mcpServers": {"theirs": {"command": "x"}}}))
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text(json.dumps(
        {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "theirs"}]}]}}))
    monkeypatch.setattr("montology_ontology.db.DB_PATH", tmp_path / ".monty" / "ontology.db")

    init_command(str(tmp_path), yes=True, as_json=True, agents="claude,codex")
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True

    claude_md = (tmp_path / "CLAUDE.md").read_text()
    assert claude_md.startswith("# Their instructions")       # untouched…
    assert "montology:begin" in claude_md                     # …appended
    mcp = json.loads((tmp_path / ".mcp.json").read_text())
    assert "theirs" in mcp["mcpServers"] and "montology" in mcp["mcpServers"]
    assert (tmp_path / ".monty" / "montology.toml").exists()
    assert (tmp_path / ".monty" / "ontology.db").exists()
    assert (tmp_path / "AGENTS.md").exists()                  # codex asked
    assert any("config.toml" in n for n in out["notes"])      # never edits global
    assert (tmp_path / ".claude" / "skills" / "words" / "SKILL.md").exists()

    # the guard hook merged into settings.json, preserving what was there
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    hooks = settings["hooks"]["PreToolUse"]
    assert any("monty guard" in json.dumps(h) for h in hooks)   # ours arrived
    assert any("theirs" in json.dumps(h) for h in hooks)        # theirs survived

    # idempotent: a second run appends nothing twice
    init_command(str(tmp_path), yes=True, as_json=True, agents="claude")
    assert (tmp_path / "CLAUDE.md").read_text().count("montology:begin") == 1


# ── disclosure: the resident page is context every agent pays for ───────────

def _tighten(ws, cap: int) -> None:
    """A workspace that has decided what its always-loaded page is worth."""
    (ws / ".monty" / "montology.toml").write_text(
        f'[gen]\nbody_cap = {cap}\nbody_cap_why = "a test workspace"\n')


def _body(text: str) -> str:
    from montology_gen.instruments import parse_frontmatter

    return parse_frontmatter(text)[1]


def test_the_rendered_page_is_named_by_the_config_not_the_directory(tmp_path):
    """A gate that fires on `mv` teaches people the gate is noise.

    The page carries the workspace's name, and it was read off the directory
    basename — so renaming the checkout, or opening it in a git worktree
    (which names the directory after the branch), made `monty lint` report
    the words skill as HAND-EDITED. That accuses the one file nobody is
    allowed to edit of having been edited, and it found a real user: an
    agent working in a worktree hit it immediately.
    """
    from montology_gen.engine import workspace_name

    ws = tmp_path / "agent-9f3c2a"          # what a worktree directory looks like
    (ws / ".monty").mkdir(parents=True)
    assert workspace_name(ws) == "agent-9f3c2a", "no config: the directory is all there is"

    (ws / ".monty" / "montology.toml").write_text('name = "acme"\n')
    assert workspace_name(ws) == "acme"     # the config outranks the directory

    (ws / ".monty" / "montology.toml").write_text('name = "   "\n')
    assert workspace_name(ws) == "agent-9f3c2a", "a blank name is not a name"


def test_gist_is_the_first_sentence_never_a_new_claim():
    from montology_gen import gist

    assert gist("a run's sandbox. It is network-blocked and dies with the run.") \
        == "a run's sandbox"
    assert gist("a short one") == "a short one"          # nothing to cut
    assert gist("x" * 400).endswith("…") and len(gist("x" * 400)) <= 171


def test_a_column_no_word_fills_is_not_rendered(ws, onto_db):
    """qubie: 0 of 99 words had a code, so `| code |` rendered '—' 99 times."""
    from montology_gen import render_words_skill

    onto_db.add("thread", "a stateful session", kind="core", pos="noun")
    assert "| code |" not in render_words_skill("t")
    onto_db.add("cell", "the box a run executes in", kind="core", code="cell", pos="noun")
    assert "| code |" in render_words_skill("t")


def test_the_ladder_demotes_the_cheapest_thing_first(ws, onto_db):
    """The failure this exists for: qubie, 99 words, 48,703 chars, third raise.

    Adopted words carry their source's prose into a budget sized for this
    repo's own instructions — so they compact, and the retired-name ledger
    (which the guard already enforces at write time) leaves first.
    """
    from montology_gen import render_pages

    onto_db.add("run", "one execution of a task", kind="core", pos="noun")
    onto_db.add("output", "what a task produces", kind="core", pos="noun")
    onto_db.rename_word("output", "dossier", "one word for the deliverable")
    for i in range(30):
        onto_db.add(f"borrowed{i}",
                    f"a term taken from elsewhere. {'Elaboration. ' * 20}",
                    kind="adopted", pos="noun")
    _tighten(ws, 6_000)

    text, pages, demoted = render_pages("t")
    assert len(_body(text)) <= 6_000                      # sync never ships over budget
    assert [d.split(":")[0] for d in demoted][:2] == ["renames", "adopted"]
    assert set(pages) >= {"renamed.md", "adopted.md"}
    assert "a term taken from elsewhere" in text          # the gist stayed resident…
    assert "Elaboration." not in text                     # …the source's prose did not
    assert "Elaboration." in pages["adopted.md"]          # …and is one read away
    assert "references/adopted.md" in text                # the page says where it went


def test_what_left_the_page_is_reported_not_silent(ws, onto_db):
    from montology_gen import lint, sync

    onto_db.add("run", "one execution of a task", kind="core", pos="noun")
    for i in range(30):
        onto_db.add(f"borrowed{i}", f"a taken term. {'More. ' * 20}", kind="adopted", pos="noun")
    _tighten(ws, 6_000)

    assert "reference page" in sync()
    assert any("demoted adopted" in r for r in lint())


def test_reference_pages_are_gated_like_the_skill(ws, onto_db):
    from montology_gen import lint, sync

    onto_db.add("run", "one execution of a task", kind="core", pos="noun")
    for i in range(30):
        onto_db.add(f"borrowed{i}", f"a taken term. {'More. ' * 20}", kind="adopted", pos="noun")
    _tighten(ws, 6_000)
    sync()
    refs = ws / ".claude" / "skills" / "words" / "references"
    assert lint()[-1].endswith("ok")

    (refs / "adopted.md").write_text("my own words")          # hand-edited…
    assert any("HAND-EDITED" in r for r in lint())            # …caught
    sync()

    (refs / "adopted.md").unlink()                            # missing…
    assert any("missing" in r for r in lint())
    sync()

    (refs / "invented.md").write_text("linked from nothing")  # orphaned…
    assert any("linked from nothing" in r for r in lint())
    sync()                                                    # …and swept
    assert not (refs / "invented.md").exists()
    assert lint()[-1].endswith("ok")


def test_a_hand_edited_skill_fails_the_gate(ws, onto_db):
    """CLAUDE.md says hand edits are lost and lint catches them. Now it does."""
    from montology_gen import lint, sync

    onto_db.add("run", "one execution of a task", kind="core", pos="noun")
    sync()
    skill = ws / ".claude" / "skills" / "words" / "SKILL.md"
    skill.write_text(skill.read_text() + "\n## My own section\n")
    assert any("HAND-EDITED" in r and "monty sync" in r for r in lint())
