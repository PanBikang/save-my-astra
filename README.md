# Save My Astra: PanBikang's Fork

Personal fork of [fengxiaohu/save-my-astra](https://github.com/fengxiaohu/save-my-astra). Astra authors all file changes. Luna performs bounded read-only investigation, runs specified checks, and monitors long-running tasks.

[fengxiaohu/save-my-astra](https://github.com/fengxiaohu/save-my-astra) 的个人 fork。Astra 负责所有文件编写；Luna 负责有明确范围的只读调查、指定检查和长任务监控。

## Routing / 分工

Default: `gpt-6-astra` / `low` as parent, `gpt-5.6-luna` / `max` as worker, with `fork_turns: none`. Terra / `max` is the fallback when Luna cannot spawn.

默认主代理为 `gpt-6-astra` / `low`，子代理为 `gpt-5.6-luna` / `max`，使用 `fork_turns: none`。Luna 无法启动时回退到 Terra / `max`。

| Owner / 负责者 | Work / 工作 |
| --- | --- |
| Astra | Decisions, all authored changes including code/tests/configuration, final diagnosis and acceptance / 决策、所有文件编写（包括代码、测试、配置）、最终诊断和验收 |
| Luna | Read-only searches, call-site inventories, log analysis, focused reviews, specified test/check commands, monitoring / 只读搜索、调用方梳理、日志分析、专项审查、指定测试或检查命令、监控 |

Luna never authors or edits files, including tests, fixtures, documentation, configuration, scripts, refactors, or formatting. It cannot weaken assertions, update snapshots/golden files, apply automatic fixes, install dependencies, start production jobs, retry failures, cancel jobs, commit, or publish. Specified check commands may generate disposable caches/logs/reports only in locations explicitly allowed by Astra.

Luna 不编写或编辑任何文件，包括测试、fixture、文档、配置、脚本、重构或格式化；不弱化断言、不更新快照或 golden 文件、不自动修复、不安装依赖、不启动生产任务、不重试失败、不取消作业、不提交或发布。指定检查命令只能在 Astra 明确允许的位置生成临时缓存、日志或报告。

Give workers a specific question, allowed paths, exact check commands and working directory, permitted output locations, and a stopping condition. Read-only searches can be chosen within that scope. Return concise paths/lines, necessary snippets, commands/exit codes, and uncertainties. Astra reads the source relevant to its changes and checks critical findings without repeating the entire investigation. Small tasks stay with Astra.

brief 需明确问题、允许读取的路径、准确的检查命令和工作目录、允许的产物位置及停止条件。范围内的只读搜索可由 Luna 自行选择命令。返回简洁的路径与行号、必要片段、命令与退出码及不确定点。Astra 阅读修改相关的源码并核验关键发现，避免重复整轮调查。小任务由 Astra 直接完成。

For example, Astra can ask Luna to locate all callers and collect a named test failure while Astra implements the fix. Luna reports evidence; Astra writes both the fix and regression tests. Monitoring uses a shared PID, job ID, or status source, a polling interval, and a stopping condition; some tools' session IDs are agent-local.

例如，Astra 可以让 Luna 定位所有调用方、收集指定测试的失败信息，自己同时实现修复。Luna 返回证据，修复代码和回归测试均由 Astra 编写。监控任务需指定共享 PID、作业 ID 或状态源、轮询间隔及停止条件；部分工具的会话 ID 仅在原代理内可用。

These are instruction-based boundaries, not filesystem sandbox enforcement. Delegation can increase total tokens; savings depend on replacing Astra's reading and checking work without duplicating it. Waiting itself does not necessarily consume model tokens. This fork does not guarantee lower cost or eliminate bugs.

这些边界由指令约束，并非文件系统沙箱强制隔离。委派可能增加总 token；费用收益取决于是否替代了 Astra 的大量阅读和检查，而没有重复工作。工具等待本身不一定消耗模型 token。本 fork 不保证降低费用或消除 bug。

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

Start a new Codex session after installation so it reloads the configuration and worker instructions. Verify with a bounded read-only repo investigation: Luna returns source references and does not edit files. Root effort selected in the UI or CLI can override the installed default.

安装后开启新的 Codex 会话，使配置和 worker 指令重新加载。可通过限定范围的只读仓库调查验证：Luna 返回源码位置，不编辑文件。界面或 CLI 中选择的主代理思考强度可以覆盖安装默认值。

## Checks / 检查

```bash
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
.venv/bin/python -m eval check
```

The upstream evaluation tools remain under `eval/`; their historical results do not measure this fork's ownership policy. See [docs/method.md](docs/method.md).

上游评测工具保留在 `eval/`；历史结果不代表本 fork 的当前分工。详见 [docs/method.md](docs/method.md)。
