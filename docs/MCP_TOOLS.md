# MCP Tools

The optional MCP server currently exposes:

- `meetings_list`: lists transcript files in the private runtime directory.
- `meeting_analyze`: analyzes one transcript, stores a private JSON result, and returns bounded evidence excerpts.
- `meeting_get_batch`: returns a resumable batch of findings.

## Recommended production additions

- `finding_review`
- `findings_query`
- `finding_link`
- `project_get_taxonomy`
- `report_export`

Write tools should require validation and preserve append-only audit history.
