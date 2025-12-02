
# **ARA6D – Modular Robot Control System**

**ARA6D** is a modular, hardware-agnostic control framework for building custom robotic systems.
It integrates:

* Stepper motor control via **Moonraker/Klipper G-code**
* Joint-level control abstractions
* Sensor feedback pipelines (AS5600 encoders via ESP32 + I²C mux)
* Real-time communication over serial, USB, and HTTP APIs

ARA6D is the foundation for your future **6-DOF robotic arm**, including high-level planning, movement primitives, and closed-loop feedback.

---

##  **Features**

### **1. G-code Control Layer**

Low-level motion interface:

* Fully supports **Moonraker HTTP API**
* Supports USB serial G-code (Klipper, Marlin, etc.)
* Relative & absolute moves
* Optional `FAKE_HOME` injections
* Verbose and dry-run modes
* Configurable feed rates

This layer ensures **hardware-compatible movement** across boards and firmware types.

---

### **2. Joint-Level Control Layer**

Abstractions for robot joints:

* Simple helper functions like `move_joint(x_deg)`
* Converts angles → G-code → Moonraker commands
* Ready to expand into:

  * Kinematics
  * Trajectory planning
  * Workspace constraints
  * Safety limits

This becomes the “brain” of your robot.

---

### **3. Sensor Layer (AS5600 Magnetic Encoders)**

Clean, filtered joint angle feedback:

* Multi-sensor support via **PCA9548A I²C multiplexer**
* Communicates from ESP32 → Raspberry Pi over serial
* Provides:

  * Raw angle
  * Calibrated angle
  * EMA-filtered angle
* Detects **offline/online** sensors
* Built for high-rate, real-time feedback

This forms the basis for **closed-loop motor control** later.

---

### **4. Modular Architecture**

ARA6D is structured like a real robotics framework:

* `gcode/` → Device control
* `controls/` → Joints, IK, motion
* `sensors/` → Encoder processing
* `src/robot_main.py` → Top-level robot class
* `save_old/` → Safe archive for legacy prototypes

Clean, extensible, and scalable.

---

##  **Directory Structure**

```
G_scripts/
├── README.md
│
├── gcode/
│   ├── gcode_moonraker_sender.py       # Movement via Moonraker HTTP API
│   └── gcode_serial_sender.py          # Movement via raw USB serial
│
├── src/
│   ├── robot_main.py                   # Main robot orchestration layer
│   │
│   ├── controls/
│   │   ├── gcode_joint_sender.py       # Joint-level movement helpers
│   │   └── motion_planning.py          # (Future) IK / trajectory planning
│   │
│   └── sensors/
│       ├── read_as5600_angles.py       # Reads multiplexer + AS5600 chain
│       └── test.py
│
├── save_old/
│   ├── gcode_moonraker_senderk_save.py # Archived early experiment
│   └── robot_main.py                   # Archived prototype
```

---

##  **Requirements**

### **Raspberry Pi Side**

* Python 3
* `requests` (for Moonraker HTTP)
* `pyserial` (for serial G-code & ESP32 input)

Install dependencies:

```bash
pip install pyserial requests
```

### **ESP32 Side**

* AS5600 sensors
* PCA9548A multiplexer
* Custom firmware (`main.cpp` in separate repo)
* Serial connection to Raspberry Pi

---

##  **Quick Start**

### **Run a test joint move (Moonraker):**

```bash
python3 gcode/gcode_moonraker_sender.py --x 5 --relative --verbose
```

### **Issue a fake home:**

```bash
python3 gcode/gcode_moonraker_sender.py --command "FAKE_HOME"
```

### **Read sensor data:**

```bash
python3 src/sensors/read_as5600_angles.py
```

---

##  **Planned Features**

* Full forward & inverse kinematics
* Robot calibration system
* Signed joint limits
* Trajectory smoothing (S-curves, jerk-limited motion)
* Safety systems:

  * Soft stops
  * Motor current monitoring
  * E-stop hooks
* Real-time sensor fusion
* ROS2 bridge package
* Web UI for teleoperation

---

##  **Project Goals**

1. Build a **functional 6-DOF robotic arm**
2. Achieve **closed-loop control** using encoder feedback
3. Integrate **machine learning models** (vision + planning)
4. Create an **open modular robotics stack** that supports:

   * Raspberry Pi
   * Jetson Orin
   * ESP32
   * Moonraker/Klipper hardware

This project is stepping toward your larger **Intuitive AI** framework.

---

##  License

(Choose one: MIT recommended)

Example:

```
MIT License — see LICENSE file for details.
```

---

##  Contributing

For now, this is a personal development repo, but structure is kept clean to allow future collaboration.

---

##  Inspiration & Credits

* Klipper
* Moonraker
* Parol6 Robotic Arm
* AS5600 documentation
* Your hands-on engineering + robotics background

