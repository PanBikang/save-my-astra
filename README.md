# Save My Astra: PanBikang's Fork

Personal fork of [fengxiaohu/save-my-astra](https://github.com/fengxiaohu/save-my-astra). Astra writes all files and executes the work. Luna only waits for existing long-running tasks and reports their status.

[fengxiaohu/save-my-astra](https://github.com/fengxiaohu/save-my-astra) 的个人 fork。Astra 负责所有文件编写和实际执行；Luna 只等待已启动的长任务、轮询状态并报告结果。

## Routing / 分工

Default: `gpt-6-astra` / `low` as parent, `gpt-5.6-luna` / `max` as monitor, with `fork_turns: none`. Terra / `max` is the fallback when Luna cannot spawn.

默认主代理为 `gpt-6-astra` / `low`，监控子代理为 `gpt-5.6-luna` / `max`，使用 `fork_turns: none`。Luna 无法启动时回退到 Terra / `max`。

| Owner / 负责者 | Work / 工作 |
| --- | --- |
| Astra | Code, tests, fixtures, documentation, configuration, scripts, refactors, scans, debugging, reviews, running commands / 代码、测试、文档、配置、脚本、重构、扫描、调试、审查和命令执行 |
| Luna | Wait for an existing task; read assigned status/log sources; report completion, failure or timeout / 等待已有任务，只读轮询指定状态或日志，报告完成、失败或超时 |

Luna cannot write any files, start jobs, run tests, retry, cancel, or fix tasks. Short waits stay with Astra. A monitor needs a shared PID, job ID, or status source, a polling interval, and a stopping condition. Some tools expose session IDs only to the agent that created them; use a shared status source in that case.

Luna 不写任何文件、不启动任务、不运行测试、不重试、不取消也不修复任务。短暂等待由 Astra 直接处理。监控任务需明确共享 PID、作业 ID 或状态源，以及轮询间隔和停止条件。部分工具的会话 ID 仅对创建它的代理可见，此时使用共享状态源。

These are instruction-based boundaries, not filesystem sandbox enforcement. Waiting itself does not necessarily consume model tokens; adding a monitor can increase total tokens. This fork prioritizes ownership and convenience, with no guaranteed cost reduction or bug prevention.

这些边界由指令约束，并非文件系统沙箱强制隔离。工具等待本身不一定消耗模型 token，增加监控代理可能增加总 token。本 fork 优先保证分工和使用习惯，不保证节省费用或消除 bug。

## Install or Replace / 全新安装或覆盖旧版

Requires Git and Python 3.11+. Use the same command for a fresh install, replacing upstream Save My Astra, or reinstalling this fork. A local virtual environment keeps dependencies separate.

需要 Git 和 Python 3.11+。全新安装、覆盖原版 Save My Astra、重装个人版均使用同一个安装命令；依赖放入仓库自己的虚拟环境。

```bash
git clone https://github.com/PanBikang/save-my-astra.git
cd save-my-astra
python3 -m venv .venv
.venv/bin/python -m pip install -e .
./scripts/install.sh
.venv/bin/python -m eval verify --profile astra-luna
```

Preview or choose a different target/profile:

预览变更，或指定目标目录和 profile：

```bash
./scripts/install.sh --dry-run
./scripts/install.sh --codex-home /path/to/.codex
./scripts/install.sh --profile astra-terra
```

The installer uses the repository's `.venv/bin/python3` when available, otherwise `python3`. Set `ASTRA_PYTHON` to override. The target defaults to `$CODEX_HOME` or `~/.codex`. A dry run writes no target files; its preview includes existing configuration, so do not publish it without checking for secrets.

安装器优先使用仓库的 `.venv/bin/python3`，否则使用 `python3`；可用 `ASTRA_PYTHON` 指定解释器。目标默认为 `$CODEX_HOME` 或 `~/.codex`。预览不写目标文件，但会包含现有配置，发布前需检查是否有密钥。

## Upgrade and Backup / 更新与备份

```bash
git pull --ff-only
.venv/bin/python -m pip install -e .
./scripts/install.sh
```

Every install backs up existing files under a unique `backups/save-my-astra-<timestamp>-<suffix>/` directory in the target Codex home, preserving relative paths:

每次安装都会在目标 Codex 目录下创建唯一的 `backups/save-my-astra-<timestamp>-<suffix>/` 目录，按原相对路径备份已有文件：

- `config.toml`
- `AGENTS.md`
- `agents/luna-max-worker.toml` (or the selected profile's worker / 或所选 profile 的 worker)
- `skills/save-my-astra/SKILL.md`

The config merge preserves provider, MCP, notify, plugins, named profiles, and unrelated agent settings. The installer replaces the known old orchestration block or its own marked block in `AGENTS.md`, preserving surrounding instructions. Worker and skill files use their existing names so this fork replaces the original installation. Restore the saved files to the same relative paths to roll back.

配置合并保留 provider、MCP、notify、plugins、命名 profile 和其他 agent 设置。安装器替换 `AGENTS.md` 中可识别的旧编排规则块或个人版标记块，保留块外指令。worker 和 skill 沿用原名称，实现覆盖安装。回滚时将备份文件还原至对应相对路径。

Start a new Codex session after installation so it reloads the configuration and worker instructions. Verify with a real long-running task: Astra starts it, and may delegate monitoring to Luna using a shared status source. Root effort selected in the UI or CLI can override the installed default.

安装后开启新的 Codex 会话，使配置和 worker 指令重新加载。可用实际长任务验证：由 Astra 启动，按需交给 Luna 通过共享状态源监控。界面或 CLI 中选择的主代理思考强度可以覆盖安装默认值。

## Checks / 检查

```bash
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
.venv/bin/python -m eval check
```

The upstream evaluation tools remain under `eval/`; their historical results do not measure this fork's monitor-only policy. See [docs/method.md](docs/method.md).

上游评测工具保留在 `eval/`；历史结果不代表本 fork 的仅监控分工。详见 [docs/method.md](docs/method.md)。
