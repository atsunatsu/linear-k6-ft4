from __future__ import annotations

from dataclasses import dataclass
import binascii
import json
from pathlib import Path
import struct
from typing import Any

from sat_bridge.reverse_tools import PACK_OBFUSCATION, analyze_firmware_bin, try_unpack_uvk5_packed_firmware


KNOWN_ANCHORS = ("DIG.M", "DIG+", "LOCK", "FREQ:%u.%05u", " CEC_0.3Q")
WINDOW_RADIUS = 48


@dataclass(slots=True)
class PatchWorkspace:
    firmware_path: Path
    source_sha256: str
    embedded_version: str
    raw_size_bytes: int
    anchors: list[dict[str, Any]]
    manifest_template: dict[str, Any]


def repack_uvk5_packed_firmware(raw_bytes: bytes, embedded_version: str) -> bytes:
    version_block = embedded_version.encode("ascii", errors="ignore")[:16].ljust(16, b"\x00")
    inserted = raw_bytes[:0x2000] + version_block + raw_bytes[0x2000:]
    packed = bytes(
        byte ^ PACK_OBFUSCATION[index % len(PACK_OBFUSCATION)]
        for index, byte in enumerate(inserted)
    )
    crc = binascii.crc_hqx(packed, 0).to_bytes(2, "little")
    return packed + crc


def build_patch_workspace(firmware_path: Path) -> PatchWorkspace:
    firmware_summary = analyze_firmware_bin(firmware_path)
    unpack = try_unpack_uvk5_packed_firmware(firmware_path.read_bytes())
    if not unpack.get("ok"):
        raise ValueError("Could not unpack the real 0.3q packed firmware.")

    raw_bytes = unpack["raw_bytes"]
    anchors = collect_anchor_windows(raw_bytes, firmware_summary.get("interesting_string_offsets", []))
    manifest_template = build_manifest_template(firmware_summary, anchors)
    return PatchWorkspace(
        firmware_path=firmware_path,
        source_sha256=str(firmware_summary["sha256"]),
        embedded_version=str(unpack.get("embedded_version", "")),
        raw_size_bytes=len(raw_bytes),
        anchors=anchors,
        manifest_template=manifest_template,
    )


def collect_anchor_windows(raw_bytes: bytes, interesting_offsets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    anchors: list[dict[str, Any]] = []
    seen_offsets: set[int] = set()
    for item in interesting_offsets:
        text = str(item.get("text", ""))
        if text not in KNOWN_ANCHORS:
            continue
        offset = int(item["offset"])
        if offset in seen_offsets:
            continue
        seen_offsets.add(offset)
        start = max(0, offset - WINDOW_RADIUS)
        end = min(len(raw_bytes), offset + WINDOW_RADIUS)
        window = raw_bytes[start:end]
        anchors.append(
            {
                "text": text,
                "offset": offset,
                "encoding": item.get("encoding", "ascii"),
                "window_start": start,
                "window_end": end,
                "window_hex": window.hex(" "),
                "raw_offset_references": find_raw_offset_references(raw_bytes, offset),
            }
        )
    anchors.sort(key=lambda item: int(item["offset"]))
    return anchors


def find_raw_offset_references(raw_bytes: bytes, offset: int, *, limit: int = 16) -> list[int]:
    needle = struct.pack("<I", offset)
    hits: list[int] = []
    search_from = 0
    while len(hits) < limit:
        found = raw_bytes.find(needle, search_from)
        if found < 0:
            break
        hits.append(found)
        search_from = found + 1
    return hits


def build_manifest_template(firmware_summary: dict[str, Any], anchors: list[dict[str, Any]]) -> dict[str, Any]:
    unpack = firmware_summary.get("unpack", {})
    version_string = str(unpack.get("embedded_version") or "")
    anchor_index = {anchor["text"]: anchor for anchor in anchors}
    return {
        "source_firmware_sha256": firmware_summary["sha256"],
        "source_embedded_version": version_string,
        "output_embedded_version": "CEC_0.3QP1",
        "notes": [
            "Fill in enabled patch entries only after you have validated the real lock-frequency or FT4 gate offsets.",
            "This template is generated from the real packed firmware and is intentionally narrow.",
        ],
        "patches": [
            {
                "name": "digital_mode_retune_gate_candidate",
                "enabled": False,
                "kind": "replace_bytes",
                "offset": None,
                "expect_hex": "",
                "replace_hex": "",
                "anchor_hint": anchor_index.get("DIG.M", {}).get("offset"),
                "notes": "Use this after you identify the code path that forces digital-mode frequency back to a fixed value.",
            },
            {
                "name": "ft4_tx_gate_candidate",
                "enabled": False,
                "kind": "replace_bytes",
                "offset": None,
                "expect_hex": "",
                "replace_hex": "",
                "anchor_hint": anchor_index.get("DIG+", {}).get("offset"),
                "notes": "Use this after you identify the branch that allows FT8 TX but blocks FT4 TX.",
            },
            {
                "name": "patched_version_banner",
                "enabled": False,
                "kind": "replace_ascii",
                "offset": anchor_index.get(" CEC_0.3Q", {}).get("offset"),
                "expect_ascii": " CEC_0.3Q",
                "replace_ascii": " CEC_3QPB",
                "notes": "Optional visual marker so testers can confirm they booted the patched bench firmware.",
            },
        ],
    }


def apply_patch_manifest(
    firmware_path: Path,
    manifest_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    firmware_bytes = firmware_path.read_bytes()
    unpack = try_unpack_uvk5_packed_firmware(firmware_bytes)
    if not unpack.get("ok"):
        raise ValueError("Could not unpack the real 0.3q packed firmware.")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_sha = str(manifest.get("source_firmware_sha256", ""))
    actual_sha = analyze_firmware_bin(firmware_path)["sha256"]
    if expected_sha and expected_sha != actual_sha:
        raise ValueError("Source firmware SHA256 does not match the manifest.")

    raw_bytes = bytearray(unpack["raw_bytes"])
    applied: list[dict[str, Any]] = []
    enabled_patches = [patch for patch in manifest.get("patches", []) if patch.get("enabled")]
    if not enabled_patches:
        raise ValueError("No enabled patches found in the manifest.")

    for patch in enabled_patches:
        applied.append(_apply_single_patch(raw_bytes, patch))

    output_embedded_version = str(manifest.get("output_embedded_version") or unpack.get("embedded_version") or "CEC_0.3QP1")
    packed = repack_uvk5_packed_firmware(bytes(raw_bytes), output_embedded_version)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(packed)

    return {
        "source_firmware": str(firmware_path),
        "manifest": str(manifest_path),
        "output_firmware": str(output_path),
        "applied_patches": applied,
        "output_embedded_version": output_embedded_version,
        "output_size_bytes": len(packed),
    }


def write_patch_workspace(workspace: PatchWorkspace, output_dir: Path, *, manifest_path: Path | None = None) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "patch-workspace.json"
    md_path = output_dir / "patch-workspace.md"
    manifest_target = manifest_path or (output_dir.parent / "patches" / "real-03q-bench.template.json")
    manifest_target.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "firmware_path": str(workspace.firmware_path),
        "source_sha256": workspace.source_sha256,
        "embedded_version": workspace.embedded_version,
        "raw_size_bytes": workspace.raw_size_bytes,
        "anchors": workspace.anchors,
        "manifest_template_path": str(manifest_target),
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_patch_workspace_markdown(payload), encoding="utf-8")
    manifest_target.write_text(json.dumps(workspace.manifest_template, indent=2, ensure_ascii=False), encoding="utf-8")
    return json_path, md_path, manifest_target


def render_patch_workspace_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Real 0.3q Patch Workspace",
        "",
        f"- firmware_path: {payload['firmware_path']}",
        f"- source_sha256: {payload['source_sha256']}",
        f"- embedded_version: {payload['embedded_version']}",
        f"- raw_size_bytes: {payload['raw_size_bytes']}",
        f"- manifest_template_path: {payload['manifest_template_path']}",
        "",
        "## Anchor Windows",
    ]
    for anchor in payload.get("anchors", []):
        lines.extend(
            [
                f"### {anchor['text']}",
                f"- offset: {anchor['offset']}",
                f"- encoding: {anchor['encoding']}",
                f"- window: {anchor['window_start']}..{anchor['window_end']}",
                f"- raw_offset_references: {anchor['raw_offset_references'] or 'none'}",
                f"- window_hex: `{anchor['window_hex']}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _apply_single_patch(raw_bytes: bytearray, patch: dict[str, Any]) -> dict[str, Any]:
    kind = str(patch.get("kind"))
    offset = patch.get("offset")
    if offset is None:
        raise ValueError(f"Patch {patch.get('name')} is missing an offset.")
    offset = int(offset)

    if kind == "replace_bytes":
        expect = bytes.fromhex(str(patch.get("expect_hex", "")).strip())
        replace = bytes.fromhex(str(patch.get("replace_hex", "")).strip())
        if not expect or not replace:
            raise ValueError(f"Patch {patch.get('name')} must define expect_hex and replace_hex.")
        if raw_bytes[offset : offset + len(expect)] != expect:
            raise ValueError(f"Patch {patch.get('name')} did not match expected bytes at offset {offset}.")
        raw_bytes[offset : offset + len(expect)] = replace
        return {"name": patch.get("name"), "kind": kind, "offset": offset, "size": len(replace)}

    if kind == "replace_ascii":
        expect_ascii = str(patch.get("expect_ascii", ""))
        replace_ascii = str(patch.get("replace_ascii", ""))
        expect = expect_ascii.encode("ascii")
        replace = replace_ascii.encode("ascii")
        if len(expect) != len(replace):
            raise ValueError(f"Patch {patch.get('name')} replace_ascii must keep the same length.")
        if raw_bytes[offset : offset + len(expect)] != expect:
            raise ValueError(f"Patch {patch.get('name')} did not match expected ASCII at offset {offset}.")
        raw_bytes[offset : offset + len(expect)] = replace
        return {"name": patch.get("name"), "kind": kind, "offset": offset, "size": len(replace)}

    raise ValueError(f"Unsupported patch kind: {kind}")
