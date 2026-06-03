<div align="right"><a href="README.md">简体中文</a> | <b>English</b></div>

<div align="center">

# ✨ silk-starry

**Master Claude Code's memory mechanism — write your `CLAUDE.md` well and keep it that way. No hand-writing, no remembering to maintain it.**

[![Claude Code](https://img.shields.io/badge/Claude%20Code-skill-8A2BE2)](https://code.claude.com/docs/en/skills)
[![CI](https://github.com/hjxccc/silk-starry/actions/workflows/ci.yml/badge.svg)](https://github.com/hjxccc/silk-starry/actions/workflows/ci.yml)
[![tested](https://img.shields.io/badge/tested-Windows%20%7C%20macOS%20%7C%20Linux-2ea44f)](https://github.com/hjxccc/silk-starry/actions/workflows/ci.yml)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-runtime%20neutral-blueviolet)](#)
[![version](https://img.shields.io/badge/version-0.1.0-blue)](CHANGELOG.md)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

<img src="assets/hero.svg" alt="silk-starry: master Claude Code's memory mechanism" width="760">

</div>

---

## What it solves

`CLAUDE.md` is the "project memory" Claude Code injects into every conversation — it defines your project's rules and red lines, and directly shapes how well the AI codes.

But it's awkward in practice: **hard to write well, harder to maintain.**

- Too long → the AI can't retain it and stops following it. Anthropic's own guidance says a bloated CLAUDE.md "gets ignored — half of it"; and an independent study, [IFScale](https://arxiv.org/abs/2507.11538), separately measured even the best frontier model at only 68% adherence under 500 instructions (a common rule of thumb is ≤200 lines).
- Written like docs (folder trees, tech-stack lists) → all stuff the AI already learns from the code; pure context waste.
- Left untouched → it **rots** as the code evolves, and starts misleading the AI six months later.
- One slip → a DB password or internal IP ends up in it, committed to git.

**silk-starry takes the whole thing off your hands**: it **writes** one when you need it, **audits** it regularly, and **updates** it as the project evolves. And if your project is big — several modules (frontend, backend, tools…) in one repo, each with its own CLAUDE.md — it tells you **which one applies when you edit a given piece of code.**

And CLAUDE.md is just *one layer* of Claude Code's **memory mechanism**. Behind it sit auto-memory (the notes Claude writes itself), `.claude/rules/`, and history that can quietly balloon your disk… **Newcomers can't tell which layer a piece of experience belongs in, which layer is silently rotting, or why `~/.claude` is eating several GB.** silk-starry's goal is exactly this: **let people who don't understand the memory mechanism still use it well** — you just talk in plain words, and it puts things in the right layer, keeps them accurate, and keeps every layer clean.

> Core idea: run `CLAUDE.md` as a **behavior contract for the AI**, and treat the whole memory mechanism as a **system you can steward and keep clean** — rather than letting it rot.

**Why "short and sharp" is non-negotiable** — every extra rule in memory is one more instruction the AI must follow at once, and the more instructions, the lower the adherence:

<div align="center"><img src="assets/why-memory.svg" alt="More instructions, lower AI adherence (IFScale)" width="720"></div>

---

## Install

**One line** (recommended):
```bash
npx skills add hjxccc/silk-starry
```

**Manual**: clone into `~/.claude/skills/silk-starry/`:
```bash
git clone https://github.com/hjxccc/silk-starry.git ~/.claude/skills/silk-starry
```
Done — available across all projects, no extra config.

---

## Usage

**Three steps to start:**

1. **Install it** (see above — one line).
2. In your project directory, just tell Claude in plain words — **"Generate a CLAUDE.md for this project."**
3. silk-starry takes over: detect the stack → pick a template → trim to only the "can't-tell-from-the-code" rules → self-audit, then show you the result. **It lands only after you confirm — never writes files silently.**

That's it — you don't need to memorize any command; silk-starry understands plain language.

> 💡 If it doesn't auto-trigger, just name it: "**use silk-starry to…**" (100% reliable).

### Just say what you want

Each group below is something silk-starry will catch — say whichever feels natural:

**Generate a new one**
```
write a CLAUDE.md for the frontend module
this project has no CLAUDE.md yet, set one up
```
**Audit / slim down**
```
audit my CLAUDE.md
my CLAUDE.md is too long, trim it
check it for vague rules or leaked secrets
```
**Capture a rule / wrap-up**
```
add "run pnpm lint before commit" to the project rules
anything from this session worth saving into CLAUDE.md?
```
**Tidy / locate across files**
```
help me organize this pile of CLAUDE.md files
I'm editing the api — which CLAUDE.md applies?
```

> **When *not* to use it**: writing a README, code comments, or API docs — those aren't "project memory"; a normal chat is enough, and silk-starry won't fire on them.

<details>
<summary><b>🔹 Prefer a slash command? (optional)</b>　just one to remember: <code>/silk</code></summary>

<br>

No command zoo — **just `/silk`**, followed by plain words; silk-starry decides whether to generate / audit / evolve / scan:

```
/silk generate a CLAUDE.md for this project
/silk my CLAUDE.md is too long, trim it
/silk remember "run lint before commit" as a rule
/silk check my auto memory
/silk            ← leave it empty: it surveys the current state and asks what you want
```

Install (copy the command file into Claude's command dir):
```bash
mkdir -p ~/.claude/commands && cp ~/.claude/skills/silk-starry/commands/silk.md ~/.claude/commands/
```
Then type `/silk` to use it.

</details>

<details>
<summary><b>🔹 Turn on "auto-reminders"? (optional)</b>　nudges you to audit at session start, logs your corrections at session end</summary>

<br>

```bash
python ~/.claude/skills/silk-starry/scripts/install_hooks.py <project-root>
```
This edits that project's `.claude/settings.json` (merged with your existing config, not overwritten); it tells you the change before applying.

</details>

<details>
<summary><b>🔹 Which tools does it run under the hood?</b>　you don't need to remember them — listed just so you know</summary>

<br>

| Tool | silk-starry uses it to… |
|---|---|
| `scan` | inventory all CLAUDE.md across the repo, find modules missing one, check whether `.env`/keys are git-tracked |
| `audit` | review one CLAUDE.md: too long / secrets / vague rules / dead links / what to move out |
| `locate` | compute "which CLAUDE.md applies when editing this file" |
| `conflicts` | detect contradictions across multiple CLAUDE.md files |
| `introspect` | predict "editing this file loads which CLAUDE.md/rules, and how big" |
| `memory_digest` | mine Claude's auto-memory for recurring lessons worth promoting to rules |
| `graduate` | after promotion, clean the corresponding memory to free budget |
| `sync_targets` | wire AGENTS.md ↔ CLAUDE.md (one source, many tools) |
| `install_hooks` | install the "auto-reminder" hooks |

> All pure-stdlib Python, read-only by default; the few that write show you a diff first. To run one manually:
> `python ~/.claude/skills/silk-starry/scripts/<tool>.py <args>`

</details>

---

## The four capabilities (in detail)

| Capability | What it does |
|---|---|
| 📝 **Generate** | Detects the stack and produces a short, executable, example-backed contract — auto-dropping anything the AI could learn by reading the code. |
| 🔍 **Audit** | Flags too-long, vague, secret-leaking, broken-link content, and points out which sections to move into `.claude/rules/`. |
| 🔄 **Evolve** | Turns the things you keep reminding the AI into permanent rules — no more repeating yourself. |
| 🧭 **Orchestrate** | Big projects pack several modules into one repo; silk-starry keeps the whole set of CLAUDE.md organized: which module's missing one, what goes in root vs sub, whether they contradict, and which one to read for a given edit. |

> Bonus: **active secret-leak prevention** — a plaintext password it reads becomes a "don't hardcode credentials" rule, instead of being copied into the file.

---

## 🧪 Tested, with data

Talk is cheap. We ran a full comparison on **real open-source projects**.

> Note: **Claude Code ships a built-in `/init` command** that auto-generates a CLAUDE.md — the way most people do it today. So that's mainly what we compare silk-starry against.

**The actual output first** — same project (`psf/requests`), silk-starry's vs Claude Code's built-in `/init`:

<div align="center"><img src="assets/effect-compare.svg" alt="silk-starry output vs /init output" width="880"></div>

**Then the line count** (shorter = the AI follows it more):

<div align="center"><img src="assets/comparison.svg" alt="silk-starry vs expert vs /init line counts" width="700"></div>

| Aspect | Result |
|---|---|
| **Accurate judgment** | We wrote 20 realistic prompts — 10 that should use silk-starry, 10 deliberately similar that shouldn't (e.g. "write me a README", "add docstrings"). silk-starry got **all 20 right**: steps in when it should, never fires when it shouldn't. |
| **More concise** | Same project, **28 lines vs 117**; and **0 leaks** — built-in `/init` will copy a plaintext password it reads straight into the file. |
| **Beats the experts** | Against HumanLayer (who literally wrote *Writing a good CLAUDE.md*): silk-starry's is shorter, and **it caught that their hand-written file had gone stale** (its contents no longer matched the code), plus added gotchas they'd missed. |
| **Robust** | Fed 24 kinds of "bad input" (empty / binary / huge / malicious path-traversal…) — **not one crashed it**. |
| **Fast** | A 7000-file repo scans in **1.1 s**. |
| **Polyglot** | Python / Go / Rust / TypeScript / Ruby all verified. |

### An honest note on effectiveness
We don't claim "install it and the AI stops making mistakes." A controlled A/B (the only difference being whether CLAUDE.md exists) showed that **when the AI reads the code thoroughly, it avoids the traps with or without CLAUDE.md**. CLAUDE.md's real value is: **saving the AI from re-reading the whole project every time, covering the case where it doesn't read everything, and keeping behavior consistent** — the bigger and more rushed the project, the more it matters. silk-starry's job is to keep that contract **accurate, concise, and un-rotted**. We even tested the angles that could weaken our own claims — which is exactly why it's trustworthy.

---

## Architecture & highlights

<div align="center"><img src="assets/architecture.svg" alt="how silk-starry works" width="780"></div>

silk doesn't just manage CLAUDE.md — it sits on top of Claude Code's **entire memory mechanism**. The diagram below (mapped from Claude Code's source) shows what each layer is, how it loads, and **where silk acts**:

<div align="center"><img src="assets/memory-arch.svg" alt="Claude Code memory mechanism × where silk acts" width="860"></div>

**In one line**: silk-starry is a **curation layer on top of the official auto-memory** — the official side *captures* learnings automatically; silk-starry *writes them well, audits, and promotes them into CLAUDE.md*. It doesn't reinvent the wheel.

What it draws on:
- **Anthropic's own mechanisms** (from Claude Code's `init` / `memdir` / `sessionMemory`): recall via a **header manifest** (the model picks by description, not keyword frequency, cf. `findRelevantMemories`); **human-readable ages** ("47 days ago", cf. `memoryAge`); length/byte thresholds aligned to official constants but treated as soft warnings.
- **[Karpathy's coding guidelines](https://github.com/multica-ai/andrej-karpathy-skills)** → an optional "12-rule behavioral contract", plus **Surgical Changes (minimal diff)** applied to silk-starry's own edits.
- **Microsoft SkillLens / SkillOpt's 9-dimension rubric** (via darwin-skill) → used to harden silk-starry's own `SKILL.md`: explicit failure branches, 🔴 checkpoints, no hedging language, an anti-pattern blacklist.
- **The AGENTS.md cross-tool standard** + Cursor/Copilot **glob path rules** → behind silk-starry's cross-tool sync and `paths:` rule-splitting.

Key mechanisms:
| Mechanism | What |
|---|---|
| **Admission test** | Every rule must answer "what *specific* thing would the AI get wrong without it?" — if you can't, cut it (same spirit as the new `/init`). |
| **Graduation loop** | recurring memory → curate → (with your OK) promote into CLAUDE.md → delete from memory to free budget. **The missing link between official auto-memory and CLAUDE.md.** |
| **Nearest-match locate + glob prediction** | given a file path, computes which CLAUDE.md applies, and predicts which `.claude/rules` would trigger (picomatch-style). |
| **Progressive disclosure** | three-level loading (name+description → main instructions → references on demand), saving context. |
| **Two safety gates** | before deleting memory: ① the target must be inside the memory dir ② dry-run by default, `--confirm` required (path-traversal verified-blocked). |

**Principles**: 🧑 you always decide (diff + confirm before any write/delete) · ✂️ minimal diff · 🎯 write only what matters · 🌐 runtime-neutral (works across 50+ compatible agents).

---

## FAQ

**Does it conflict with Claude Code's built-in `/init`?** No. `/init` generates once at the start; silk-starry is a generate → audit → keep-updating loop, and the default `/init` neither prevents leaks nor handles updates.

**What is `@AGENTS.md`?** Some tools (Cursor, Copilot, Codex) read `AGENTS.md` instead of `CLAUDE.md`. One line `@AGENTS.md` in your CLAUDE.md pulls its content in — one source, every tool. silk-starry can wire this up automatically.

**Will it change my files behind my back?** No. Every write/delete shows you a diff and waits for confirmation first.

---

## ⚠️ Disclaimer

- **Not an official project**: silk-starry is a **community tool**, **not affiliated with or endorsed by Anthropic**. "Claude" / "Claude Code" are Anthropic's trademarks; "AGENTS.md", "Cursor", "Codex" etc. belong to their owners — referenced only for interoperability.
- **It creates/deletes files — review them**: it creates or modifies `CLAUDE.md`, `.gitignore`, `.claude/settings.json`; `graduate` deletes auto-memory files. All designed with "human-in-loop + diff + minimal change + dry-run by default", but **use under version control and review every change**; the author isn't liable for data loss.
- **Secret detection is best-effort, not a security guarantee**: heuristic-based and **may miss things**; re-check before committing/publishing.
- **No effectiveness promise**: see "An honest note on effectiveness" above; test data is observed under specific conditions and isn't a guarantee of fewer mistakes.
- **Provided "AS IS"**, without warranty of any kind. See [LICENSE](LICENSE).

## Credits & References
- **Evidence base**: [*How Many Instructions Can LLMs Follow at Once?* (IFScale, arXiv 2507.11538)](https://arxiv.org/abs/2507.11538) — the basis for silk-starry's "shorter is stronger, put the most important rules first" (even the best frontier model follows only 68% at 500 instructions, and is biased toward earlier ones).
- **Official basis**: [Anthropic · Claude Code Best Practices](https://code.claude.com/docs/en/best-practices) and the official memory docs (CLAUDE.md / Auto Memory mechanics, the admission test, "treat it like code").
- **Philosophy**: community deep-dives on Claude Code's memory mechanism — the four-layer load order, instruction budget, the config-roles model, and "maintain CLAUDE.md like code".
- **Method inspiration**: [Andrej Karpathy's coding guidelines](https://github.com/multica-ai/andrej-karpathy-skills), HumanLayer's *Writing a good CLAUDE.md*; and [Khazix's neat-freak skill](https://github.com/KKKKhazix/khazix-skills) (which inspired the third-layer docs/README sync idea).

## License
[MIT](LICENSE) · Free to use; PRs welcome.
