# ESP32 SEN0193 Soil Moisture Dashboard Skill

[Chinese version](README.zh-CN.md)

This skill builds a complete ESP32-C6 and Capacitive Soil Moisture Sensor V2.0 (SEN0193) monitor: wiring, calibration, project generation, MQTT setup, flashing, verification, and a local or Cloudflare-hosted dashboard.

## Usage

```sh
git clone https://github.com/emqx/thing-loom.git
cd thing-loom/sen0193
codex
```

Then ask: `Build me a soil-moisture monitor.`

![SEN0193 to ESP32-C6 wiring](assets/sen0193-esp32-c6-wiring.svg)

Follow the labels printed on the sensor:

| SEN0193 | ESP32-C6 |
|---|---|
| `VCC` / red / `+` | `3V3` |
| `GND` / black / `-` | `GND` |
| `AOUT` / yellow / `S` | `GPIO 0` |

The board accepts 3.3-5.5V and outputs 0-3.0V. The documented setup uses 3.3V. Keep the electronics above the marked immersion line dry.

## Calibration

The generated firmware reports both sensor millivolts and a 0-100% normalized moisture value. The dashboard explains the conversion, shows its calibration points, and labels 0-29% as dry, 30-69% as moist, and 70-100% as wet. Its 2500 mV dry and 1250 mV wet defaults are only starting points. Record stabilized readings in air and water, never immersing above the marked line, then generate with:

```sh
scripts/scaffold.py data/my-plant --dry-mv <air-reading> --wet-mv <water-reading>
```

Reading depends on insertion depth and soil packing, so calibrate again for measurements that must be comparable.

## Delivery and security

- **Local HTML:** no Cloudflare account or deployment.
- **Remote URL:** Cloudflare Workers Static Assets with a least-privilege token entered through a hidden prompt.

Zero EMQX is the default disposable broker. `--broker custom` accepts a custom MQTT and WebSocket endpoint and validates both with MQTTX. Credentials are prompted locally and written only to Git-ignored files under `data/<project>` with mode `600`. A remote static dashboard exposes its demo MQTT credential to visitors; private or production dashboards need an authenticated backend.

## Default hardware and tooling

- ESP32-C6-DevKitC-1
- SEN0193 Capacitive Soil Moisture Sensor V2.0
- USB-C data cable and 2.4 GHz Wi-Fi

Only the ESP32 core and `PubSubClient` Arduino library are required; analog sampling uses the native Arduino-ESP32 ADC API.
