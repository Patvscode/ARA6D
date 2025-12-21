#!/usr/bin/env python3
"""
Utility script to send simple G-code moves to a Klipper-controlled device
via the Moonraker HTTP API.

This variant supports both raw axis controls (--x/--y/--z/--a/--b/--c)
and joint-style controls (--j1..--j6), plus an option to send FAKE_HOME
first (requires a FAKE_HOME macro in printer.cfg).

Example usages:

    # Dry run, show what would be sent
    python3 gcode_joint_sender.py --j1 5 --relative --dry-run

    # Send a small relative move on joint 1 (mapped to X),
    # automatically issuing FAKE_HOME first
    python3 gcode_joint_sender.py \
      --host localhost \
      --port 7125 \
      --j1 5 \
      --relative \
      --fake-home-first \
      --verbose
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
            Install it with:

                python3 -m pip install --user requests

            """
        )
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI args for Moonraker connection and joint/axis movement intent."""
    parser = argparse.ArgumentParser(
        description=(
            "Send a G-code script to Moonraker (/printer/gcode/script), "
            "with optional joint-style controls and FAKE_HOME."
        )
    )

    parser.add_argument(
        "--host",
        default="localhost",
        help="Moonraker host (default: localhost).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7125,
        help="Moonraker port (default: 7125).",
    )
    parser.add_argument(
        "--api-key",
        help="Optional Moonraker API key (sent as X-Api-Key header).",
    )

    parser.add_argument(
        "--command",
        help=(
            "Raw G-code line or multi-line script to send. "
            "If omitted, the script builds a G1 move using "
            "--x/--y/--z/--a/--b/--c and/or --j1..--j6 plus --feed."
        ),
    )
    parser.add_argument(
        "--relative",
        action="store_true",
        help="Wrap movement in G91/G90 so values are treated as offsets.",
    )
    parser.add_argument(
        "--feed",
        type=float,
        default=1200.0,
        help="Feed rate (used only when building a move command).",
    )

    # Axis-level arguments (X/Y/Z/A/B/C)
    for axis in ("x", "y", "z", "a", "b", "c"):
        parser.add_argument(
            f"--{axis}",
            type=float,
            help=f"Target for the {axis.upper()} axis (absolute or relative).",
        )

    # Joint-level arguments (J1..J6) for robotic-arm style control
    for idx in range(1, 7):
        parser.add_argument(
            f"--j{idx}",
            type=float,
            help=f"Target for joint J{idx} (mapped to an axis internally).",
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
        help="Send FAKE_HOME before the movement commands.",
    )
    return parser.parse_args()


def build_commands(args: argparse.Namespace) -> List[str]:
    """
    Build a list of G-code commands to send as a single Moonraker script.

    - If --command is provided, that is sent as-is (single logical script).
    - Otherwise, we construct a G1 move from axis and/or joint values.
    """
    if args.command:
        # Allow multi-line scripts; strip leading/trailing whitespace only.
        script = args.command.strip()
        # Split into lines so we can combine with G91/G90 if needed.
        return [line for line in script.splitlines() if line.strip()]

    # 1. Start with raw axis inputs (explicit axis flags take initial precedence).
    axis_values = {axis: getattr(args, axis) for axis in ("x", "y", "z", "a", "b", "c")}

    # 2. Map joints J1..J6 onto axes X/Y/Z/A/B/C
    #    J1 -> X, J2 -> Y, J3 -> Z, J4 -> A, J5 -> B, J6 -> C
    joint_to_axis = {
        "j1": "x",
        "j2": "y",
        "j3": "z",
        "j4": "a",
        "j5": "b",
        "j6": "c",
    }

    for joint, axis in joint_to_axis.items():
        joint_value = getattr(args, joint, None)
        if joint_value is not None:
            # Joint value overrides any direct axis value for that axis
            axis_values[axis] = joint_value

    # 3. Build the G1 movement line from final axis_values
    axes: List[str] = []
    for axis, value in axis_values.items():
        if value is not None:
            axes.append(f"{axis.upper()}{value:g}")

    if not axes:
        raise SystemExit(
            "No axis or joint values provided. "
            "Specify --command, axis flags (--x/--y/--z/--a/--b/--c) "
            "or joint flags (--j1..--j6)."
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
    timeout: float = 5.0,
) -> None:
    """
    Send the given G-code commands as a single script to Moonraker.

    This uses the /printer/gcode/script endpoint and joins the commands
    with newlines into one 'script' string.
    """
    url = f"http://{host}:{port}/printer/gcode/script"
    script = "\n".join(commands)

    headers = {}
    if api_key:
        headers["X-Api-Key"] = api_key

    if verbose:
        print(f"POST {url}")
        print("Payload script:")
        print(script)

    try:
        resp = requests.post(
            url,
            json={"script": script},
            headers=headers,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        sys.exit(f"HTTP error when talking to Moonraker: {exc!r}")

    if verbose:
        print("Moonraker response:")
        print(resp.text)

    if not resp.ok:
        sys.exit(f"Moonraker returned HTTP {resp.status_code}: {resp.text}")


def main() -> None:
    """Entry point that assembles a G-code script and posts it to Moonraker."""
    args = parse_args()
    commands = build_commands(args)

    # Optionally prepend FAKE_HOME
    if args.fake_home_first:
        commands = ["FAKE_HOME"] + commands

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
