# Hampter Link

**Secure, Off-Grid, High-Bandwidth P2P Multimedia System**

A peer-to-peer communication system built on Raspberry Pi 5 with Intel AX210 Wi-Fi 6E, designed for secure, off-grid multimedia streaming and messaging.

---

## Features

- 🔐 **Secure Communication**: TLS 1.3 encryption with mutual authentication
- 📡 **Wi-Fi 6E Support**: High-bandwidth 6GHz operation with 2.4GHz fallback
- 🎥 **Real-time Video**: Low-latency H.264 streaming between nodes
- 💬 **Instant Messaging**: Prioritized text communication lane
- 📊 **Hardware Telemetry**: Remote monitoring of CPU, battery, and temperature
- 🖥️ **Modern GUI**: Dark-themed command dashboard

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HAMPTER LINK                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │   GUI       │    │  Protocol   │    │  Hardware   │          │
│  │  Dashboard  │◄──►│   Engine    │◄──►│  Drivers    │          │
│  └─────────────┘    └──────┬──────┘    └─────────────┘          │
│                            │                                     │
│                     ┌──────┴──────┐                              │
│                     │    QUIC     │                              │
│                     │  Transport  │                              │
│                     └──────┬──────┘                              │
│                            │                                     │
│                     ┌──────┴──────┐                              │
│                     │  Intel AX210 │                             │
│                     │   Wi-Fi 6E   │                             │
│                     └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

### Protocol Lanes

| Lane | Name      | Priority | Purpose                    |
|------|-----------|----------|----------------------------|
| 0    | Heartbeat | Highest  | Ping, telemetry, keep-alive |
| 1    | Chatter   | High     | Text messages, commands    |
| 2    | Flow      | Medium   | Real-time audio/video      |
| 3    | Haul      | Low      | Bulk file transfers        |

---

## Hardware Requirements

- **Raspberry Pi 5** (8GB recommended)
- **Intel AX210 Wi-Fi 6E Module** with M.2 E-Key HAT
- **USB Power Bank** (5000mAh+ for portable operation)
- **SparkFun LCD** (optional, I2C 16x2)
- **PWM Fan** (optional, 5V GPIO-controlled)

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/youruser/HampterLink.git
cd HampterLink
```

### 2. Install System Dependencies
```bash
chmod +x install_deps.sh
./install_deps.sh
```

### 3. Generate Certificates
```bash
source venv/bin/activate
python gen_certs.py
```

### 4. Configure the Node
Edit `config.json` to set your node type (A or B) and network settings:
```json
{
    "node_type": "A",
    "network": {
        "ip_A": "192.168.100.1",
        "ip_B": "192.168.100.2",
        "port": 4433,
        "interface": "wlan0"
    }
}
```

### 5. Run the Application
```bash
source venv/bin/activate
python main.py
```

---

## Project Structure

```
HampterLink/
├── main.py                 # Application entry point
├── config.json             # Node configuration
├── gen_certs.py            # Certificate generator
├── install_deps.sh         # Dependency installer
├── requirements.txt        # Python dependencies
├── certs/                  # TLS certificates
└── src/
    ├── gui/
    │   ├── main_window.py  # GUI dashboard
    │   └── styles.py       # QSS theme
    ├── protocol/
    │   ├── quic_engine.py  # QUIC transport layer
    │   ├── packet_def.py   # Lane/packet definitions
    │   └── security.py     # TLS configuration
    ├── hardware/
    │   ├── fan_ctrl.py     # PWM fan controller
    │   ├── lcd_drv.py      # LCD display driver
    │   ├── telemetry.py    # System stats
    │   └── wifi_monitor.py # WiFi RSSI/band monitor
    └── media/
        └── streamer.py     # GStreamer video handler
```

---

## Development

### Running in Mock Mode

The application gracefully degrades when hardware is unavailable:
- **No GPIO**: Fan control uses mock
- **No I2C**: LCD uses mock
- **No GStreamer**: Video uses mock
- **No WiFi interface**: RSSI uses simulated data

### Running Tests
```bash
source venv/bin/activate
python -m pytest tests/
```

---

## License

MIT License - See LICENSE file for details.

---

**Project Hampter Link** - *Secure mesh communication for the modern burrow.*
# Hampter
