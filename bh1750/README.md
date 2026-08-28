# ESP32 BH1750FVI Dashboard Skill

[Chinese version](README.zh-CN.md)

This skill builds a complete ESP32-C6 and BH1750FVI ambient-light monitor: wiring, project generation, Zero EMQX or custom MQTT broker setup, firmware flashing, serial verification, and a local or Cloudflare-hosted live dashboard.

## Usage

```sh
git clone https://github.com/emqx/thing-loom.git
cd thing-loom/bh1750
codex
```

Then ask:

```text
Build me an ambient-light monitor.
```

The agent guides the wiring, collects secrets through hidden local prompts, uses Zero EMQX or a custom broker, flashes the firmware, verifies a real lux message with MQTTX, and opens the dashboard.

![BH1750FVI to ESP32-C6 wiring](assets/bh1750fvi-esp32-c6-wiring.svg)

Follow the labels printed on the sensor module:

| BH1750FVI module | ESP32-C6 |
|---|---|
| `VCC` | `5V` |
| `SDA` / `DAT` | `GPIO 6` |
| `SCL` | `GPIO 7` |
| `GND` | `GND` |
| `ADDR` / `ADD` | `GND` or unconnected (`0x23`) |

The documented breakout module accepts a 5V input. A bare BH1750FVI IC does not. Before power-up, confirm that a different board regulates or level-shifts SDA and SCL to 3.3V; never apply 5V logic to ESP32 GPIO.

## Delivery and security

- **Local HTML:** open the generated `web/public/index.html`; Cloudflare is not used.
- **Remote URL:** deploy the same page with Cloudflare Workers Static Assets using a least-privilege API token entered through a hidden prompt.

Zero EMQX remains the default. With `--broker custom`, the scaffold prompts locally for the broker host, device port and `mqtt`/`mqtts` protocol, username, hidden password, and separate `ws://`/`wss://` dashboard URL. MQTTX validates both endpoints before any project files are written; remote dashboards require `wss://`. The scaffold stores Wi-Fi, MQTT, and optional Cloudflare credentials in `data/<project>/.env` with mode `600`. Generated projects and all `.env` files are ignored by Git.

A remote static page necessarily contains its disposable Zero MQTT WSS credential. Use this only for an isolated demo. Private or production dashboards need an authenticated backend and durable messaging service.

## Default hardware and tooling

- ESP32-C6-DevKitC-1
- BH1750FVI breakout module
- USB-C data cable
- 2.4 GHz Wi-Fi

The skill installs only missing components:

```sh
brew install arduino-cli
brew install emqx/mqttx/mqttx-cli
arduino-cli core install esp32:esp32
arduino-cli lib install BH1750 PubSubClient
```

MQTTX verifies the real message over MQTTS without `--insecure`. The firmware uses the system CA bundle and synchronizes its clock before the TLS handshake.
