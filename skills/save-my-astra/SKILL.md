---
name: save-my-astra
description: >-
  Install or update PanBikang's personal Save My Astra fork. Astra low writes
  all files including tests; Luna max performs read-only investigation,
  runs specified checks, and monitors tasks. Supports fresh installation and replacing
  upstream Save My Astra while preserving unrelated Codex configuration.
  安装或更新 PanBikang 个人版 Save My Astra；Astra 编写所有文件，
  Luna 只读调查、执行指定检查和监控长任务，支持全新安装及覆盖原版。
---

# Save My Astra: Personal Fork

Use https://github.com/PanBikang/save-my-astra, forked from fengxiaohu/save-my-astra. Keep the installed skill name `save-my-astra` so this replaces the original installation.

使用 https://github.com/PanBikang/save-my-astra，源自 fengxiaohu/save-my-astra。安装后的技能名保持 `save-my-astra`，以覆盖原版安装。

## Ownership / 分工

Astra owns all authored changes, including code, tests, fixtures, documentation, configuration, scripts, refactors, and formatting, plus decisions and final acceptance. Luna may perform bounded read-only searches, call-site inventories, log analysis, focused reviews, exact parent-specified test/check commands, and long-task monitoring. No child-authored file changes, weakened assertions, snapshot/golden updates, automatic fixes, dependency installation, production jobs, retries, cancellation, commits, or publishing. Check-generated disposable caches/logs/reports are allowed only at locations the parent explicitly names. Fallback workers follow the same boundary.

Astra 负责所有文件编写，包括代码、测试、文档、配置、脚本、重构和格式化，以及决策和最终验收。Luna 可进行有明确范围的只读搜索、调用方梳理、日志分析、专项审查，运行主代理准确指定的测试或检查命令，并监控长任务。子代理不编辑文件、不弱化断言、不更新快照或 golden 文件、不自动修复、不安装依赖、不启动生产任务、不重试、不取消、不提交或发布。检查生成的临时缓存、日志和报告仅允许写入主代理明确指定的位置；回退 worker 遵守相同边界。

Give a specific question, allowed paths, exact check commands and working directory, permitted generated-output locations, and a stopping condition. Read-only search commands may be chosen within scope. Return concise paths/lines, necessary snippets, commands/exit codes, and uncertainties. Astra reads source relevant to its edits and checks critical evidence without repeating the entire investigation. Keep small tasks with Astra.

brief 需包含具体问题、允许路径、准确检查命令和工作目录、允许产物位置及停止条件。Luna 可在范围内选择只读搜索命令。返回简洁的路径与行号、必要片段、命令与退出码及不确定点。Astra 阅读修改相关的源码并核验关键证据，避免重复整轮调查。小任务由 Astra 直接完成。

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

Start a new session to reload configuration. Verify with a bounded read-only repo investigation: the child returns evidence and does not edit files. The child must be Luna, never another Astra. If Luna is rejected, retry once with `gpt-5.6-terra` / `max` and report the fallback; `./scripts/install.sh --profile astra-terra` installs that default.

开启新会话以重新加载配置，用限定范围的只读仓库调查验证：子代理返回证据而不编辑文件。子代理应为 Luna，不应复制 Astra。Luna 被拒绝时可用 `gpt-5.6-terra` / `max` 重试一次并告知用户；`./scripts/install.sh --profile astra-terra` 可安装该默认路由。
