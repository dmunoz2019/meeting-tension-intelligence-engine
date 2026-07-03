# Meeting Tension Intelligence Engine

Open-source Python engine for extracting tension, dissatisfaction, risks, requirements, scope concerns, possible system gaps, agreements, and unresolved questions from meeting transcripts.

The engine is designed for consulting, ERP implementation, project governance, discovery workshops, and other high-stakes meetings where a simple summary is not enough.

## What it does

- Parses timestamped Markdown or plain-text transcripts.
- Discovers meeting-specific phrases at runtime using contrastive n-grams.
- Generates adaptive Python and POSIX-compatible regex patterns.
- Scores dissatisfaction separately from project risk.
- Detects conversational acts such as concern, rejection, requirement, commitment, question, warning, and alignment.
- Uses contextual Spanish sentiment with negation, intensifiers, hedging, and hypothetical-example discounting.
- Optionally adds hashed TF-IDF-style features and linear weak-supervision classification without publishing a vocabulary.
- Keeps raw transcripts and project-specific model packs outside the public repository.
- Exposes an optional MCP server for interactive analysis by an AI client.

## Privacy-first design

This repository contains no private transcripts, customer names, learned phrases, embeddings, or model weights derived from confidential meetings.

Project-specific artifacts belong in a private runtime volume:

```text
/data/private/
├── transcripts/
├── adaptive_rules/
├── model_packs/
├── embeddings/
└── review_feedback/
```

See [PRIVACY.md](PRIVACY.md).

## Architecture

```text
Transcript
   ↓
Timestamp parser and sentence segmentation
   ↓
Universal high-recall seeds
   ↓
Runtime contrastive phrase discovery
   ↓
Adaptive regex and productive templates
   ↓
Contextual sentiment and conversational acts
   ↓
Optional hashed vector classifier
   ↓
Tension, dissatisfaction, risk, and review queue
   ↓
JSON / CSV / MCP tools
```

## Install

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

For NLP/vector features:

```bash
pip install -e '.[nlp]'
```

For MCP:

```bash
pip install -e '.[mcp]'
```

For development:

```bash
pip install -e '.[dev,nlp,mcp]'
```

## Quick start

Analyze the included synthetic transcript:

```bash
meeting-intelligence analyze \
  examples/synthetic_meeting.md \
  --output-dir output
```

Generate adaptive rules only:

```bash
meeting-intelligence discover \
  examples/synthetic_meeting.md \
  --output output/adaptive_rules.json
```

Run the MCP server:

```bash
meeting-intelligence serve-mcp --data-dir /data/private
```

## Example output

```json
{
  "sentence": "Me preocupa que el calendario no cubra todas las validaciones.",
  "act": "CONCERN",
  "sentiment": "NEGATIVE",
  "dissatisfaction_score": 71.4,
  "project_risk_score": 62.1,
  "tension_level": "HIGH",
  "certainty": "ASSERTED",
  "review_required": true
}
```

## Important limitations

- Regex and weak supervision create candidates; they do not prove a contractual agreement or system gap.
- Sentiment is assigned to an utterance unless speaker attribution is reliable.
- A phrase such as “the system does not do that” may be a hypothetical example rather than a confirmed limitation.
- Contradictions, agreements, and scope changes require contextual review.
- Internal validation against weak labels is not equivalent to evaluation against human annotations.

## Roadmap

- Speaker normalization and authority profiles.
- Cross-meeting contradiction and supersession graph.
- Requirement and UAT candidate generation.
- Private online learning from reviewer corrections.
- PostgreSQL/pgvector persistence adapter.
- Google Sheets and NocoDB export adapters.

## License

Apache License 2.0. See [LICENSE](LICENSE).
