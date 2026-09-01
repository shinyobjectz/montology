"""What a workspace is tuned to — readable, changeable, and refusable.

The knobs existed and nothing could name them: to move the gate from
advisory to enforced you opened the TOML and guessed a key. These cases
are the two failures that made that dangerous — a setting written into
the wrong place, and a value accepted that means nothing — plus the one
thing a naive writer destroys: the comments montology wrote to explain
the very keys it is setting.
"""

import pytest

TEMPLATE = """\
name = "app"
created = "2026-09-01"

[guard]
# the firewall (agent pre-write hook): block | warn | off
names  = "block"   # retired words ALWAYS block; collisions follow [scan]
design = "block"   # rogue values vs tokens — only fires when tokens exist

[scan]
# which word kinds a code declaration may NOT be named after
enforced_kinds = ["core", "inner"]
allow = []
"""


@pytest.fixture()
def root(tmp_path):
    (tmp_path / ".monty").mkdir()
    (tmp_path / ".monty" / "montology.toml").write_text(TEMPLATE)
    return tmp_path


def _toml(root):
    return (root / ".monty" / "montology.toml").read_text()


def test_every_setting_reports_its_value_and_where_it_came_from(root):
    from montology_core import settings as cfg

    by_name = {r["name"]: r for r in cfg.effective(root)}
    assert by_name["guard.names"]["value"] == "block"
    assert by_name["guard.names"]["source"] == "montology.toml"
    # never set, so the default — and SAID to be the default, because
    # "block" read off a file and "block" read off nothing are different
    # facts when you are deciding whether to change it
    assert by_name["scan.collisions"]["value"] == "advisory"
    assert by_name["scan.collisions"]["source"] == "default"
    assert all(r["effect"] for r in by_name.values())


def test_setting_a_key_that_exists_replaces_it_in_place(root):
    from montology_core import settings as cfg

    cfg.write(root, "guard.names", "warn")
    text = _toml(root)
    assert 'names = "warn"' in text
    assert 'names  = "block"' not in text
    assert text.count("[guard]") == 1


def test_the_comments_survive_the_write(root):
    """A writer that round-tripped the TOML would delete the sentence
    explaining the key it just set. The config is half comment on purpose."""
    from montology_core import settings as cfg

    cfg.write(root, "guard.design", "off")
    text = _toml(root)
    assert "# the firewall (agent pre-write hook): block | warn | off" in text
    assert "# which word kinds a code declaration may NOT be named after" in text


def test_a_key_not_yet_present_lands_in_its_own_section(root):
    from montology_core import settings as cfg

    cfg.write(root, "scan.collisions", "enforce")
    text = _toml(root)
    before, scan = text.split("[scan]", 1)
    assert 'collisions = "enforce"' in scan
    assert 'collisions =' not in before   # not dropped into [guard] above it


def test_a_section_that_does_not_exist_is_appended(root):
    from montology_core import settings as cfg

    cfg.write(root, "design.enforce", "true")
    text = _toml(root)
    assert "[design]" in text and "enforce = true" in text


def test_a_commented_out_key_is_documentation_not_a_setting(tmp_path):
    """`# names = "warn"` is an example someone wrote to explain the key.
    Overwriting it would silently delete the explanation and leave the real
    setting unset."""
    from montology_core import settings as cfg

    (tmp_path / ".monty").mkdir()
    (tmp_path / ".monty" / "montology.toml").write_text(
        '[guard]\n# names = "warn"   # what this looks like\n')
    cfg.write(tmp_path, "guard.names", "off")
    text = (tmp_path / ".monty" / "montology.toml").read_text()
    assert '# names = "warn"   # what this looks like' in text
    assert 'names = "off"' in text


def test_a_bad_value_is_refused_with_the_allowed_set(root):
    from montology_core import settings as cfg

    with pytest.raises(ValueError) as e:
        cfg.write(root, "guard.names", "loud")
    assert "block | warn | off" in str(e.value)
    assert _toml(root) == TEMPLATE, "a refusal must not have written anything"


def test_an_unknown_key_is_refused_with_the_real_ones(root):
    from montology_core import settings as cfg

    with pytest.raises(KeyError) as e:
        cfg.write(root, "guard.loudness", "11")
    assert "scan.collisions" in e.value.args[0]


def test_lists_and_booleans_round_trip_as_toml(root):
    from montology_core import settings as cfg

    cfg.write(root, "scan.exclude", "vendor/**, **/*.generated.ts")
    cfg.write(root, "design.enforce", "yes")
    by_name = {r["name"]: r for r in cfg.effective(root)}
    assert by_name["scan.exclude"]["value"] == ["vendor/**", "**/*.generated.ts"]
    assert by_name["design.enforce"]["value"] is True


def test_a_kind_that_is_not_a_kind_is_refused(root):
    from montology_core import settings as cfg

    with pytest.raises(ValueError) as e:
        cfg.write(root, "scan.enforced_kinds", "core,inner,invented")
    assert "invented" in str(e.value)


def test_what_the_writer_sets_is_what_the_scan_reads(root):
    """The whole point of the schema: a key the writer invents that the
    engines never read is a setting that silently does nothing."""
    from montology_core import settings as cfg
    from montology_scan.surface import _scan_config

    cfg.write(root, "scan.exclude", "vendor/**")
    cfg.write(root, "scan.collisions", "enforce")
    got = _scan_config(root)
    assert got["exclude"] == ["vendor/**"]
    assert got["collisions"] == "enforce"


def test_a_missing_config_is_the_defaults_and_a_write_says_so(tmp_path):
    from montology_core import settings as cfg

    (tmp_path / ".monty").mkdir()
    assert cfg.read(tmp_path) == {}
    assert {r["source"] for r in cfg.effective(tmp_path)} == {"default"}
    with pytest.raises(FileNotFoundError) as e:
        cfg.write(tmp_path, "guard.names", "off")
    assert "monty init" in str(e.value)
