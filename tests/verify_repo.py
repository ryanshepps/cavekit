#!/usr/bin/env python3
"""Local verification runner for Cavekit install surfaces."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CheckFailure(RuntimeError):
    pass


def section(title: str) -> None:
    print(f"\n== {title} ==")


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_synced_files() -> None:
    section("Synced Files")

    for skill in ["backprop", "build", "caveman", "check", "spec"]:
        source = ROOT / "skills" / skill / "SKILL.md"
        copy = ROOT / "plugins" / "ck" / "skills" / skill / "SKILL.md"
        ensure(copy.exists(), f"Codex plugin skill copy missing: {skill}")
        ensure(
            copy.read_text(encoding="utf-8") == source.read_text(encoding="utf-8"),
            f"Codex plugin skill copy mismatch: {skill}",
        )

    source_format = ROOT / "FORMAT.md"
    copy_format = ROOT / "plugins/ck/FORMAT.md"
    ensure(copy_format.exists(), "Codex plugin FORMAT.md copy missing")
    ensure(
        copy_format.read_text(encoding="utf-8") == source_format.read_text(encoding="utf-8"),
        "Codex plugin FORMAT.md copy mismatch",
    )

    print("Codex skill and FORMAT.md copies OK")


def verify_manifests() -> None:
    section("Manifests")

    claude_plugin = read_json(ROOT / ".claude-plugin/plugin.json")
    claude_marketplace = read_json(ROOT / ".claude-plugin/marketplace.json")
    codex_plugin = read_json(ROOT / "plugins/ck/.codex-plugin/plugin.json")
    codex_marketplace = read_json(ROOT / ".agents/plugins/marketplace.json")

    ensure(isinstance(claude_plugin, dict), "Claude plugin manifest must be an object")
    ensure(isinstance(claude_marketplace, dict), "Claude marketplace manifest must be an object")
    ensure(isinstance(codex_plugin, dict), "Codex plugin manifest must be an object")
    ensure(isinstance(codex_marketplace, dict), "Codex marketplace manifest must be an object")

    ensure(claude_plugin["name"] == "ck", "Claude plugin name must remain ck")
    ensure(codex_plugin["name"] == "ck", "Codex plugin name must be ck")
    ensure(codex_plugin["skills"] == "./skills/", "Codex plugin skills path must be ./skills/")

    ensure(codex_marketplace["name"] == "cavekit", "Codex marketplace name must be cavekit")
    ensure(
        codex_marketplace["interface"]["displayName"] == "Cavekit",
        "Codex marketplace display name must be Cavekit",
    )

    plugins = codex_marketplace["plugins"]
    ensure(len(plugins) == 1, "Codex marketplace must expose exactly one plugin")
    plugin = plugins[0]
    ensure(plugin["name"] == "ck", "Codex marketplace plugin name must be ck")
    ensure(
        plugin["source"] == {"source": "local", "path": "./plugins/ck"},
        "Codex marketplace source must point to ./plugins/ck",
    )
    ensure(
        plugin["policy"] == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "Codex marketplace policy must be AVAILABLE/ON_INSTALL",
    )
    ensure(plugin["category"] == "Coding", "Codex marketplace category must be Coding")

    print("Claude and Codex manifests OK")


def verify_codex_trigger_text() -> None:
    section("Codex Trigger Text")

    expected = {
        "spec": "/ck:spec",
        "build": "/ck:build",
        "check": "/ck:check",
    }
    for skill, trigger in expected.items():
        text = (ROOT / "plugins" / "ck" / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        ensure("Codex triggers:" in text, f"{skill} skill missing Codex trigger line")
        ensure(trigger in text, f"{skill} skill missing {trigger} trigger")
        ensure(f"use Cavekit {skill}" in text, f"{skill} skill missing natural-language Cavekit trigger")

    print("Codex slash and natural-language triggers OK")


def main() -> int:
    checks = [
        verify_synced_files,
        verify_manifests,
        verify_codex_trigger_text,
    ]

    try:
        for check in checks:
            check()
    except CheckFailure as exc:
        print(f"\nFAIL: {exc}", file=sys.stderr)
        return 1

    print("\nAll local verification checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
