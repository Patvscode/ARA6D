#!/usr/bin/env python3
"""
Utility script to send simple G-code moves to a controller over a serial port.

Place this file on the machine connected via USB/serial to your motion controller,
install pyserial (pip install pyserial), and run:
    python3 gcode_serial_sender.py --port /dev/ttyUSB0 --x 10 --y -2 --feed 1200
"""
from __future__ import annotations

import argparse
import sys
import textwrap
import time
from typing import Iterable, List

try:
    import serial  # type: ignore
except ImportError as exc:
    sys.exit(
        textwrap.dedent(
            """\
            pyserial is required for this tool.
            Install it with:  python3 -m pip install --user pyserial
            """
        )
    )

# Map a human-friendly option name to actual characters so we can
# interoperate with controllers that expect LF/CR/CRLF terminators.
LINE_ENDINGS = {
    "lf": "\n",
    "cr": "\r",
    "crlf": "\r\n",
}

def parse_args() -> argparse.Namespace:
    """Collect CLI parameters that define the serial connection + G-code to send."""
    parser = argparse.ArgumentParser(
        description="Send a single (optionally relative) movement command over serial."
    )
    parser.add_argument(
        "--port",
        default="/dev/ttyUSB0",
        help="Serial device path (e.g. /dev/ttyUSB0, /dev/ttyACM0, COM3).",
    )
    parser.add_argument(
        "--baud", type=int, default=115200, help="Controller baud rate (default: 115200)."
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Seconds to wait for controller responses.",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=0.1,
        help="Delay (seconds) between sending each G-code line.",
    )
    parser.add_argument(
        "--line-ending",
        choices=sorted(LINE_ENDINGS.keys()),
        default="lf",
        help="Line termination used by the controller firmware.",
    )
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
        help="Show the generated commands without touching the serial port.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print controller responses and additional progress information.",
    )
    return parser.parse_args()

def build_commands(args: argparse.Namespace) -> List[str]:
    """Translate CLI flags into a list of concrete G-code commands."""
    if args.command:
        return [args.command.strip()]

    axes = []
    for axis in ("x", "y", "z", "a", "b", "c"):
        value = getattr(args, axis)
        if value is not None:
            axes.append(f"{axis.upper()}{value:g}")

    if not axes:
        raise SystemExit(
            "No axis values provided. Specify --command or at least one of --x/--y/--z/--a/--b/--c."
        )

    move_cmd = f"G1 {' '.join(axes)} F{args.feed:g}"
    commands: List[str] = []
    if args.relative:
        commands.append("G91")
    commands.append(move_cmd)
    if args.relative:
        commands.append("G90")
    return commands

def send_commands(
    port: str,
    baud: int,
    timeout: float,
    commands: Iterable[str],
    wait_time: float,
    line_ending: str,
    verbose: bool,
) -> None:
    """Open the serial port and stream each command with optional logging."""
    with serial.Serial(port, baudrate=baud, timeout=timeout) as ser:
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        for cmd in commands:
            payload = (cmd + line_ending).encode("ascii")
            if verbose:
                print(f">> {cmd}")
            ser.write(payload)
            ser.flush()
            time.sleep(wait_time)
            if verbose:
                response = ser.readline().decode("utf-8", errors="replace").strip()
                if response:
                    print(f"<< {response}")

def main() -> None:
    """Entry point that orchestrates parsing, command building, and I/O."""
    args = parse_args()
    commands = build_commands(args)

    if args.dry_run:
        print("Commands that would be sent:")
        for cmd in commands:
            print(cmd)
        return

    try:
        send_commands(
            port=args.port,
            baud=args.baud,
            timeout=args.timeout,
            commands=commands,
            wait_time=args.wait,
            line_ending=LINE_ENDINGS[args.line_ending],
            verbose=True if args.verbose else False,
        )
    except serial.SerialException as exc:
        sys.exit(f"Serial error: {exc}")

if __name__ == "__main__":
    main()
