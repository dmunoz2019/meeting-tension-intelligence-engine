# Contributing

Contributions are welcome.

## Rules

- Use only synthetic or properly licensed public examples.
- Never submit real customer transcripts or model artifacts derived from private meetings.
- Add tests for new detection rules.
- Explain whether a feature increases recall, precision, or interpretability.
- Keep automatic decisions conservative for agreements, scope changes, and system gaps.

## Development

```bash
pip install -e '.[dev,nlp,mcp]'
pytest
ruff check .
```
