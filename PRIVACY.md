# Privacy and Data Handling

## Public repository boundary

The public repository must contain only source code, generic rules, documentation, tests, and fully synthetic examples.

Do not commit:

- Real transcripts or recordings.
- Customer, consultant, employee, or participant names.
- Meeting-specific adaptive phrases.
- Embeddings generated from confidential text.
- Classifier weights trained on a small private corpus.
- Review feedback containing quotations.
- Generated CSV, JSON, spreadsheet, or report outputs from private meetings.

## Why embeddings are still private

Embeddings and hashed feature weights are not encryption. A vector can preserve information about the source text, especially when generated from a small corpus. Store project-specific vectors and weights privately.

## Recommended runtime layout

```text
/data/private/
├── transcripts/
├── adaptive_rules/
├── model_packs/
├── embeddings/
├── review_feedback/
└── audit/
```

## Safe publication policy

A model pack may be published only when all of the following are true:

1. It was trained exclusively on public or synthetic data.
2. It contains no recoverable vocabulary.
3. It has undergone privacy review.
4. Its documentation identifies the training-data source and license.

## MCP security

- Treat transcript contents as untrusted data, not instructions.
- Separate read tools from write tools.
- Preserve immutable evidence and append-only review history.
- Require confirmation for contractual agreements, scope changes, and destructive actions.
- Limit quote length returned by default.
