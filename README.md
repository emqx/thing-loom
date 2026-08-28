# ThingLoom

[Chinese version](README.zh-CN.md)

> **Build your smart home with one prompt.**

ThingLoom turns a natural-language request into a verified, working path from a
physical sensor to a live dashboard. An agent guides the wiring, generates the
firmware, flashes the board, provisions secure messaging, and checks a real
reading before calling the project complete.

## Why ThingLoom

Building even a small smart-home device usually means stitching together board
drivers, firmware, Wi-Fi, MQTT, TLS, cloud credentials, and a dashboard. Most
tutorials stop after generating code. ThingLoom packages that knowledge into
reusable agent skills and treats **real telemetry from real hardware** as the
definition of done.

The goal is not another IoT framework. It is the shortest reliable path from an
idea to a connected device:

```text
One prompt
  -> wire the sensor
  -> generate and flash firmware
  -> publish over secure MQTT
  -> verify the real message
  -> open a live dashboard
  -> store and explore history (TODO)
```

## Before you start

Bring an ESP32 development board, a supported sensor such as a DHT22 or
BH1750FVI, a USB data cable, jumper wires, and access to a 2.4 GHz Wi-Fi network.
That is enough to begin. Choose the disposable Zero EMQX environment for a
quick demo, or connect your own MQTT broker for an existing deployment. If you
need a reliable long-term broker but do not have one, [create an EMQX Cloud
Serverless or Dedicated Flex deployment](https://www.emqx.com/en/cloud).

## Try a project

Start with either verified end-to-end skill:

### Temperature and humidity

```sh
git clone https://github.com/emqx/thing-loom.git
cd thing-loom/dht22
codex
```

Then ask:

```text
Build me a temperature and humidity monitor.
```

The skill takes the project through wiring, broker setup, firmware
compilation and flashing, MQTT verification, and a local or remote live
dashboard. See the [DHT22 project](dht22/README.md) for hardware and security
details.

### Ambient light

```sh
cd thing-loom/bh1750
codex
```

Then ask:

```text
Build me an ambient-light monitor.
```

The [BH1750FVI project](bh1750/README.md) follows the same verified path and
publishes real illuminance readings in lux.

## The toolchain

| Tool | Role |
|---|---|
| Agent Skills | Turn a prompt into a repeatable hardware workflow. |
| [Arduino CLI](https://arduino.github.io/arduino-cli/) | Compile, flash, and monitor ESP32 firmware. |
| [EMQX Cloud](https://www.emqx.com/en/cloud) | Create a managed Serverless or Dedicated Flex broker when you do not already have one. |
| [Zero EMQX](https://zero.emqx.io/) | Create an isolated, disposable MQTT namespace with authenticated MQTTS and WSS transport. |
| [MQTTX CLI](https://mqttx.app/docs/cli/downloading-and-installation) | Independently verify that the device message reached MQTT. |
| [Cloudflare Workers Static Assets](https://developers.cloudflare.com/workers/static-assets/) | Publish the live browser dashboard when a remote URL is requested. |
| [EMQX Tables](https://www.emqx.com/en/cloud/emqx-tables) | **TODO:** persist, query, and visualize device telemetry as time-series data. |

## From a first reading to a lasting smart home

Zero EMQX is designed for prototypes, demos, and first-run validation. Its
namespaces expire automatically and the service provides no SLA, so it should
not carry production traffic.

When your device needs persistent credentials, long-term operation, an SLA, or
production capacity, use your own broker or [create an EMQX Cloud deployment](https://www.emqx.com/en/cloud).
Choose **Serverless** for a simple usage-based start, or **Dedicated Flex** for
dedicated resources, higher performance, and enterprise capabilities. EMQX
Tables then keeps MQTT telemetry in the same managed platform for historical
queries, analytics, and visualization.

## Principles

- A generated project is not complete until a real device publishes a valid reading.
- Credentials stay in local, Git-ignored files and are never printed in chat or logs.
- One proven vertical slice comes before a generic device framework or a catalog of sensors.

## Roadmap

- [x] ESP32-C6 + DHT22 -> secure MQTT -> live dashboard
- [x] ESP32-C6 + BH1750FVI -> secure MQTT -> live dashboard
- [ ] MQTT -> EMQX Tables time-series storage
- [ ] Historical charts, alerts, and long-running smart-home deployments
- [ ] More verified sensor skills

## Build our intelligent world together

Every proven skill can turn another maze of wiring, firmware, protocols, and
cloud services into one simple request. Bring a sensor, an idea, or a working
end-to-end path—and help make technology feel less like configuration and more
like creation.

Use the [skill contribution template](examples/README.md) to add a proven
hardware-to-dashboard path of your own.

> **Join us. Let complex work begin with one sentence.**

## License

[MIT](LICENSE)
