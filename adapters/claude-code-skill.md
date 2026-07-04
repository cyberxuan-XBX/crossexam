# Adapter: /crossexam slash command for Claude Code

One-sentence panels from inside any Claude Code session. Create
`.claude/commands/crossexam.md` in your project (or `~/.claude/commands/`
for global):

```markdown
---
description: Run a CrossExam multi-model panel on a question and report the verdict
---
Run `cxam run "$ARGUMENTS"` in the project root (run `cxam setup` first if it
reports no seats). Stream progress. When it finishes, read _Msg/synthesis.md
and report back: (1) the consensus conclusions, (2) the disagreement table
verbatim — do not resolve disagreements yourself; they are the user's to judge.
```

Usage inside Claude Code:

```
/crossexam why does the nightly ETL double-count refunds?
```

The session becomes the moderator: it launches the panel (its own vendor's
tier trio by default, or whatever `cxam setup` configured), waits, and briefs
you on where the models agree and exactly where they don't.
