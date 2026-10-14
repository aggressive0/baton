# Verifiable Session Handoff

**Pass the baton, not the blur. Two-way session handoff for AI coding agents.**

**接力棒，不是模糊回忆。面向 AI 编码 Agent 的双向会话交接。**

[English](#english) · [中文](#中文)

---

## English

### What it does

Verifiable Session Handoff helps one coding-agent session hand work to the next. It creates a single
active `HANDOFF.md`, rebuilt from repository evidence and durable log entries,
then checks that handoff against the current project before resuming.

A handoff contains **claims to verify, not facts to trust blindly**.

| Protocol | Purpose |
|---|---|
| **LOG** | Capture user requirements, rejected approaches, and pitfalls when they happen. Re-read the written entry to confirm persistence. |
| **WRITE** | Rebuild task state from files and commands; label claims `verified`, `reported`, `unverified`, or `blocked`; validate, scan, and save with a stale-write guard. |
| **READ** | Compare recorded state with current reality, verify material claims, then resume according to action risk. |
| **PROMOTE** | Propose durable cross-task knowledge for project instructions after deduplication, conflict review, and user confirmation. |

### What it does not guarantee

No prompt or skill can guarantee that every important event is logged before
context loss, that a secret scanner catches all secrets, or that Git status
proves an external upload/deployment. Verifiable Session Handoff makes evidence and uncertainty
visible; it does not turn unverified claims into facts.

### Install

Clone/download the repository into your agent's skills directory. Example for
Claude Code:

```bash
# Personal skill
mkdir -p ~/.claude/skills
git clone https://github.com/aggressive0/baton.git ~/.claude/skills/verifiable-session-handoff

# Or install at project level from the project root
mkdir -p .claude/skills
git clone https://github.com/aggressive0/baton.git .claude/skills/verifiable-session-handoff
```

The skill uses the Agent Skills `SKILL.md` convention. Other runtimes may use a
different skill directory; follow that runtime's installation rules.

### Use

During work, make sure important events are logged as they happen. Example:

> Log this: `pytest -q` hides skipped tests

When pausing unfinished work:

> Write a handoff for the next session.

In a fresh session:

> Continue from the handoff.

A low-risk, reversible next step can proceed after a concise status report. The
agent should pause for ambiguity, material state conflicts, destructive actions,
or external side effects. A handoff is never authorization to deploy, publish,
delete data, or change permissions.

### Validate the project files

Requires Python 3; the scripts use only the Python standard library.

```bash
# Validate an existing handoff
python scripts/handoff.py validate HANDOFF.md

# Capture the fingerprint before preparing the candidate
FINGERPRINT="$(python scripts/handoff.py fingerprint HANDOFF.md)"

# Scan the candidate before saving
python scripts/scan_secrets.py /tmp/HANDOFF.candidate.md

# Save only if the file still matches the version you originally read
python scripts/handoff.py safe-write \
  --target HANDOFF.md \
  --candidate /tmp/HANDOFF.candidate.md \
  --expected-sha "$FINGERPRINT"
```

If `HANDOFF.md` did not exist when the candidate was prepared, use
`--expected-missing` instead of `--expected-sha`.

The safe-write helper coordinates writers that use the helper and replaces a
validated file atomically. It does **not** lock manual editors or agents that
bypass it; always re-read and validate after writing. A leftover lock file is
not removed automatically: check whether a writer is active before deleting a
stale lock.

The scanner prints file, line, and finding category, but not the matched value.
`safe-write` repeats the scan and blocks unapproved findings at the save
boundary. An inspected non-secret false positive can be allowed explicitly with
`--allow-finding FILENAME:LINE:CATEGORY:LINE_SHA256`; never use this to retain a real secret.
Exit codes: `0` no configured-pattern matches; `1` at least one finding; `2`
usage/read error. A clean scan is not proof that no sensitive information is
present; inspect the handoff manually too.

### Cold-start acceptance test

1. Start a real, unfinished task. Capture at least one user decision or pitfall.
2. Write a handoff. Validate it and inspect evidence statuses, protected entries,
   next steps, and scan results.
3. Start a genuinely fresh session with the same project and ask it to continue
   from the handoff.
4. Check whether it reports drift, preserves decisions, distinguishes verified
   evidence from historical claims, and chooses a safe next action.
5. Repeat after changing HEAD, dirtying a file, changing a recorded file, and
   creating a stale-write conflict. The helper should refuse stale replacement.

Do not measure success only by Markdown formatting. A structurally valid file
that loses a user constraint or misstates project state is still a failed handoff.

### Repository layout

```text
baton/
├── SKILL.md
├── references/
│   ├── template.md
│   └── examples.md
├── scripts/
│   ├── handoff.py
│   ├── scan_secrets.py
│   └── scan.sh
├── tests/
├── TESTING.md
├── MIGRATION.md
├── README.md
├── CHANGELOG.md
└── LICENSE
```

## 中文

### 这是什么

Verifiable Session Handoff 用于把一个 AI 编码会话的工作状态交给下一个会话。它让 Agent 从仓库证据和持久化日志重建 `HANDOFF.md`，并在恢复工作前核对交接内容与当前项目状态。

核心原则：**交接文档里是待验证的主张，不是可以盲信的事实。**

| 协议 | 作用 |
|---|---|
| **LOG** | 用户要求、用户否决、踩坑发生时立即记录，并重新读取确认写入成功。 |
| **WRITE** | 根据文件与命令重建任务状态；把主张标记为 `verified`、`reported`、`unverified` 或 `blocked`；校验、扫描，并防止覆盖已变化的交接文件。 |
| **READ** | 比较交接记录与真实状态，核验重要主张，再按下一步操作的风险决定继续还是暂停。 |
| **PROMOTE** | 经过去重、冲突检查和用户确认后，将跨任务有效的知识迁移到项目指令文件。 |

### 保证边界

任何提示词或 Skill 都无法保证上下文丢失前每条重要事件都已记录，也不能保证秘钥扫描发现所有敏感信息，更不能只凭 Git 状态证明外部上传或部署成功。Verifiable Session Handoff 的目标是暴露证据与不确定性，而不是把未经验证的说法变成事实。

### 安装

下载或克隆本仓库，并放到 Agent 的 Skill 目录。Claude Code 示例：

```bash
# 个人级
mkdir -p ~/.claude/skills
git clone https://github.com/aggressive0/baton.git ~/.claude/skills/verifiable-session-handoff

# 或在项目根目录安装为项目级 Skill
mkdir -p .claude/skills
git clone https://github.com/aggressive0/baton.git .claude/skills/verifiable-session-handoff
```

其他运行时的 Skill 目录可能不同，请遵循对应工具的安装约定。

### 使用

工作过程中，重要事件发生时就记录。例如：

> 记个坑：`pytest -q` 会隐藏被跳过的测试

暂停未完成的任务时：

> 给下一个会话写份交接。

新会话中：

> 从交接文件继续上次的工作。

低风险、可逆的下一步可以在简短汇报状态后继续；需求不明、项目状态存在重大冲突、破坏性操作或外部副作用则应暂停。交接文件不是部署、发布、删除数据或修改权限的授权。

### 本地验证工具

需要 Python 3；脚本仅依赖 Python 标准库。

```bash
python scripts/handoff.py validate HANDOFF.md
FINGERPRINT="$(python scripts/handoff.py fingerprint HANDOFF.md)"  # 编辑前先记录
python scripts/scan_secrets.py /tmp/HANDOFF.candidate.md

python scripts/handoff.py safe-write \
  --target HANDOFF.md \
  --candidate /tmp/HANDOFF.candidate.md \
  --expected-sha "$FINGERPRINT"
```

如果准备候选文件时 `HANDOFF.md` 不存在，使用 `--expected-missing`。安全写入助手只协调同样使用它的写入方；手工编辑器或绕过助手的 Agent 不受它的锁保护，所以保存后仍需重新读取和校验。残留锁不会自动删除；确认没有写入进程后再清理。

扫描器只显示文件、行号和命中类别，不打印可能泄漏的匹配值。退出码：`0` 没有配置规则命中；`1` 有命中；`2` 用法或读取错误。零命中不代表绝对安全，仍需人工检查。

### 升级已有交接文件

0.2.0 修改了交接文件结构，已有的 v0.1.x `HANDOFF.md` 不会原样通过新版校验器。升级后的第一次 WRITE 应重建新结构，同时保留受保护内容。请按 [MIGRATION.md](MIGRATION.md) 操作。

### 冷启动验收测试

1. 选一个真实、尚未完成的任务，至少记录一次用户决定或踩坑。
2. 生成交接后运行校验，检查证据状态、受保护记录、下一步和扫描结果。
3. 在同一项目启动一个真正的新会话，只要求它从交接继续。
4. 检查它是否报告状态漂移、保留用户决定、区分验证证据和历史主张，并选择安全的下一步。
5. 再测试 HEAD 变化、工作区变脏、记录文件变化和过期写入冲突；写入助手应拒绝覆盖旧版本。

不要只看 Markdown 格式是否正确。结构正确但丢失用户约束或误报项目状态，仍然是失败的交接。

## License

MIT. See `LICENSE`.
