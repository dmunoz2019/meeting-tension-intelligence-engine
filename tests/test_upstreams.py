from meeting_intelligence.upstreams import load_upstreams, validate_upstreams, vendor_plan


def test_upstream_manifest_is_valid_and_private_weight_safe() -> None:
    specs = load_upstreams()
    assert len(specs) >= 8
    assert not validate_upstreams(specs)
    assert all(spec.weights_policy == "runtime-private-cache" for spec in specs)
    assert {spec.name for spec in specs} >= {
        "faster-whisper",
        "whisperx",
        "pyannote-audio",
        "presidio",
        "flag-embedding",
    }


def test_vendor_plan_uses_local_ignored_cache() -> None:
    plan = vendor_plan(load_upstreams())
    assert all(".vendor-cache/" in row["command"] for row in plan)
