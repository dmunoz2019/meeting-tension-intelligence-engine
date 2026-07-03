# State-of-the-Art Architecture

This branch starts the migration from a transcript sentiment utility to an
**evidence-based meeting intelligence and project assurance engine**.

## Design principles

1. **Evidence before interpretation.** Every claim references immutable evidence spans.
2. **Ports before vendors.** ASR, diarization, alignment, embeddings, reranking, PII,
   storage, telemetry, and orchestration are interfaces.
3. **Adapter-first vendoring.** Upstream source and weights are not copied into Git.
4. **Hybrid retrieval.** BM25 and dense retrieval are fused with Reciprocal Rank Fusion;
   an optional cross-encoder reranks a small candidate set.
5. **Human review for high-impact claims.** Agreements, scope changes, and system gaps
   remain candidates until validated.
6. **Versioned provenance.** Model runs, configuration hashes, evidence checksums, and
   temporal validity are first-class domain data.

## New domain layer

`meeting_intelligence.domain` defines source artifacts, evidence spans, speaker
identity and authority, claims, assertion modes, review states, relations, and model
runs. It has no dependency on Hugging Face, a database, or an orchestration framework.

## New ports and adapters

`meeting_intelligence.ports` defines contracts for ASR, diarization, forced alignment,
embeddings, reranking, PII redaction, and telemetry.

Initial lazy adapters:

- `FasterWhisperASR`
- `PyannoteDiarizer`
- `PresidioPIIRedactor`

## Hybrid retrieval

`meeting_intelligence.retrieval.HybridRetriever` implements BM25 plus dense retrieval,
Reciprocal Rank Fusion, and optional cross-encoder reranking. The in-memory
implementation is the reference contract for a later PostgreSQL FTS + pgvector adapter.

## Evaluation

The evaluation package includes precision, recall, F1, accuracy, Brier score, expected
calibration error, Recall@K, reciprocal rank, and evidence-span intersection over union.

## Next architectural slices

1. Canonical audio → ASR → diarization → alignment pipeline.
2. PostgreSQL FTS + pgvector repository and hybrid search adapter.
3. Presidio privacy gateway before external inference or export.
4. Authority-aware decisions and agreement validation.
5. Temporal project memory with supersession and contradiction relations.
6. OpenTelemetry spans and MLflow experiment lineage.
7. ERP-specific requirement, fit-gap, change-request, and UAT generation.
