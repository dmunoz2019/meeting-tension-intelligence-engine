# Upstream vendor policy

This project uses an **adapter-first vendor strategy**.

- Upstream source trees are not copied into this repository.
- Model weights are never committed.
- `src/meeting_intelligence/vendor/upstreams.toml` records the approved repository,
  reference, SPDX license, integration mode, Python extra, and private-cache policy.
- Optional local source checkouts belong under `.vendor-cache/`, which is ignored.
- Every adapter must have contract tests using fakes so CI does not download weights.
- A separate integration workflow may download approved weights into an ephemeral cache.

Use:

```bash
meeting-intelligence upstreams verify
meeting-intelligence upstreams list
meeting-intelligence upstreams plan
```
