# Approved upstream integrations

The project does not fork or embed upstream source by default. The integration model is:

- **dependency**: normal Python dependency
- **adapter**: imported lazily behind a local protocol
- **service**: deployed independently and accessed through an adapter
- **reference**: architecture/reference implementation, not installed by default

The source of truth is `src/meeting_intelligence/vendor/upstreams.toml`.

## Why no large source vendoring?

Large source copies create security, licensing, and update debt. The manifest and local
adapters preserve replaceability while allowing a controlled `.vendor-cache/` checkout
for audits or emergency patching.

## Weight policy

Model weights and embeddings are data artifacts, not source dependencies. They belong
in a private runtime cache, MinIO bucket, or model registry. They are never committed to
this public repository.
