---
name: esp32-sen0193-cloudflare
description: Guide a customer from wiring an ESP32-C6 and SEN0193 Capacitive Soil Moisture Sensor V2.0 through calibration, Zero EMQX or custom MQTT broker setup, firmware flashing, and a local or Cloudflare-hosted live dashboard. Use for complete soil-moisture monitor builds from a cloned thing-loom sensor directory.
---

# ESP32 SEN0193 Dashboard

Complete the working path, not just file generation: firmware must publish a real moisture reading over MQTTS and the English dashboard must show it over WSS.

## Guided intake

Ask in the customer's language and wait where physical confirmation or a delivery choice is required:

1. Confirm the ESP32 is connected to the Mac with a data-capable USB cable and the sensor is wired. Show [the SEN0193 wiring diagram](assets/sen0193-esp32-c6-wiring.svg): sensor `VCC/red/+` to `3V3`, `GND/black/-` to `GND`, and `AOUT/yellow/S` to GPIO 0. Tell the customer to follow printed labels rather than connector position. Never connect the analog output to a non-ADC pin or expose the electronics above the probe's immersion line to water. Wait until they confirm.
2. Explain that the default dry/wet calibration values (2500/1250 mV) are starting points only. For useful percentages, record the stabilized `millivolts` reading first in air (dry) and then in water up to, but never above, the marked immersion line (wet), with the final installation depth held consistent. Regenerate with `--dry-mv <air>` and `--wet-mv <water>`; require dry to be greater than wet. Do not claim agronomic accuracy without soil-specific calibration.
3. Tell the customer that the scaffold prompts locally for the Wi-Fi SSID and password. Collect the password only through its hidden terminal prompt, never in chat or a command argument. If the agent cannot give the customer direct access to that prompt, give them the exact scaffold command to run in their own terminal and wait for completion.
4. Ask for one broker:
   - **Zero EMQX:** default; provisions an isolated disposable namespace automatically.
   - **Custom broker:** prompts locally for host, device port and `mqtt`/`mqtts` protocol, username, hidden password, and separate `ws://`/`wss://` dashboard URL. It validates both endpoints with MQTTX before writing files. Recommend `mqtts` and `wss`; the ESP32 requires a publicly trusted server certificate for `mqtts`.
5. Ask for one dashboard delivery:
   - **Local HTML:** default; no Cloudflare account, token, Wrangler, or deployment.
   - **Remote URL:** Cloudflare Workers Static Assets.
6. For Remote URL, say that the scaffold prompts locally for a least-privilege Cloudflare API token scoped to the target account. Never request or print a global API key. A custom broker must provide a `wss://` dashboard URL.
7. For Zero EMQX, explain before creating it: this makes a disposable isolated MQTT namespace, uses authenticated MQTTS/WSS only, and returns its password once. Every provisioning request uses the fixed tag `emqx-thing-loom`. Default to `idle_ttl`; use `fixed_ttl` only when requested.

Immediately before running the scaffold, tell the customer that it writes Wi-Fi, MQTT, and any Cloudflare credentials to `data/<project>/.env` with mode `600`; the sensor directory ignores every `.env` and everything generated under `data/`. For Zero EMQX, also disclose that it calls `POST https://zero.emqx.io/v1/instances`; ask for confirmation, do not provision until they agree, and do not automatically retry an ambiguous timeout.

For Remote URL, disclose that a static browser dashboard receives the MQTT credential, so a visitor can inspect it. This is acceptable only for an isolated demo credential. Use an authenticated backend for private or production data.

## Inputs and hardware

- Target `ESP32-C6-DevKitC-1`; confirm any different board before compiling.
- SEN0193 input is 3.3-5.5V and analog output is 0-3.0V. Power it from 3V3 for the documented setup. ESP32-C6 GPIO 0-6 are ADC pins; default to GPIO 0 and keep ADC input at or below 3.3V.
- Use fixed topic `sen0193/readings`. Payload is `{"moisture": <0..100>, "millivolts": <reading>}`. Zero EMQX isolates it between tenants; a custom broker must permit publish and subscribe.
- Keep generated customer code under this directory's `data/`. Reuse an existing project's `.env`. On resume, monitor serial first; a valid `Published` reading means firmware can be reused.

## Scaffold

After confirmation, run one of these from this skill:

```sh
scripts/scaffold.py data/<project-name> --delivery local
scripts/scaffold.py data/<project-name> --delivery remote
scripts/scaffold.py data/<project-name> --broker custom --delivery local
scripts/scaffold.py data/<project-name> --broker custom --delivery remote
```

The script securely prompts for credentials, provisions Zero EMQX by default, and copies `assets/project/`. Use `--pin`, `--dry-mv`, `--wet-mv`, `--worker-name`, or `--zero-lifecycle fixed_ttl` only as needed. Always choose a new output under `data/`.

If Wi-Fi authentication fails, rerun `scripts/scaffold.py data/<project-name> --update-wifi`. It prompts for replacement Wi-Fi credentials and changes only `.env` and `secrets.h`; compile and flash again without provisioning another broker.

## Toolchain and device

1. Inspect USB devices and serial ports before installing anything. A native `/dev/cu.usbmodem*` ESP32-C6 port on macOS needs no third-party driver.
2. Install only missing commands or dependencies:

   ```sh
   brew install arduino-cli
   brew install emqx/mqttx/mqttx-cli
   arduino-cli core update-index
   arduino-cli core install esp32:esp32
   arduino-cli lib install PubSubClient
   ```

3. Resolve the port with `arduino-cli board list`. Use `CDCOnBoot=cdc` for native `/dev/cu.usbmodem*` and `default` for `/dev/cu.usbserial*`:

   ```sh
   arduino-cli compile --fqbn esp32:esp32:esp32c6 --board-options CDCOnBoot=<cdc-option>,FlashSize=8M,PartitionScheme=default_8MB <project>
   arduino-cli upload --port <port> --fqbn esp32:esp32:esp32c6 --board-options CDCOnBoot=<cdc-option>,FlashSize=8M,PartitionScheme=default_8MB <project>
   ```

4. Monitor at 115200 baud. Require one `Published` line containing finite `moisture` from 0 through 100 and non-negative `millivolts`. Confirm the voltage changes downward when the probe moves from air into water; otherwise stop and check wiring. Calibrate and reflash before treating the percentage as meaningful.

## MQTTX verification

Load `.env` without echoing it or enabling shell tracing, then subscribe:

```sh
mqttx sub -h "$MQTT_HOST" -p "$MQTT_PORT" -l "$MQTT_PROTOCOL" -u "$MQTT_USERNAME" -P "$MQTT_PASSWORD" -t "$MQTT_TOPIC"
```

Require one valid JSON message. For `mqtts`, verify the certificate; never pass `--insecure`. Stop the subscriber after capturing the reading.

## Local HTML

Open the absolute `web/public/index.html` path with the native file opener and ask the customer to confirm live values. Only with consent, fall back to Python's standard-library HTTP server if `file://` is blocked. Return the local HTML path, project path, observed percentage and millivolts. Do not perform Cloudflare actions.

## Remote Cloudflare

Only for Remote URL: load `.env` without printing it, run `npx --yes wrangler@latest whoami`, then a dry run. Request approval immediately before `npx --yes wrangler@latest deploy`. Verify the URL shows `Receiving live data` and numeric moisture. Return the URL, project path, observed reading, broker endpoints, and for Zero EMQX its instance ID and lifecycle—but never credentials. Offer cleanup only with explicit confirmation.
