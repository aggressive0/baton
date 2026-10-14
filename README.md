# baton

**Pass the baton, not the blur. Two-way session handoff protocol for AI coding agents.**
**接力棒，不是模糊回忆。面向 AI 编码 Agent 的双向会话交接协议。**

[English](#english) · [中文](#中文)

---

## English

### What it is

When an agent session ends, its context dies with it. Compaction is lossy
and automatic; recall from a dying context is worse. This skill makes the
agent write a single `HANDOFF.md` — **rebuilt from evidence** (git, files,
append-only logs), not recalled from memory — and, in the next session's
first minutes, **verify** that document against the repo before trusting
it.

Core idea: a handoff contains *claims*, not *facts*. Write from evidence,
read with verification.

| Mechanism | What it does |
|---|---|
| **LOG** | Pitfalls and user rejections are appended to protected sections the moment they happen — dated, crash- and compaction-resilient |
| **WRITE** | Rebuilds HANDOFF.md from git + logs at session end; per-section budgets under a 120-line cap measured by command; lists PROMOTE candidates for your confirmation; scans for secrets; refuses to overwrite a handoff changed since the session last read it |
| **READ** | New session checks git drift, spot-checks claims (harder on self-admitted reconstructed handoffs), echoes the plan back and waits for your confirmation before touching anything |
| **PROMOTE** | Durable knowledge moves to CLAUDE.md/AGENTS.md by a decidable test — does the ban survive a task switch? The handoff stays a baton, not a wiki |

Works with any tool that follows the [Agent Skills](https://github.com/anthropics/skills)
SKILL.md convention (Claude Code and compatible runtimes).

### Why not just /compact or CLAUDE.md?

- **Compaction** is lossy, automatic, and unverifiable — you get a summary,
  not a state transfer.
- **CLAUDE.md** holds conventions true across all sessions; it is the wrong
  place for "what am I stuck on right now". This skill PROMOTEs durable
  facts there and keeps task state in HANDOFF.md.
- **A plain handoff template** (five paragraphs written at session end)
  fails twice: it recalls from an already-degraded context, and nobody
  verifies it on the other side. The protocol here fixes both.

### Install

```bash
# personal — available in all projects
cp -r baton ~/.claude/skills/

# or project-level — shared via the repo
cp -r baton .claude/skills/
```

### Usage

**During a session** — no command needed; the agent appends pitfalls and
rejections as they happen. You can also say:

> Log this: `pytest -q` hides skipped tests
> 记个坑：pytest -q 会隐藏 skip 的测试

**Session ending:**

> Session's ending, write a handoff
> 会话要结束了，写份交接

**New session:**

> Continue from the handoff
> 继续上次的工作

The agent will report git drift, restate task / blocker / plan, and wait
for your confirmation before working. On any conflict, the repo wins and
the handoff gets fixed on the spot.

### Cold-start acceptance test

Verify your install with a real handoff:

1. Pick a real task; work on it; hit at least one real pitfall.
2. Say "write a handoff". Check HANDOFF.md: ≤ 120 lines, a verbatim error
   in Section 4, your rejections in Section 2.
3. Open a **fresh** session in the same repo. Say only: "continue from the
   handoff".
4. Pass = it restates task / blocker / plan, shows a git-drift report
   first, asks **zero** clarifying questions about already-decided things,
   and avoids every recorded pitfall. Fail = the handoff was the bug; fix
   the handoff, not the protocol.

### Repo layout

```
baton/
├── SKILL.md              # the protocol: LOG / WRITE / READ / PROMOTE
├── references/
│   ├── template.md       # HANDOFF.md template + per-field rules + scan list
│   └── examples.md       # worked good/bad examples
├── scripts/
│   └── scan.sh           # optional deterministic secret scan
├── README.md
├── LICENSE               # MIT
└── CHANGELOG.md
```

### Design decisions

- HANDOFF.md is meant to be **committed**: teams share it, git history is
  the archive — hence the secret scan on every write. Gitignore it if you
  prefer; the skill adapts.
- One file, always the current state. History lives in git.
- Anti-bloat is enforced, not suggested: 120-line cap checked with a
  command, per-section budgets, rebuild-from-evidence on every write
  (prevents copy-of-copy degradation), and two append-only protected
  sections — with one exit valve: fixed pitfalls move to a tail
  `## Archived` section, outside the budget and still append-only.
- Concurrency is handled, not hoped away: WRITE refuses to overwrite a
  handoff that changed since the session last read it, and the branch
  strategy is explicit — merge often, keep HANDOFF.md out of `main`, or
  opt into per-branch `HANDOFF.<branch>.md` files.

---

## 中文

### 这是什么

Agent 会话结束时，上下文随之消亡。compaction 有损且不可验证，靠残缺记忆回忆更糟。这个 skill 让 Agent 在会话结束前重建一份 `HANDOFF.md` —— **从证据重建**（git、文件、追加式日志），而不是从记忆里回忆 —— 并在新会话开始的头几分钟里**先验证再信任**。

核心原则：交接文档里是主张，不是事实。写入靠证据，读取必验证。

| 机制 | 作用 |
|---|---|
| **LOG** | 踩坑和用户否决当场追加到受保护段，带日期，不怕崩溃和 compaction |
| **WRITE** | 会话末从 git + 日志重建，逐节预算、120 行用命令实测；PROMOTE 候选列给你确认；保存前扫描秘钥；拒绝覆盖本会话没读过的最新交接 |
| **READ** | 新会话先查 git 漂移、抽查断言（自报 reconstructed 的文档抽查加倍）、向你复述计划并等你确认，然后才动手 |
| **PROMOTE** | 用可判定规则迁移永久知识——这条 ban 换个任务还成立吗？成立就进 CLAUDE.md/AGENTS.md，交接棒不做 wiki |

适用于遵循 SKILL.md 规范的工具（Claude Code 及兼容运行时）。

### 为什么不用 /compact 或 CLAUDE.md？

- **Compaction** 有损、自动、无法验证 —— 你得到的是摘要，不是状态转移。
- **CLAUDE.md** 存放对所有会话都成立的约定；"我现在卡在哪"这类任务状态放那里是错的。本 skill 把持久事实 PROMOTE 到那里，任务状态留在 HANDOFF.md。
- **普通交接模板**（会话末写五个段落）会输两次：从已经退化的上下文里回忆，而且对面没人验证。本协议两头都修了。

### 安装

```bash
# 个人级 —— 所有项目可用
cp -r baton ~/.claude/skills/

# 或项目级 —— 随仓库共享
cp -r baton .claude/skills/
```

### 用法

**会话中** —— 无需指令，Agent 会在踩坑/被否决的瞬间自动记录；也可以主动说：

> 记个坑：pytest -q 会隐藏 skip 的测试

**会话要结束时：**

> 会话要结束了，写份交接

**新会话：**

> 继续上次的工作

Agent 会先报告 git 漂移，复述任务/卡点/计划，等你确认后才开工。交接与仓库现状冲突时，以仓库为准，并当场修正交接文档。

### 冷启动验收测试

1. 选一个真实任务，做到至少踩一个真实的坑。
2. 说"写份交接"。检查 HANDOFF.md：≤120 行、第 4 段有逐字报错、第 2 段有你的否决记录。
3. 在同一仓库开一个**全新**会话，只说："继续上次的工作"。
4. 通过标准：复述任务/卡点/计划；先出示 git 漂移报告；对已决事项提出 **0 个**澄清问题；避开所有记录的坑。不通过，就是交接文档有 bug —— 改文档，不改协议。

### 设计取舍

- HANDOFF.md 默认**提交进 git**：团队共享，git 历史天然归档，所以每次写入都扫秘钥。想 gitignore 也可以，skill 会自适应。
- 单文件，永远是当前态；历史交给 git。
- 反膨胀是硬规则不是建议：120 行上限用命令测量；逐节行数预算；每次从证据重建而非复制上一份（防"传话游戏"式退化）；两段只增不删的受保护段，唯一出口是已修复的坑打上 `resolved:` 标记移入文件尾部 `## Archived` 区（不计入预算、依旧只增不删）。
- 并发冲突是被处理的，不是被祈祷掉的：WRITE 覆盖前校验文件自本会话上次读取后未被他人改动；HANDOFF.md 跟随功能分支，团队需显式选型（勤合并 / 不进 main / 可选 `HANDOFF.<branch>.md` 按分支分文件）。

## License

MIT
