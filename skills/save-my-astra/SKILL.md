---
name: save-my-astra
description: >-
  Install or update PanBikang's personal Save My Astra fork. Astra low writes
  all files including tests and runs ordinary work; Luna max only waits for
  existing long-running tasks. Supports fresh installation and replacing
  upstream Save My Astra while preserving unrelated Codex configuration.
  安装或更新 PanBikang 个人版 Save My Astra；Astra 编写所有文件并执行工作，
  Luna 仅等待和监控已有长任务，支持全新安装及覆盖原版。
---

# Save My Astra: Personal Fork

Use https://github.com/PanBikang/save-my-astra, forked from fengxiaohu/save-my-astra. Keep the installed skill name `save-my-astra` so this replaces the original installation.

使用 https://github.com/PanBikang/save-my-astra，源自 fengxiaohu/save-my-astra。安装后的技能名保持 `save-my-astra`，以覆盖原版安装。

## Ownership / 分工

Astra owns all writing, including code, tests, fixtures, documentation, configuration, scripts, and refactors, plus ordinary execution, scans, debugging, and review. Luna only waits for tasks the parent already started, polls explicitly assigned read-only status/log sources, and reports completion, failure, or timeout. No child file writes, test runs, new jobs, retries, cancellation, or repairs. Fallback workers follow the same boundary.

Astra 负责所有文件编写，包括代码、测试、文档、配置、脚本和重构，以及普通执行、扫描、调试和审查。Luna 仅等待主代理已启动的任务，只读轮询指定状态或日志，报告完成、失败或超时。子代理不写文件、不运行测试、不新建任务、不重试、不取消也不修复；回退 worker 遵守相同边界。

Default routing: `gpt-6-astra` / `low`, `gpt-5.6-luna` / `max`, worker `luna_max_worker`, `fork_turns: none`. Give monitors a shared job/PID/status source, polling interval, and stopping condition. Some command session IDs are agent-local; use a shared source instead. Keep brief waits with the parent. Do not promise lower total tokens or cost: waiting in a tool need not consume model tokens, while spawning and polling add overhead.

默认路由：`gpt-6-astra` / `low`、`gpt-5.6-luna` / `max`，worker 为 `luna_max_worker`，使用 `fork_turns: none`。监控 brief 需包含共享作业 ID、PID 或状态源、轮询间隔及停止条件。部分命令会话 ID 仅在原代理可用，此时改用共享状态源。短等待由主代理处理。工具等待不一定消耗模型 token，而启动和轮询子代理有额外开销，不承诺降低总 token 或费用。

## Install / 安装

Clone this fork if needed. Requires Python 3.11+. Run from its checkout; use the same installer for fresh installs and upgrades:

如有需要先克隆个人 fork。需要 Python 3.11+，在仓库中执行；全新安装和覆盖安装使用同一安装器：

```bash
git clone https://github.com/PanBikang/save-my-astra.git
cd save-my-astra
python3 -m venv .venv
.venv/bin/python -m pip install -e .
./scripts/install.sh --dry-run
./scripts/install.sh
.venv/bin/python -m eval verify --profile astra-luna
```

For an existing checkout, use `git pull --ff-only`, refresh dependencies, and rerun the installer. `--codex-home DIR` selects a target; otherwise it uses `$CODEX_HOME` or `~/.codex`. `ASTRA_PYTHON` overrides the interpreter. Do not substitute upstream installation instructions or manually overwrite whole user configuration files.

已有 checkout 时使用 `git pull --ff-only`，更新依赖后重跑安装器。`--codex-home DIR` 指定目标，否则使用 `$CODEX_HOME` 或 `~/.codex`。`ASTRA_PYTHON` 指定解释器。不要改用上游安装说明，也不要手动整份覆盖用户配置。

The installer backs up config, AGENTS, the selected worker, and the skill before replacing them. It merges the routing keys (`model`, `model_reasoning_effort`, `default_subagent_model`, `default_subagent_reasoning_effort`, `hide_spawn_agent_metadata`) while preserving provider, MCP, notify, plugins, and unrelated settings. It replaces the known legacy orchestration block or its managed block in AGENTS, keeping surrounding instructions.

安装器在替换前备份 config、AGENTS、所选 worker 和 skill。合并路由字段（`model`、`model_reasoning_effort`、`default_subagent_model`、`default_subagent_reasoning_effort`、`hide_spawn_agent_metadata`），保留 provider、MCP、notify、plugins 和其他设置。AGENTS 仅替换可识别的旧编排规则块或管理标记块，保留周围指令。

## Verify / 验证

Start a new session to reload configuration. Verify monitoring on an actual long-running task, using a shared status source. The child must be Luna, never another Astra. If Luna is rejected, retry once with `gpt-5.6-terra` / `max` and report the fallback; `./scripts/install.sh --profile astra-terra` installs that default.

开启新会话以重新加载配置，用真实长任务和共享状态源验证监控。子代理应为 Luna，不应复制 Astra。Luna 被拒绝时可用 `gpt-5.6-terra` / `max` 重试一次并告知用户；`./scripts/install.sh --profile astra-terra` 可安装该默认路由。
