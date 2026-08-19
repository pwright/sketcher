# Issue Tracker

Issues for this repo live in **GitHub Issues** at `pwright/sketcher`.

## Creating issues

Use the `gh` CLI:

```bash
gh issue create --title "..." --body "..."
```

## Reading issues

```bash
gh issue list
gh issue view <number>
```

## Updating issues

```bash
gh issue edit <number> --add-label "..." --body "..."
gh issue comment <number> --body "..."
```

## PRs as a request surface

**Disabled.** External PRs are not automatically triaged as issues. If you want to include PRs in the triage queue, flip this flag to **Enabled** and add workflow rules below.
