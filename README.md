# Meeting Tension Intelligence Engine

Privacy-first engine for extracting tension, dissatisfaction, risks, requirements,
scope concerns, possible system gaps, agreements, and unresolved questions from
meeting transcripts.

## Current capabilities

- Timestamped Markdown and plain-text parsing.
- Runtime adaptive regex discovery.
- Contextual Spanish sentiment and conversational acts.
- Separate dissatisfaction and project-risk scores.
- Optional hashed NLP classification.
- JSON and CSV exports.
- Optional MCP server.

## State-of-the-art architecture branch

This branch adds the first evidence-based architecture slice:

- immutable source artifacts and evidence spans
- claims with assertion mode, authority, temporal validity, and review state
- model-run provenance with configuration hashes
- ports for ASR, diarization, alignment, embeddings, reranking, PII, and telemetry
- lazy faster-whisper, pyannote.audio, and Presidio adapters
- BM25 + dense retrieval fused with Reciprocal Rank Fusion
- optional cross-encoder reranking
- classification, calibration, retrieval, and evidence-span metrics
- approved upstream registry with refs, licenses, extras, and private weight policy

See [docs/STATE_OF_ART_ARCHITECTURE.md](docs/STATE_OF_ART_ARCHITECTURE.md) and
[docs/UPSTREAMS.md](docs/UPSTREAMS.md).

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,nlp]'
```

Optional integrations:

```bash
pip install -e '.[audio-faster-whisper]'
pip install -e '.[diarization]'
pip install -e '.[privacy]'
pip install -e '.[retrieval-bge,postgres]'
pip install -e '.[observability,mlops]'
```

## Upstream management

Upstream source and model weights are not committed. Inspect the approved integration
manifest with:

```bash
meeting-intelligence upstreams verify
meeting-intelligence upstreams list
meeting-intelligence upstreams plan
```

## Quick start

```bash
meeting-intelligence analyze examples/synthetic_meeting.md --output-dir output
```

## Privacy

No real transcript, customer-specific learned phrase, embedding, or private model weight
belongs in this repository. Runtime caches and optional source audits live outside Git.

## Quality

```bash
ruff check .
pytest -q
meeting-intelligence upstreams verify
python -m build
```

## License

Apache License 2.0. Optional upstreams and model weights retain their own licenses.
