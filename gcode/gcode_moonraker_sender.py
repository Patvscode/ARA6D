#!/usr/bin/env python3
"""
Utility script to send simple G-code moves to a Klipper/Moonraker instance.

Instead of talking directly to the USB serial port, this script sends G-code
to Moonraker's HTTP API:

    POST /printer/gcode/script

Typical use (Raspberry Pi running Klipper + Moonraker):

    python3 gcode_moonraker_sender.py --x 5 --relative --verbose

This will build:

    G91
    G1 X5 F1200
    G90

and send it to http://localhost:7125/printer/gcode/script by default.
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from typing import Iterable, List

try:
    import requests  # type: ignore
except ImportError:
    sys.exit(
        textwrap.dedent(
            """\
            The 'requests' library is required for this tool.

            Install it with (recommended on Raspberry Pi OS):

                sudo apt update
                sudo apt install python3-requests
            """
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Send a single (optionally relative) movement command to "
            "a Klipper/Moonraker instance over HTTP."
        )
    )

    # Moonraker connection settings
    parser.add_argument(
        "--host",
        default="localhost",
        help="Moonraker host name or IP (default: localhost).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7125,
        help="Moonraker port (default: 7125).",
    )
    parser.add_argument(
        "--api-key",
        help="Moonraker API key, if authentication is enabled (optional).",
    )

    # G-code construction options (same semantics as the serial script)
    parser.add_argument(
        "--command",
        help=(
            "Raw G-code line to send. If omitted, the script builds a G1 move "
            "using --x/--y/--z/--a/--b/--c and --feed."
        ),
    )
    parser.add_argument(
        "--relative",
        action="store_true",
        help="Wrap movement in G91/G90 so axis values are treated as offsets.",
    )
    parser.add_argument(
        "--feed",
        type=float,
        default=1200.0,
        help="Feed rate (used only when building a move command).",
    )
    for axis in ("x", "y", "z", "a", "b", "c"):
        parser.add_argument(
            f"--{axis}",
            type=float,
            help=f"Target for the {axis.upper()} axis (absolute or relative).",
        )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the generated commands without contacting Moonraker.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print request details and Moonraker responses.",
    )

    parser.add_argument(
	"--fake-home-first",
	action="store_true",
	help="send FAKE_HOME before the movement commands.",
    )
    return parser.parse_args()


def build_commands(args: argparse.Namespace) -> List[str]:
    """
    Build a list of G-code lines based on CLI arguments.

    This mirrors the behavior of the serial-based sender so you can swap
    between them without changing your CLI usage.
    """
    if args.command:
        return [args.command.strip()]

    axes = []
    for axis in ("x", "y", "z", "a", "b", "c"):
        value = getattr(args, axis)
        if value is not None:
            axes.append(f"{axis.upper()}{value:g}")

    if not axes:
        raise SystemExit(
            "No axis values provided. Specify --command or at least one of "
            "--x/--y/--z/--a/--b/--c."
        )

    move_cmd = f"G1 {' '.join(axes)} F{args.feed:g}"
    commands: List[str] = []
    if args.relative:
        commands.append("G91")
    commands.append(move_cmd)
    if args.relative:
        commands.append("G90")
    return commands


def send_commands_moonraker(
    host: str,
    port: int,
    api_key: str | None,
    commands: Iterable[str],
    verbose: bool,
) -> None:
    """
    Send the given G-code commands to Moonraker via /printer/gcode/script.
    """
    base_url = f"http://{host}:{port}"
    url = f"{base_url}/printer/gcode/script"

    script = "\n".join(commands)

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-Api-Key"] = api_key

    payload = {"script": script}

    if verbose:
        print(f"POST {url}")
        print("Payload script:")
        print(script)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=5.0)
    except requests.RequestException as exc:
        sys.exit(f"HTTP error when talking to Moonraker: {exc}")

    if resp.status_code != 200:
        sys.exit(f"Moonraker error: HTTP {resp.status_code}: {resp.text}")

    if verbose:
        print("Moonraker response:")
        print(resp.text)


def main() -> None:
    args = parse_args()
    commands = build_commands(args)

    if args.dry_run:
        print("Commands that would be sent to Moonraker:")
        for cmd in commands:
            print(cmd)
        return

    send_commands_moonraker(
        host=args.host,
        port=args.port,
        api_key=args.api_key,
        commands=commands,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
