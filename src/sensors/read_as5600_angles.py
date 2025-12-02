#!/usr/bin/env python3
"""
read_as5600_angles.py

Simple serial reader for the ESP32 + AS5600 + I2C mux setup.
It just opens the serial port, reads lines, and prints them.

Later, we can add parsing and structure (e.g. a dict of joint angles),
but for now we just want clean, continuous readings.
"""

import sys
import time

try:
    import serial  # pyserial
except ImportError:
    sys.exit(
        "pyserial is required. Install with:\n"
        "  python3 -m pip install --user pyserial\n"
    )


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 read_as5600_angles.py /dev/ttyUSB2")
        sys.exit(1)

    port = sys.argv[1]
    baud = 115200

    print(f"Opening {port} at {baud} baud...")
    try:
        ser = serial.Serial(port, baudrate=baud, timeout=1.0)
    except serial.SerialException as exc:
        sys.exit(f"Could not open serial port {port}: {exc}")

    print("Connected. Press Ctrl+C to stop.\n")

    try:
        while True:
            line = ser.readline().decode("utf-8", errors="replace").strip()
            if not line:
                # no data this cycle
                continue

            # For now, just print the raw ESP32 line
            print(line)

            # If you want to slow things slightly:
            # time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()

