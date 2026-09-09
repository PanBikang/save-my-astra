from __future__ import annotations

import os
import subprocess
import tomllib
from pathlib import Path

import pytest

from eval.profiles import load_profile
from eval.render import render_template


ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "scripts" / "install.sh"
BEGIN = "<!-- save-my-astra:begin -->"
END = "<!-- save-my-astra:end -->"


def _run_install(home: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the real installer with an isolated home and no model/network calls."""
    env = os.environ.copy()
    env.pop("CODEX_HOME", None)
    result = subprocess.run(
        [str(INSTALL), "--codex-home", str(home), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def _upstream_agents(profile_name: str = "astra-luna") -> str:
    """Representative unmarked upstream block, independent of Git history."""
    profile = load_profile(profile_name)
    return (
        "# Codex orchestration\n\n"
        f"Root: {profile.parent_model}. Child: {profile.subagent_model}.\n"
        "Child tasks use fork_turns: none.\n\n"
        "### Workers take\n\n"
        "- Narrow edits with an explicit file list\n"
        "- Tests, formatting, refactors in a bounded path\n\n"
        "## Writing\n\n"
        "Lead with the result. Use short paragraphs. Use lists only for parallel items. No filler closings.\n"
    )


def _expected_agents() -> str:
    return render_template("AGENTS.md", load_profile("astra-luna")).strip("\n")


def _managed_body(text: str) -> str:
    assert text.count(BEGIN) == 1
    assert text.count(END) == 1
    start = text.index(BEGIN) + len(BEGIN)
    end = text.index(END, start)
    return text[start:end].strip("\n")


def _without_managed_block(text: str) -> str:
    start = text.index(BEGIN)
    end = text.index(END, start) + len(END)
    return text[:start] + text[end:]


def test_fresh_install_writes_default_astra_luna_home(tmp_path: Path):
    home = tmp_path / "codex"

    _run_install(home)

    config = tomllib.loads((home / "config.toml").read_text())
    assert config["model"] == "gpt-6-astra"
    assert config["model_reasoning_effort"] == "low"
    assert config["agents"]["enabled"] is True
    assert config["agents"]["default_subagent_model"] == "gpt-5.6-luna"
    assert config["agents"]["default_subagent_reasoning_effort"] == "max"
    assert config["features"]["multi_agent_v2"]["hide_spawn_agent_metadata"] is False

    agents = (home / "AGENTS.md").read_text()
    assert _managed_body(agents) == _expected_agents()

    worker = home / "agents" / "luna-max-worker.toml"
    worker_config = tomllib.loads(worker.read_text())
    assert worker_config["model"] == "gpt-5.6-luna"
    assert worker_config["model_reasoning_effort"] == "max"

    skill = home / "skills" / "save-my-astra" / "SKILL.md"
    assert skill.exists()
    assert "default_subagent_model" in skill.read_text()


def test_dry_run_previews_without_writing(tmp_path: Path):
    home = tmp_path / "codex"
    home.mkdir()
    config = home / "config.toml"
    config.write_text('model_provider = "keep-provider"\n')
    before = config.read_bytes()

    result = _run_install(home, "--dry-run")

    assert "profile: astra-luna" in result.stdout
    assert "gpt-6-astra" in result.stdout
    assert config.read_bytes() == before
    assert not (home / "AGENTS.md").exists()
    assert not (home / "agents").exists()
    assert not (home / "skills").exists()
    assert not (home / "backups").exists()


@pytest.mark.parametrize("heading", ["# User preferences", "## User preferences"])
def test_upgrade_replaces_exact_legacy_template_and_keeps_preferences(
    tmp_path: Path, heading: str
):
    home = tmp_path / "codex"
    home.mkdir()
    legacy = _upstream_agents() + f"\n{heading}\nKeep this local preference.\n"
    (home / "AGENTS.md").write_text(legacy)

    _run_install(home)

    agents = (home / "AGENTS.md").read_text()
    assert agents.startswith(BEGIN)
    assert _managed_body(agents) == _expected_agents()
    assert "- Narrow edits with an explicit file list" not in agents
    outside = _without_managed_block(agents)
    assert outside.count(heading) == 1
    assert outside.count("Keep this local preference.") == 1
    assert "{{PARENT_MODEL}}" not in agents


def test_custom_agents_are_retained_when_markers_are_added(tmp_path: Path):
    home = tmp_path / "codex"
    home.mkdir()
    custom = (
        "# Local project policy\n"
        "Use the repository's pinned formatter.\n\n"
        "## Operator notes\n"
        "Keep this section during upgrades.\n"
    )
    (home / "AGENTS.md").write_text(custom)

    _run_install(home)

    agents = (home / "AGENTS.md").read_text()
    assert _managed_body(agents) == _expected_agents()
    outside = _without_managed_block(agents)
    assert "# Local project policy" in outside
    assert "Use the repository's pinned formatter." in outside
    assert "## Operator notes" in outside
    assert "Keep this section during upgrades." in outside


def test_repeated_install_is_idempotent_and_does_not_duplicate_managed_block(
    tmp_path: Path,
):
    home = tmp_path / "codex"
    home.mkdir()
    (home / "AGENTS.md").write_text("# Local instructions\nKeep this line.\n")

    _run_install(home)
    tracked = [
        home / "AGENTS.md",
        home / "config.toml",
        home / "agents" / "luna-max-worker.toml",
        home / "skills" / "save-my-astra" / "SKILL.md",
    ]
    first = {path: path.read_bytes() for path in tracked}

    _run_install(home)

    assert {path: path.read_bytes() for path in tracked} == first
    agents = (home / "AGENTS.md").read_text()
    assert agents.count(BEGIN) == 1
    assert agents.count(END) == 1
    assert agents.count("# Local instructions") == 1
    assert agents.count("Keep this line.") == 1


def test_install_preserves_unrelated_config_and_agent_settings(tmp_path: Path):
    home = tmp_path / "codex"
    home.mkdir()
    (home / "config.toml").write_text(
        'model_provider = "keep-provider"\n'
        'model = "old-parent"\n'
        'model_reasoning_effort = "high"\n'
        'notify = ["/bin/true", "turn-ended"]\n'
        'plugins = ["keep-plugin"]\n\n'
        "[agents]\n"
        "enabled = false\n"
        "max_depth = 7\n"
        "max_threads = 3\n"
        'interrupt_message = "keep this message"\n\n'
        "[mcp_servers.keep_server]\n"
        'url = "https://example.invalid/mcp"\n'
        '\n[profiles.custom]\nmodel = "keep-custom-model"\n'
        'model_reasoning_effort = "high"\n'
        '\n[features.multi_agent_v2]\n# Keep this setting\nother_setting = true\n'
    )

    _run_install(home)

    config = tomllib.loads((home / "config.toml").read_text())
    assert config["model_provider"] == "keep-provider"
    assert config["notify"] == ["/bin/true", "turn-ended"]
    assert config["plugins"] == ["keep-plugin"]
    assert config["mcp_servers"]["keep_server"]["url"] == "https://example.invalid/mcp"
    assert config["agents"]["enabled"] is True
    assert config["agents"]["max_depth"] == 7
    assert config["agents"]["max_threads"] == 3
    assert config["agents"]["interrupt_message"] == "keep this message"
    assert config["profiles"]["custom"]["model"] == "keep-custom-model"
    assert config["profiles"]["custom"]["model_reasoning_effort"] == "high"
    assert config["features"]["multi_agent_v2"]["other_setting"] is True
    assert "# Keep this setting" in (home / "config.toml").read_text()


def test_rapid_reinstalls_create_complete_unique_backups(tmp_path: Path):
    home = tmp_path / "codex"
    (home / "agents").mkdir(parents=True)
    (home / "skills" / "save-my-astra").mkdir(parents=True)
    original = {
        Path("config.toml"): 'model_provider = "before"\n',
        Path("AGENTS.md"): "# Existing instructions\n",
        Path("agents/luna-max-worker.toml"): 'model = "old-worker"\n',
        Path("skills/save-my-astra/SKILL.md"): "old skill\n",
    }
    for relative, content in original.items():
        path = home / relative
        path.write_text(content)

    _run_install(home)
    _run_install(home)

    backups = sorted(path for path in (home / "backups").iterdir() if path.is_dir())
    assert len(backups) == 2
    assert len({path.name for path in backups}) == 2
    expected_paths = set(original)
    for backup in backups:
        assert expected_paths <= {
            path.relative_to(backup)
            for path in backup.rglob("*")
            if path.is_file()
        }
    assert any(
        all((backup / relative).read_text() == content for relative, content in original.items())
        for backup in backups
    )


@pytest.mark.parametrize(
    ("filename", "invalid"),
    [
        ("config.toml", "[broken\n"),
        ("AGENTS.md", BEGIN + "\nmissing end\n"),
        ("AGENTS.md", END + "\n" + BEGIN),
        ("AGENTS.md", BEGIN + END + BEGIN + END),
    ],
)
def test_invalid_input_fails_before_any_target_write(tmp_path: Path, filename: str, invalid: str):
    home = tmp_path / "codex"
    home.mkdir()
    target = home / filename
    target.write_text(invalid)
    result = subprocess.run(
        [str(INSTALL), "--codex-home", str(home)], cwd=ROOT, text=True, capture_output=True
    )
    assert result.returncode != 0
    assert target.read_text() == invalid
    assert list(home.iterdir()) == [target]


def test_upgrade_marked_policy_preserves_both_surrounding_sections(tmp_path: Path):
    home = tmp_path / "codex"
    home.mkdir()
    prefix = "# Local preference\nKeep the first section.\n\n"
    suffix = "\n\n## More rules\nKeep the last section.\n"
    (home / "AGENTS.md").write_text(prefix + BEGIN + "\nold rules\n" + END + suffix)
    _run_install(home)
    actual = (home / "AGENTS.md").read_text()
    assert actual == prefix + BEGIN + "\n" + _expected_agents() + "\n" + END + suffix
