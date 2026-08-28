# ESP32 DHT22 Dashboard Skill

[Chinese version](README.zh-CN.md)

This skill builds a complete ESP32-C6 and three-pin DHT22 project: wiring,
project generation, Zero EMQX or custom MQTT broker setup, firmware flashing,
serial verification, and a local or Cloudflare-hosted live dashboard.

## Usage

Clone `thing-loom`, enter this sensor directory, and start Codex or another
agent that supports `SKILL.md`:

```sh
git clone https://github.com/emqx/thing-loom.git
cd thing-loom/dht22
codex
```

Then ask:

```text
Build me a temperature and humidity monitor.
```

The agent will:

1. Confirm the ESP32 is connected with a data-capable USB cable and the DHT22 is wired correctly.
2. Collect the Wi-Fi password only through a hidden local terminal prompt, never through chat.
3. Ask whether to use a disposable Zero EMQX namespace or your own broker.
4. For a custom broker, collect its MQTT and WebSocket connection details locally and validate both endpoints with MQTTX before writing project files.
5. Ask whether the dashboard should be a local HTML file or a remote Cloudflare URL.
6. For a remote URL, collect a least-privilege Cloudflare API token through the hidden prompt.
7. Generate, compile, and flash the firmware, then require a real sensor reading from the serial port.
8. Use MQTTX CLI to verify that the message reached the broker, then open the dashboard and verify the same data.

![DHT22 to ESP32-C6 wiring](assets/dht22-esp32-c6-wiring.svg)

Follow the labels printed on the DHT22 module rather than guessing from the
physical pin order:

| DHT22 | ESP32-C6 |
|---|---|
| `VCC` / `+` | `3V3` |
| `DATA` / `OUT` / `S` | `GPIO 4` |
| `GND` / `-` | `GND` |

## Local and remote dashboards

- **Local HTML:** Open the generated `web/public/index.html`; no Cloudflare account is required.
- **Remote URL:** Deploy the same page with Cloudflare Workers Static Assets. The API token is entered locally and stored in the Git-ignored `.env` file.

A remote static page must receive an MQTT WSS credential, so
a visitor can inspect it in the browser. This is suitable only for an isolated
demo. Private or production dashboards require an authenticated backend and a
non-disposable broker.

## Broker, credentials, and lifecycle

The default uses Zero EMQX. Pass `--broker custom` to enter your broker host,
device port and `mqtt`/`mqtts` protocol, username, hidden password, and its
separate `ws://`/`wss://` dashboard URL. MQTTX validates both endpoints before
the scaffold creates the output directory. Remote dashboards require `wss://`.
The scaffold writes the following values to `data/<project>/.env` with file
mode `600`:

- Wi-Fi SSID and password
- Broker source, protocol, MQTT/WebSocket endpoints, username, password, and topic
- Zero instance ID and lifecycle when Zero EMQX is selected
- Cloudflare API token for remote delivery

All generated code stays under this sensor directory's `data/` folder. Its
contents and every `.env` file are ignored by Git. Never share the credential
file. When resuming a project, reuse its `.env` and Zero instance; if the serial
port already shows a valid `Published` reading, do not rebuild or flash again.

The default lifecycle is `idle_ttl`: active MQTTS or WSS connections keep the
namespace alive, and it is deleted after the returned idle period with no
connections. An expired instance or lost password cannot be queried or
recovered; create a new instance and regenerate the project instead.

## Default hardware

- ESP32-C6-DevKitC-1
- Three-pin DHT22 module
- USB-C data cable
- 2.4 GHz Wi-Fi

Confirm any different board, sensor, or data GPIO before compiling.

## Tooling

The skill inspects the existing toolchain and installs only missing components:

```sh
brew install arduino-cli
brew install emqx/mqttx/mqttx-cli
arduino-cli core install esp32:esp32
arduino-cli lib install "DHT sensor library" PubSubClient
```

MQTTX uses the selected protocol, port, and generated credentials. Never pass
`--insecure`. With `mqtts`, the ESP32 firmware uses the system CA bundle and
synchronizes its clock with NTP before the TLS handshake.
