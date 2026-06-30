# Maker/Checker Article Pipeline Example

## Goal

Produce a short article with separate generation and verification roles so the loop does not accept its own unchecked output.

## Agents

| Role | Responsibility | Must Not Do |
|:---|:---|:---|
| Maker | Draft the article from the brief and source notes | Score or approve the draft |
| Checker | Evaluate the draft against the rubric | Rewrite the whole article silently |
| Gate | Decide pass, retry, or stop | Change the scoring rubric mid-run |

## Rubric

| Dimension | Maximum |
|:---|:---:|
| Hook strength | 10 |
| Data support | 10 |
| Low AI flavor | 10 |
| Mobile readability | 10 |
| Interaction hook | 10 |

A draft passes at **40/50** or above. The loop stops after three failed rounds.

## Loop

1. Read the brief and source notes.
2. Maker drafts version `v1`.
3. Checker scores `v1` and returns structured feedback.
4. If the score is at least 40, the Gate marks the article as ready.
5. If the score is below 40, Maker revises using only the Checker feedback.
6. If `v3` still fails, stop and escalate to a human.

## State Updates

Record each attempt in `STATE.md`:

```markdown
## Current Run
- Status: running
- Current batch: article-2026-06-30

## Progress
| Metric | Value |
|--------|-------|
| Draft attempts | 2 |
| Checker passes | 0 |
| Checker failures | 2 |
```

## Hard Stops

- The Checker cannot access source notes.
- The Maker invents unsupported claims.
- The same failure appears in two consecutive revisions.
