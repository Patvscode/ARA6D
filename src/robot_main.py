#!/usr/bin/env python3
"""
robot_main.py

Interactive “base” console for your robot.

- Lets you move joints J1..J6 interactively.
- Under the hood, calls gcode_joint_sender.py (which talks to Moonraker/Klipper).
- Designed to be easy to extend with more actions later.

Usage (from ~/Documents/G_scripts):

    python3 robot_main.py

Then follow the on-screen menu.
"""

from __future__ import annotations

import subprocess
from typing import Optional


# Default Moonraker connection (adjust if needed)
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 7125


def prompt_float(label: str) -> Optional[float]:
    """
    Prompt the user for a float, allow empty input to mean 'None'.
    """
    while True:
        raw = input(f"{label} (blank for none): ").strip()
        if raw == "":
            return None
        try:
            return float(raw)
        except ValueError:
            print("  ! Please enter a number or leave blank.")


def prompt_yes_no(label: str, default: bool = True) -> bool:
    """
    Simple yes/no prompt.

    default=True -> [Y/n]
    default=False -> [y/N]
    """
    if default:
        suffix = " [Y/n]: "
    else:
        suffix = " [y/N]: "

    while True:
        raw = input(label + suffix).strip().lower()
        if raw == "" and default is not None:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  ! Please answer y or n (or press Enter for default).")


def move_joints_interactive() -> None:
    """
    Interactively ask for joint offsets and send a single move via gcode_joint_sender.py.
    """
    print("\n=== Joint Move ===")
    print("Enter the amount you want to move each joint (relative units).")
    print("Leave a field empty if you don't want to move that joint.\n")

    # Ask for J1..J6 offsets. Each one maps to a joint/axis in gcode_joint_sender.py.
    j1 = prompt_float("J1")
    j2 = prompt_float("J2")
    j3 = prompt_float("J3")
    j4 = prompt_float("J4")
    j5 = prompt_float("J5")
    j6 = prompt_float("J6")

    # If no joints specified, just bail out
    if all(v is None for v in (j1, j2, j3, j4, j5, j6)):
        print("No joints specified, nothing to do.\n")
        return

    # Options that toggle relative moves and optional FAKE_HOME injection.
    relative = prompt_yes_no("Use relative move (G91/G90)?", default=True)
    fake_home_first = prompt_yes_no("Send FAKE_HOME before move?", default=True)

    # Feed rate controls move speed in mm/min for the generated G1 command.
    while True:
        raw_feed = input("Feed rate (mm/min, default 400): ").strip()
        if raw_feed == "":
            feed = 400.0
            break
        try:
            feed = float(raw_feed)
            break
        except ValueError:
            print("  ! Please enter a number or press Enter for default.")

    # Build the command to call gcode_joint_sender.py as a subprocess.
    # This keeps the CLI in one place and reuses its Moonraker logic.
    cmd = [
        "python3",
        "gcode_joint_sender.py",
        "--host",
        DEFAULT_HOST,
        "--port",
        str(DEFAULT_PORT),
        "--feed",
        str(feed),
        "--verbose",
    ]

    # Add joint flags for any joints that were specified
    if j1 is not None:
        cmd += ["--j1", str(j1)]
    if j2 is not None:
        cmd += ["--j2", str(j2)]
    if j3 is not None:
        cmd += ["--j3", str(j3)]
    if j4 is not None:
        cmd += ["--j4", str(j4)]
    if j5 is not None:
        cmd += ["--j5", str(j5)]
    if j6 is not None:
        cmd += ["--j6", str(j6)]

    if relative:
        cmd.append("--relative")
    if fake_home_first:
        cmd.append("--fake-home-first")

    print("\nAbout to run:")
    print("  " + " ".join(cmd))
    confirm = prompt_yes_no("Proceed with this move?", default=True)
    if not confirm:
        print("Move cancelled.\n")
        return

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"\n! Error running gcode_joint_sender.py: {exc}\n")
    else:
        print("\nMove command sent.\n")


def main_menu() -> None:
    """
    Simple text menu that can be expanded as you add more robot functions.
    """
    while True:
        print("=== Robot Main ===")
        print("1) Move joints (J1..J6)")
        # Future options can go here, e.g.:
        # print("2) Run pre-defined motion sequence")
        # print("3) Home / fake-home routine")
        print("q) Quit")
        choice = input("Select an option: ").strip().lower()

        if choice == "1":
            move_joints_interactive()
        elif choice in ("q", "quit", "exit"):
            print("Exiting robot_main.")
            break
        else:
            print("Unknown option, please choose again.\n")


if __name__ == "__main__":
    main_menu()
