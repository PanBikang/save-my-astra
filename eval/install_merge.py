from __future__ import annotations

import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import tomlkit

from eval.paths import SKILL_FILE, SKILL_NAME
from eval.profiles import load_profile
from eval.render import render_template

MANAGED_BEGIN = "<!-- save-my-astra:begin -->"
MANAGED_END = "<!-- save-my-astra:end -->"


def merge_snippet(existing: str, profile_name: str) -> str:
    profile = load_profile(profile_name)
    data = tomlkit.parse(existing)
    data["model"] = profile.parent_model
    data["model_reasoning_effort"] = profile.parent_effort
    agents = data.setdefault("agents", tomlkit.table())
    # Repair the upstream installer's misplaced root options without discarding agent settings.
    for key in ("notify", "model_provider"):
        if key in agents:
            data.setdefault(key, agents.pop(key))
    agents["enabled"] = profile.agents_enabled
    agents["default_subagent_model"] = profile.subagent_model
    agents["default_subagent_reasoning_effort"] = profile.subagent_effort
    agents.setdefault("max_concurrent_threads_per_session", 4)
    features = data.setdefault("features", tomlkit.table())
    features.setdefault("multi_agent_v2", tomlkit.table())["hide_spawn_agent_metadata"] = False
    text = tomlkit.dumps(data)
    return text if text.endswith("\n") else text + "\n"


def merge_agents(existing: str, profile_name: str) -> str:
    content = render_template("AGENTS.md", load_profile(profile_name)).rstrip()
    block = f"{MANAGED_BEGIN}\n{content}\n{MANAGED_END}"
    if MANAGED_BEGIN in existing or MANAGED_END in existing:
        if existing.count(MANAGED_BEGIN) != 1 or existing.count(MANAGED_END) != 1:
            raise ValueError("AGENTS.md has incomplete or duplicate Save My Astra markers")
        start = existing.index(MANAGED_BEGIN)
        end = existing.index(MANAGED_END)
        if end < start:
            raise ValueError("AGENTS.md has reversed Save My Astra markers")
        return existing[:start] + block + existing[end + len(MANAGED_END):]

    # The upstream installer wrote an unmarked document. Replace only its known span.
    legacy_start = existing.find("# Codex orchestration\n")
    legacy_end_text = "Lead with the result. Use short paragraphs. Use lists only for parallel items. No filler closings."
    if legacy_start >= 0:
        legacy_end = existing.find(legacy_end_text, legacy_start)
        if legacy_end < 0:
            raise ValueError("Unrecognized legacy Codex orchestration block; no files were changed")
        legacy_end += len(legacy_end_text)
        legacy = existing[legacy_start:legacy_end]
        if "### Workers take" not in legacy or "fork_turns: none" not in legacy:
            raise ValueError("Unrecognized legacy Codex orchestration block; no files were changed")
        return existing[:legacy_start] + block + existing[legacy_end:]
    separator = "\n\n" if existing and not existing.endswith("\n") else "\n" if existing else ""
    return existing + separator + block + "\n"


def worker_filename(profile_name: str) -> str:
    profile = load_profile(profile_name)
    return f"{profile.subagent_name.replace('_', '-')}.toml"


def install_files(codex_home: Path, profile_name: str) -> dict[Path, str]:
    profile = load_profile(profile_name)
    config = codex_home / "config.toml"
    existing = config.read_text() if config.exists() else ""
    agents = codex_home / "AGENTS.md"
    existing_agents = agents.read_text() if agents.exists() else ""
    return {
        Path("config.toml"): merge_snippet(existing, profile_name),
        Path("AGENTS.md"): merge_agents(existing_agents, profile_name),
        Path("agents") / worker_filename(profile_name): render_template("agents/worker.toml", profile),
        Path("skills") / SKILL_NAME / "SKILL.md": SKILL_FILE.read_text(),
    }


def write_install(codex_home: Path, profile_name: str) -> Path:
    files = install_files(codex_home, profile_name)
    backup_root = codex_home / "backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = Path(tempfile.mkdtemp(prefix=f"save-my-astra-{stamp}-", dir=backup_root))
    for relative in files:
        source = codex_home / relative
        if source.exists():
            target = backup / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for relative, content in files.items():
        target = codex_home / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    return backup


def verify_install(codex_home: Path, profile_name: str) -> tuple[list[str], dict[str, str]]:
    """Check a CODEX_HOME after install. Empty error list means OK."""
    import tomllib

    profile = load_profile(profile_name)
    errors: list[str] = []
    config_path = codex_home / "config.toml"
    worker_path = codex_home / "agents" / worker_filename(profile_name)
    summary = {
        "profile": profile.name,
        "parent": f"{profile.parent_model} / {profile.parent_effort}",
        "child": f"{profile.subagent_model} / {profile.subagent_effort}",
        "worker": worker_path.name,
        "agents_enabled": str(profile.agents_enabled).lower(),
        "hide_spawn_agent_metadata": "false",
    }
    if not config_path.exists():
        return [f"missing {config_path}"], summary
    data = tomllib.loads(config_path.read_text())
    if data.get("model") != profile.parent_model:
        errors.append(f"config model is {data.get('model')!r}, want {profile.parent_model!r}")
    if data.get("model_reasoning_effort") != profile.parent_effort:
        errors.append(
            "config model_reasoning_effort is "
            f"{data.get('model_reasoning_effort')!r}, want {profile.parent_effort!r}"
        )
    agents = data.get("agents") or {}
    if bool(agents.get("enabled")) != profile.agents_enabled:
        errors.append(f"agents.enabled is {agents.get('enabled')!r}, want {profile.agents_enabled}")
    if agents.get("default_subagent_model") != profile.subagent_model:
        errors.append(
            "default_subagent_model is "
            f"{agents.get('default_subagent_model')!r}, want {profile.subagent_model!r}"
        )
    if agents.get("default_subagent_reasoning_effort") != profile.subagent_effort:
        errors.append(
            "default_subagent_reasoning_effort is "
            f"{agents.get('default_subagent_reasoning_effort')!r}, want {profile.subagent_effort!r}"
        )
    hidden = (data.get("features") or {}).get("multi_agent_v2") or {}
    if hidden.get("hide_spawn_agent_metadata") is not False:
        errors.append("features.multi_agent_v2.hide_spawn_agent_metadata must be false")
        summary["hide_spawn_agent_metadata"] = str(
            hidden.get("hide_spawn_agent_metadata")
        ).lower()
    if profile.agents_enabled and profile.subagent_model == profile.parent_model:
        errors.append("routed profile child model clones the parent")
    if not worker_path.exists():
        errors.append(f"missing worker {worker_path}")
        return errors, summary
    worker = tomllib.loads(worker_path.read_text())
    if worker.get("model") != profile.subagent_model:
        errors.append(
            f"worker model is {worker.get('model')!r}, want {profile.subagent_model!r}"
        )
    if worker.get("model_reasoning_effort") != profile.subagent_effort:
        errors.append(
            "worker model_reasoning_effort is "
            f"{worker.get('model_reasoning_effort')!r}, want {profile.subagent_effort!r}"
        )
    agents_md = (codex_home / "AGENTS.md").read_text() if (codex_home / "AGENTS.md").exists() else ""
    if profile.agents_enabled:
        if profile.subagent_model not in agents_md:
            errors.append("AGENTS.md does not name the child model")
        if "fork_turns: none" not in agents_md:
            errors.append("AGENTS.md missing fork_turns: none")
    expected_agents = render_template("AGENTS.md", profile).rstrip()
    if expected_agents not in agents_md:
        errors.append("AGENTS.md does not contain the personal monitor-only delegation rules")
    expected_worker = tomlkit.parse(render_template("agents/worker.toml", profile))
    if worker.get("developer_instructions") != expected_worker["developer_instructions"]:
        errors.append("worker instructions do not match the personal monitor-only policy")
    return errors, summary


def format_verify(errors: list[str], summary: dict[str, str]) -> str:
    lines = [
        f"profile: {summary['profile']}",
        f"parent:  {summary['parent']}",
        f"child:   {summary['child']}",
        f"worker:  {summary['worker']}",
        f"agents.enabled: {summary['agents_enabled']}",
        f"hide_spawn_agent_metadata: {summary['hide_spawn_agent_metadata']}",
    ]
    if errors:
        lines.append("verify: FAIL")
        lines.extend(f"- {err}" for err in errors)
    else:
        lines.append("verify: OK")
    return "\n".join(lines)
