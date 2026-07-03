# Security Policy

## Reporting a vulnerability

Please report vulnerabilities privately to the repository owner rather than opening a public issue containing exploit details or private data.

## Security principles

- Transcript text is untrusted input.
- File paths are resolved inside configured data directories.
- The MCP server exposes no shell execution tool.
- Raw transcripts are not returned unless explicitly enabled.
- Findings preserve source hashes and bounded evidence excerpts.
- Write operations use explicit validation and append-only audit records.
