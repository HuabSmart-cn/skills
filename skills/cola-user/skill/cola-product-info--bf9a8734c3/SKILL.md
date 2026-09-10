---
name: cola-product-info
description: "The entry point to everything Cola knows about itself. Through the documentation index it can reach every official doc: features (项目 / Projects（原 Coding Cola）, C 空间 / C Space, 智能闹钟 / Smart Alarms, Cola Skill, 通用邮箱 / Universal Email, Google 日历 / Google Calendar, Outlook 日历 / Outlook Calendar, 外部应用 / External Apps, 觉知 / Awareness and 心迹 / imprints, voice input, channels and plugins), configuration (account, Token Plan, models, memory, network, shortcuts), developer integrations (MCP, CLI, Plugin SDK), and product facts (version, updates / changelog / 更新日志 with per-version release notes, platforms, terms, privacy). Use this for ANY question about Cola itself: how a feature works, how to configure something, what a term means, what Cola can or cannot do, how it works internally, what changed in an update, or account / billing / feedback questions. Read this before answering from memory or searching the web."
homepage: https://colaos.ai/
metadata:
  category: system
---

# Cola Product Information

## Answering questions about Cola

The documentation site is the source of truth for features, concepts, configuration,
integrations, and plugin development. Don't answer those from memory, and don't reach for
web search first.

1. **Fetch `https://docs.colaos.ai/llms.txt`** — a ~4.5 KB index of every page in both
   languages, one line each: `[Title](/zh/<slug>): description`. It is regenerated on every
   docs build, so it is never stale.
2. **Pick the page by its description, then read it** at `/zh/<slug>/` or `/en/<slug>/`,
   matching the user's language. The index lists both — don't hand a Chinese user an `/en/`
   link. The trailing slash is required.

`https://docs.colaos.ai/llms-full.txt` returns every page's full text at once.

### Rules

- Only use slugs that came from llms.txt — **never construct a docs URL yourself**. There is
  no `/docs/` path segment; `https://docs.colaos.ai/zh/docs/` is an empty redirect shell.
- **Never conclude a feature doesn't exist from anything you failed to find.** Three
  different misses, same rule:
  - An empty or very short fetch → you used the wrong URL; re-check llms.txt.
  - No matching page in llms.txt → the docs don't cover it.
  - The page loaded but doesn't mention it → the docs don't cover that detail.

  In all three, report what the *documentation* says or doesn't say — never that Cola can't
  do it: say "the docs don't specifically cover this," not "Cola doesn't support it." Cola's
  implementation runs well ahead of its docs; MCP support, for instance, is fully implemented. The only thing that
  justifies "Cola doesn't support X" is a doc that explicitly says so.
- Once you've reported that the docs don't cover it, you may search the web.
- One llms.txt fetch per conversation is enough.
- If llms.txt is unreachable (offline, proxy failure, site down), fall back to
  `references/docs-index.md` in this skill — a snapshot taken when this app version was
  built — and tell the user the live docs may have changed since.

## Official links

- Website https://colaos.ai/ · Download https://colaos.ai/download
- Terms https://colaos.ai/terms · Privacy https://colaos.ai/privacy

## Versions & updates

- **Read the running version from the `COLA_APP_VERSION` environment variable.** Do not hunt
  through `Info.plist` with `mdfind` / `find` / `defaults read`. If it isn't set, say you
  can't determine the version and point the user to Settings / About.
- **For "what changed / what's new" questions** — 更新内容、版本历史、某版本改了什么 —
  read the changelog page on the docs site (listed in llms.txt as 更新日志 / Changelog).
  It carries every version's release notes, newest first.
