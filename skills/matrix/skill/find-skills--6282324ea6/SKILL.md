---
name: find-skills
description: Make sure you have the right skill for the job BEFORE starting any substantial deliverable — build a website, write tests, set up deployment, design a UI, integrate an API, scrape data, edit media, automate a workflow, and so on. The moment a task lands, reflexively check whether an existing workspace/department skill covers it; if none does and the work is specialized or recurring, find and install a proven community skill to raise delivery quality. The user does NOT need to mention skills — they'll just say "make me a website" or "add CI"; treat that as your cue to line up the best capability. Reuse what's installed first; reach for the community only for a real gap.
category: development
symbolName: sparkle.magnifyingglass
seedVersion: 2
---

# Find Skills

Skills are how you deliver better work. Before you start any substantial task,
make sure you're equipped with the right one — pulled from what's already
installed when possible, or from the open ecosystem (https://skills.sh) when
there's a genuine gap.

This is a **reflex, not a feature the user requests.** The user is skill-agnostic
— they say "build me a landing page" or "set up tests," and it's on you to
quietly line up the best capability for it. They should never have to know a
skill exists, ask for one, or approve the *checking*. The only thing that
surfaces to them is a better result (and a quick heads-up before you install
anything new — see Step 4).

The bias is **reuse first, install last.** A redundant or low-quality community
skill is worse than none: it fragments triggers, confuses routing, and adds
unvetted instructions. So check what you have, and only go shopping for a real,
specialized gap.

## When This Reflex Fires

The trigger is **a task arriving that you're about to act on** — not the user
saying the word "skill." When you pick up work that is specialized, domain-heavy,
or likely to recur, pause for a beat and ask: *is there a skill that would let me
do this better?* Examples of the kinds of asks that should fire it:

- "Make me a website / landing page" → look for web-design, React/Next.js,
  frontend skills
- "Add tests" / "set up CI" → testing, e2e, ci-cd skills
- "Deploy this" → deployment, docker, infra skills
- "Design the UI" / "make it look good" → design-system, accessibility skills
- "Pull data from X" / "integrate Y's API" → scraping, that API's skill
- Any time you catch yourself about to hand-roll a non-trivial, packaged-feeling
  workflow from scratch

Skip it for genuinely trivial, one-off asks (a quick edit, a single question),
and for anything an installed skill already obviously handles — in that case
just use the skill silently and get on with the work.

## Step 0 — Check What You Already Have (mandatory, silent)

This whole step is invisible to the user. Before searching the community, prove
to yourself the gap is real:

1. **List what's already installed.** Look in both scopes:
   - Workspace skills: `skills/<name>/SKILL.md` (from the department cwd:
     `../../skills/`)
   - Department skills: `departments/<id>/skills/<name>/SKILL.md`
   ```bash
   ls -1 ../../skills/ 2>/dev/null; ls -1 skills/ 2>/dev/null
   ```
2. **Read the description of any plausible match.** A skill's `description:`
   frontmatter is its contract. Skim the ones whose names or domains are even
   loosely related — the capability you want is often bundled into a broader
   skill (e.g. media work lives in `media-generation`, repeatable workflows in
   `skill-creator`).
3. **Decide honestly:** does an existing skill cover this, even imperfectly? If
   yes, **use it** — adapt your approach to the tool you already have, or refine
   that skill via `skill-creator` rather than installing a competitor.

Only when nothing existing fits do you proceed below.

## Step 1 — Understand the Need

Pin down three things so your search is precise:

1. **Domain** — React, testing, deployment, design, a named API, etc.
2. **Specific task** — writing tests, animating UI, reviewing PRs, generating a
   changelog…
3. **Recurrence** — is this common enough that a battle-tested skill likely
   exists? One-offs don't justify an install.

## Step 2 — Check the Leaderboard, Then Search

Start with the most-installed, most-trusted options before casting a wide net.

- **Leaderboard first:** https://skills.sh ranks skills by total installs.
  Official sources dominate the top — `vercel-labs/agent-skills` (React,
  Next.js, web design), `anthropics/skills` (frontend design, document
  processing). If one obviously covers the need, you're done searching.
- **Then search by keyword** if the leaderboard doesn't cover it:
  ```bash
  npx skills find "<specific keywords>"     # e.g. "react performance", "pr review"
  ```
  Specific beats broad: `react testing` over `testing`. Try synonyms
  (`deploy` → `deployment` → `ci-cd`) if the first query is dry.

If `npx skills` isn't available in this environment, fall back to browsing the
leaderboard directly (`curl -sL https://skills.sh`) to identify candidates.

## Step 3 — Verify Quality Before Recommending Anything

**Never recommend a skill on search results alone.** Gate every candidate:

- **Install count** — prefer 1K+. Be skeptical below 100.
- **Source reputation** — `vercel-labs`, `anthropics`, `microsoft` and similar
  official orgs are trustworthy; unknown authors are not.
- **Repo health** — a source repo with <100 stars deserves real skepticism.
- **Trigger overlap** — would this skill's triggers collide with an existing
  one? If so, prefer extending the existing skill instead.

## Step 4 — The One Time You Surface It: Before Installing

Everything up to here was silent. Installing a new community skill is the **only**
moment you involve the user — because it adds unvetted third-party instructions to
their workspace, which deserves a yes. Keep it to one quick line, framed around the
*task*, not the machinery:

> "To do this well I'd like to pull in <skill> (<source>, <N> installs) — it
> handles <capability>. OK to add it?"

Don't lecture them about the skill system; they just want the website. Show the
candidate(s) — name, what it does, install count + source, skills.sh link — and
get a go-ahead before installing anything new.

When approved, install so that **this workspace can actually load it**. Neo reads
skills from `skills/<name>/` (workspace) and
`departments/<id>/skills/<name>/` (department) — *not* from the global
`npx skills -g` location, so a global install would be invisible here. Install
into the workspace layout instead:

1. Fetch the skill folder from its source repo (the skills.sh entry names it as
   `owner/repo@skill`; files live under that repo on GitHub). At minimum grab
   `SKILL.md`, plus any `scripts/`, `references/`, or `assets/` it ships.
2. Write them into a new `skills/<name>/` directory (workspace scope, shared
   across departments) or `departments/<id>/skills/<name>/` if the capability is
   team-specific.
3. Keep the source's `name:` frontmatter so the skill keeps its identity, and
   verify the description still reads as a clear WHAT + WHEN. If the import
   needs reshaping to fit this workspace, route through the `skill-creator`
   skill.

Example of presenting a find before installing:

```
Found a strong match: "react-best-practices" from vercel-labs/agent-skills —
React/Next.js performance guidelines from Vercel Engineering. (185K installs)

Want me to install it into this workspace's skills/ ? It'll be available to
every department.
```

## When No Skill Fits

If nothing existing covers it and the community has no trustworthy match, don't
make a production of it — just do the task with your general capabilities and
move on. Only mention the skill search if it's genuinely relevant (e.g. the user
asked, or it's a recurring need worth capturing). If the work will recur, it's
worth quietly authoring a workspace skill for it via `skill-creator` — a vetted
in-house skill beats a shaky community one.

## The One Rule

This is a reflex, not a conversation. On every substantial task: silently check
what's installed, use it if it fits, and only when there's a real gap go find a
proven community skill — surfacing exactly one thing to the user, the ask for
permission to install. They said "make me a website"; your job is to quietly show
up with the right tools and deliver a better result. When in doubt, build it
in-house with `skill-creator` instead.
