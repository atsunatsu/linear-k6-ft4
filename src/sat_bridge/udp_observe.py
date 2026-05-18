from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import subprocess


PORT_KEYS = {
    "UDPServerPort": "wsjtx_udp_server_port",
    "SendSymPort": "wsjtx_send_sym_port",
    "N1MMServerPort": "wsjtx_n1mm_server_port",
    "PTTMethod": "wsjtx_ptt_method",
    "Rig": "wsjtx_rig",
}


@dataclass(slots=True)
class UdpBinding:
    protocol: str
    local_host: str
    local_port: int
    pid: int
    process_name: str


@dataclass(slots=True)
class UdpObservation:
    wsjtx_ini_path: str
    wsjtx_ini_values: dict[str, str]
    interesting_ports: list[int]
    bindings: list[UdpBinding]


def default_wsjtx_ini_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    return Path(local_app_data) / "WSJT-X" / "WSJT-X.ini"


def parse_wsjtx_ini(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in PORT_KEYS:
            values[PORT_KEYS[key]] = _normalize_ini_value(key, value.strip())
    return values


def _normalize_ini_value(key: str, value: str) -> str:
    if key == "PTTMethod":
        upper = value.upper()
        if "VOX" in upper:
            return "VOX"
    return value


def parse_netstat_udp(text: str, interesting_ports: set[int]) -> list[tuple[str, str, int, int]]:
    bindings: list[tuple[str, str, int, int]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("UDP"):
            continue
        parts = re.split(r"\s+", line)
        if len(parts) < 4:
            continue
        local_address = parts[1]
        pid_text = parts[-1]
        parsed = _parse_host_port(local_address)
        if parsed is None:
            continue
        host, port = parsed
        if port not in interesting_ports:
            continue
        try:
            pid = int(pid_text)
        except ValueError:
            continue
        bindings.append(("UDP", host, port, pid))
    return bindings


def _parse_host_port(value: str) -> tuple[str, int] | None:
    if value.startswith("[") and "]:" in value:
        host, port_text = value.rsplit("]:", 1)
        host = host.lstrip("[")
    elif ":" in value:
        host, port_text = value.rsplit(":", 1)
    else:
        return None

    try:
        return host, int(port_text)
    except ValueError:
        return None


def lookup_process_names(pids: set[int]) -> dict[int, str]:
    names: dict[int, str] = {}
    for pid in sorted(pids):
        process_name = _lookup_process_name_with_tasklist(pid)
        if process_name == "unknown":
            process_name = _lookup_process_name_with_powershell(pid)
        names[pid] = process_name
    return names


def _lookup_process_name_with_tasklist(pid: int) -> str:
    completed = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout.strip()
    if not output or output.startswith("INFO:") or "Access denied" in output:
        return "unknown"
    fields = _parse_tasklist_csv_line(output)
    return fields[0] if fields else "unknown"


def _lookup_process_name_with_powershell(pid: int) -> str:
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            f"(Get-Process -Id {pid} -ErrorAction SilentlyContinue).ProcessName",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout.strip()
    if not output:
        return "unknown"
    return output


def _parse_tasklist_csv_line(line: str) -> list[str]:
    if not line:
        return []
    matches = re.findall(r'"([^"]*)"', line)
    return matches


def collect_udp_observation(wsjtx_ini_path: Path, interesting_ports: list[int]) -> UdpObservation:
    ini_values = parse_wsjtx_ini(wsjtx_ini_path)
    completed = subprocess.run(
        ["netstat", "-ano", "-p", "udp"],
        capture_output=True,
        text=True,
        check=False,
    )
    parsed_bindings = parse_netstat_udp(completed.stdout, set(interesting_ports))
    process_names = lookup_process_names({pid for _, _, _, pid in parsed_bindings})
    bindings = [
        UdpBinding(
            protocol=protocol,
            local_host=host,
            local_port=port,
            pid=pid,
            process_name=process_names.get(pid, "unknown"),
        )
        for protocol, host, port, pid in parsed_bindings
    ]
    bindings.sort(key=lambda item: (item.local_port, item.pid, item.local_host))
    return UdpObservation(
        wsjtx_ini_path=str(wsjtx_ini_path),
        wsjtx_ini_values=ini_values,
        interesting_ports=interesting_ports,
        bindings=bindings,
    )


def render_text_report(observation: UdpObservation) -> str:
    lines = [
        f"WSJT-X ini: {observation.wsjtx_ini_path}",
        f"interesting_ports: {', '.join(str(port) for port in observation.interesting_ports)}",
        "wsjtx_ini_values:",
    ]
    if observation.wsjtx_ini_values:
        for key, value in observation.wsjtx_ini_values.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- <not found>")

    lines.append("udp_bindings:")
    if observation.bindings:
        for binding in observation.bindings:
            lines.append(
                f"- {binding.local_host}:{binding.local_port} "
                f"pid={binding.pid} process={binding.process_name}"
            )
    else:
        lines.append("- <no matching UDP bindings>")
    return "\n".join(lines)


def write_json_report(path: Path, observation: UdpObservation) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "wsjtx_ini_path": observation.wsjtx_ini_path,
        "wsjtx_ini_values": observation.wsjtx_ini_values,
        "interesting_ports": observation.interesting_ports,
        "bindings": [asdict(binding) for binding in observation.bindings],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Observe WSJT-X / DigiManager UDP ports before loopback capture."
    )
    parser.add_argument(
        "--wsjtx-ini",
        default=str(default_wsjtx_ini_path()),
        help="Path to WSJT-X.ini",
    )
    parser.add_argument(
        "--ports",
        default="2237,4532,5957",
        help="Comma-separated UDP ports to inspect.",
    )
    parser.add_argument(
        "--json",
        default="logs/udp-port-observation.json",
        help="Where to write the JSON observation report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    interesting_ports = [int(item.strip()) for item in args.ports.split(",") if item.strip()]
    observation = collect_udp_observation(Path(args.wsjtx_ini), interesting_ports)
    print(render_text_report(observation))
    write_json_report(Path(args.json), observation)
    print(f"JSON report written to {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
