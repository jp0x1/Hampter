# Hampter Link MVP Walkthrough

# Hardware For Demo:
Raspberry Pi with AX210 wifi chip, communication output interface is LCD display using i2c SDA/SCL lines with 2 pull down resistors, and speaker output.

## Overview
Phase 1 MVP of the Hampter Link peer-to-peer system. This version establishes an Ad-Hoc/Mesh link using Intel AX210 hardware (or standard Wi-Fi) and creates a secure QUIC tunnel for text communication.

## Installation
```bash
# 1. Install System Dependencies
# (Ensure python3-venv, build-essentials, libffi-dev are installed)

# 2. Setup Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Run
sudo ./venv/bin/python main.py
```
*Note: `sudo` is required for network configuration.*

## Features Implemented
### 1. Networking Layer
*   **Automatic Scanning**: Detects wireless interfaces and highlights AX210 cards.
*   **Ad-Hoc Mode**: Configures IBSS mode automatically via `setup_network.sh`.
*   **Discovery**: Uses UDP Broadcasting (Port 5566) to find peers on the local link.

### 2. Protocol Layer
*   **QUIC**: Custom `HampterProtocol` built on `aioquic`.
*   **Secure**: Auto-generates TLS 1.3 self-signed certificates on first launch.
*   **Multiplexing**: Supports control streams and chat streams (ready for video).

### 3. User Interface
*   **Cyber Dashboard**: A `rich`-based TUI with live telemetry.
*   **Status Panel**: Shows connection state, Peer IP, and Ping.
*   **Log Panel**: Displays incoming messages and system events.

## Usage
1.  Run the app on **Node A** and **Node B**.
2.  Select the interface (e.g., `wlan0`).
3.  Enter unique IPs (e.g., `10.0.0.1` and `10.0.0.2`).
4.  The system will auto-discover and link up.
5.  Type in the console to chat!
