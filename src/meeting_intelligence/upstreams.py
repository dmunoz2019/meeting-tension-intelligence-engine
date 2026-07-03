from __future__ import annotations

import tomllib
from dataclasses import asdict, dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_ALLOWED_MODES = {"dependency", "adapter", "service", "reference"}
_ALLOWED_LICENSES = {"Apache-2.0", "BSD-2-Clause", "MIT", "PostgreSQL"}


@dataclass(frozen=True, slots=True)
class UpstreamSpec:
    name: str
    repository: str
    ref: str
    license: str
    mode: str
    package: str | None
    extra: str | None
    purpose: str
    weights_policy: str = "runtime-private-cache"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_manifest_path() -> Path:
    return Path(str(files("meeting_intelligence").joinpath("vendor/upstreams.toml")))


def load_upstreams(path: Path | None = None) -> list[UpstreamSpec]:
    manifest = path or default_manifest_path()
    payload = tomllib.loads(manifest.read_text(encoding="utf-8"))
    rows = payload.get("upstream", [])
    if not isinstance(rows, list):
        raise ValueError("manifest must contain [[upstream]] entries")
    return [UpstreamSpec(**row) for row in rows]


def validate_upstreams(specs: list[UpstreamSpec]) -> list[str]:
    errors: list[str] = []
    names: set[str] = set()
    for spec in specs:
        if spec.name in names:
            errors.append(f"duplicate upstream name: {spec.name}")
        names.add(spec.name)
        parsed = urlparse(spec.repository)
        if parsed.scheme != "https" or parsed.netloc != "github.com":
            errors.append(f"{spec.name}: repository must be an https://github.com URL")
        if spec.license not in _ALLOWED_LICENSES:
            errors.append(f"{spec.name}: unsupported license {spec.license}")
        if spec.mode not in _ALLOWED_MODES:
            errors.append(f"{spec.name}: unsupported mode {spec.mode}")
        if not spec.ref.strip():
            errors.append(f"{spec.name}: ref is required")
        if spec.weights_policy != "runtime-private-cache":
            errors.append(
                f"{spec.name}: weights_policy must keep weights in a private runtime cache"
            )
    return errors


def vendor_plan(specs: list[UpstreamSpec]) -> list[dict[str, str]]:
    return [
        {
            "name": spec.name,
            "mode": spec.mode,
            "ref": spec.ref,
            "repository": spec.repository,
            "command": (
                f"git clone --filter=blob:none --depth 1 --branch {spec.ref} "
                f"{spec.repository}.git .vendor-cache/{spec.name}"
            ),
        }
        for spec in specs
    ]
