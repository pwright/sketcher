# Domain Documentation

This repo uses a **single-context** layout.

## Layout

- **`CONTEXT.md`** at repo root — domain concepts, key patterns, constraints
- **`docs/adr/`** — architecture decision records (one ADR per file, numbered `0001-...`, `0002-...`, etc.)

## Consumer rules

**When to read `CONTEXT.md`:**
- Before making architectural decisions
- When you need to understand domain concepts or terminology
- When the user asks about "how we do X here" or "why we chose Y"

**When to read ADRs:**
- When you encounter patterns that seem unusual and want to understand the rationale
- When you're about to reverse a prior decision
- When the user asks for the history of a design choice

**When NOT to read:**
- For routine edits to files you already understand
- When the user's request is self-contained and doesn't touch architectural boundaries

## Creating new ADRs

When you make a significant architectural decision during a session, offer to capture it as an ADR. Use the [MADR format](https://adr.github.io/madr/):

```markdown
# [short title]

## Context and Problem Statement

[What decision are we making and why?]

## Considered Options

* Option 1
* Option 2

## Decision Outcome

Chosen option: "[option]", because [justification].

### Consequences

* Good: ...
* Bad: ...
```

Number the file sequentially (`docs/adr/0001-...`).
