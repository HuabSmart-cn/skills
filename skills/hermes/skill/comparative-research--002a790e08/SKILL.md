---
name: comparative-research
description: "Research subjects BEFORE drawing comparisons or making claims. Applies when users ask 'how does X compare to Y', 'what's the difference between X and Y', 'is X better than Y', or any question requiring factual knowledge about a specific product, tool, entity, or concept."
tags: [research, comparison, web-search, accuracy]
triggers:
  - "user asks to compare two or more things"
  - "user asks 'what is X' about a specific product/tool/entity"
  - "user asks 'how does X differ from Y'"
  - "question requires factual knowledge about a named entity you're not certain about"
---

# Comparative Research

## Core Principle

**Research FIRST, compare SECOND.** Never speculate about a product, tool, or entity when you can search for current facts. Wrong assumptions in comparisons erode trust faster than most other errors.

## Workflow

### Step 1: Identify what you actually know vs. assume
Before responding to any comparative or "what is X" question:
- Do you have **verified, current** knowledge of the subject?
- Could the product/tool have changed significantly since your training data?
- Are there **multiple things with the same name** (disambiguation)?

If uncertain on any of these → search first.

### Step 2: Research the subject
Use available tools to gather facts:
- `web_search` or `web_extract` for general information
- `browser_*` tools for interactive pages
- Wikipedia API for structured lookups:
  ```
  curl -s "https://en.wikipedia.org/api/rest_v1/page/summary/TOPIC"
  curl -s "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=QUERY&format/json"
  ```
- Official documentation/sites for authoritative details

Key facts to gather:
- **What it actually is** (not what you assume)
- **When it was released/updated** (products evolve)
- **Current capabilities and limitations**
- **Disambiguation** — does the name refer to multiple things?

### Step 3: Compare with verified facts
Only after research:
- State what each subject **actually is** (with sources if possible)
- Compare on **concrete, verifiable dimensions**
- Acknowledge uncertainty where it exists
- Use tables for structured comparison when helpful

## Pitfalls

1. **Assuming you know what "X" is** — Names are ambiguous. "Codex" could mean the 2021 language model OR the 2025 AI agent. "Copilot" could mean GitHub Copilot, Microsoft Copilot, or others. Always verify.

2. **Stale knowledge** — AI products change fast. What was true 6 months ago may be wrong today. When comparing AI tools/models, prefer searching for current information.

3. **Lengthy speculative answers** — A long comparison based on assumptions is worse than a short "let me research that first." Users notice when you're guessing.

4. **Searching after already committing to claims** — If you've already stated "X does Y" and then search proves you wrong, you've lost credibility. Search before making claims.

5. **Ignoring disambiguation** — Wikipedia and other sources often return disambiguation pages. Don't pick the first meaning; clarify which one the user means if ambiguous.

## User Preference: Chinese Language

When the user writes in Chinese, respond in Chinese. Research can be done in English for better coverage, but the final comparison should be in the user's language.

## Example Flow

**User**: "你和codex有什么不一样"

**Wrong approach**: Immediately launch into a speculative comparison table.

**Right approach**:
1. Recognize "codex" is ambiguous — could be multiple products
2. Search: `curl -s "https://en.wikipedia.org/w/api.php?action=query&titles=OpenAI_Codex&prop=extracts&exintro=true&format=json"`
3. Discover there are TWO products: Codex language model (2021) and Codex AI agent (2025)
4. Research each one's current capabilities
5. THEN provide a grounded comparison with verified facts
