---
name: esp32-dht22-cloudflare
description: Guide a customer from wiring an ESP32-C6 and three-pin DHT22 through Zero EMQX or custom MQTT broker setup, firmware flashing, and a local or Cloudflare-hosted live dashboard. Use for complete temperature-and-humidity builds from a cloned thing-loom sensor directory.
---

# ESP32 DHT22 Dashboard

Complete the working path, not just file generation: firmware must publish a real reading over MQTTS and the English dashboard must show it over WSS.

## Guided intake

Ask in the customer's language and wait where physical confirmation or a delivery choice is required:

1. Confirm the ESP32 is connected to the Mac with a data-capable USB cable and the sensor is wired. Show [the DHT22 wiring diagram](assets/dht22-esp32-c6-wiring.svg): module `VCC` to `3V3`, `DATA/OUT/S` to GPIO 4, and `GND` to `GND`. Tell the customer to follow printed labels rather than physical pin order. Wait until they confirm.
2. Tell the customer that the scaffold will prompt locally for the Wi-Fi SSID and password. Collect the password only through its hidden terminal prompt, never in chat or a command argument. If the agent cannot give the customer direct access to that prompt, give them the exact scaffold command to run in their own terminal and wait for completion; do not try terminal UI automation or request credentials in chat.
3. Ask for one broker:
   - **Zero EMQX:** default; provisions an isolated disposable namespace automatically.
   - **Custom broker:** the scaffold locally prompts for its host, device port and `mqtt`/`mqtts` protocol, username, hidden password, and separate `ws://`/`wss://` dashboard URL. It validates both endpoints with MQTTX before writing any project files. Recommend `mqtts` and `wss`; the ESP32 requires a publicly trusted server certificate for `mqtts`.
4. Ask for one dashboard delivery:
   - **Local HTML:** default; no Cloudflare account, token, Wrangler, or deployment.
   - **Remote URL:** Cloudflare Workers Static Assets.
5. For Remote URL, tell the customer that the scaffold will prompt locally for a least-privilege Cloudflare API token scoped to the target account. The token uses a hidden prompt. Never request or print a global API key. A custom broker must provide a `wss://` dashboard URL for remote delivery.
6. For Zero EMQX, explain before creating it: this makes a disposable isolated MQTT namespace, uses authenticated MQTTS/WSS only, and returns its password once. Every provisioning request must use the fixed tag `emqx-thing-loom` so the Zero team can attribute usage. State the chosen lifecycle. Default to `idle_ttl`, which keeps the namespace while a device or dashboard is connected and deletes it after the returned idle duration with no connections; use `fixed_ttl` only when requested.

Immediately before running the scaffold, tell the customer that it writes the Wi-Fi, MQTT, and any Cloudflare credentials to `data/<project>/.env` with mode `600`; the sensor directory ignores every `.env` and everything generated under `data/`. For Zero EMQX, also disclose that it calls `POST https://zero.emqx.io/v1/instances`; ask for confirmation, do not provision until they agree, and do not automatically retry an ambiguous timeout because a tenant may already have been created.

For Remote URL, also disclose that a static browser dashboard must receive the MQTT credential, so a visitor can inspect it. This is acceptable only for an isolated demo credential. Use an authenticated backend for private or production data.

## Inputs and hardware

- Target `ESP32-C6-DevKitC-1`; confirm any different board before compiling.
- Use the fixed topic `dht22/readings`; Zero EMQX isolates it between tenants, while a custom broker must allow the supplied user to publish and subscribe to it. The scaffold creates a unique Worker name unless supplied.
- Keep all generated customer code under this sensor directory's `data/` folder. If an existing generated project there has `.env`, reuse its broker configuration instead of provisioning or configuring another one. Never display or commit its values. On a resumed project, monitor the serial port first; a valid `Published` reading means the existing firmware can be reused without compiling or flashing again.

## Scaffold

After confirmation, run one of these from this skill:

```sh
scripts/scaffold.py data/<project-name> --delivery local
scripts/scaffold.py data/<project-name> --delivery remote
scripts/scaffold.py data/<project-name> --broker custom --delivery local
scripts/scaffold.py data/<project-name> --broker custom --delivery remote
```

The script securely prompts for Wi-Fi credentials and, for Remote URL, a Cloudflare token. The default provisions Zero EMQX. `--broker custom` prompts locally for the custom connection and requires MQTTX; it verifies the device and dashboard endpoints before creating the output directory. The script then writes `.env` and copies the project from `assets/project/`. Use `--worker-name`, `--pin`, or `--zero-lifecycle fixed_ttl` only when requested. Always choose an output under `data/`; do not overwrite an existing directory.

## Toolchain and device

1. Inspect USB devices and serial ports before installing anything. A native `/dev/cu.usbmodem*` ESP32-C6 port on macOS needs no third-party driver.
2. Use existing `arduino-cli` and `mqttx` commands. On macOS with Homebrew, install only the missing command:

   ```sh
   brew install arduino-cli
   brew install emqx/mqttx/mqttx-cli
   ```

   On other systems, use the user's package manager or the official Arduino CLI and [MQTTX CLI](https://mqttx.app/docs/cli/downloading-and-installation) installers with approval. Verify MQTTX with `mqttx -v`.
3. Check `arduino-cli core list` and `arduino-cli lib list`, then install only the missing ESP32 dependencies:

   ```sh
   arduino-cli core update-index
   arduino-cli core install esp32:esp32
   arduino-cli lib install "DHT sensor library" PubSubClient
   ```

4. Resolve the connected port with `arduino-cli board list`; do not assume the first serial device.
5. Select USB CDC on boot from the detected connection: use `cdc` for a native macOS `/dev/cu.usbmodem*` port and `default` for a USB-to-UART `/dev/cu.usbserial*` port so serial logs remain visible. Compile and upload with the matching value, replacing paths and the port:

   ```sh
   arduino-cli compile --fqbn esp32:esp32:esp32c6 --board-options CDCOnBoot=<cdc-option>,FlashSize=8M,PartitionScheme=default_8MB <project>
   arduino-cli upload --port <port> --fqbn esp32:esp32:esp32c6 --board-options CDCOnBoot=<cdc-option>,FlashSize=8M,PartitionScheme=default_8MB <project>
   ```

6. Monitor at 115200 baud. Require one `Published` line with finite temperature and humidity before opening the dashboard; the firmware cannot reach that line until Wi-Fi, clock synchronization, and authenticated MQTT have succeeded. Capture their individual startup lines only when diagnosing a failure. The firmware diagnoses whether a failed SSID is visible on 2.4 GHz. If an iPhone hotspot appears on the Mac under Personal Hotspots but the ESP32 cannot see its SSID, enable **Allow Others to Join** and **Maximize Compatibility** so it advertises a joinable 2.4 GHz network.

## MQTTX verification

After the firmware publishes, load the generated `.env` into the MQTTX process without echoing it or enabling shell tracing, then subscribe with:

```sh
mqttx sub -h "$MQTT_HOST" -p "$MQTT_PORT" -l "$MQTT_PROTOCOL" -u "$MQTT_USERNAME" -P "$MQTT_PASSWORD" -t "$MQTT_TOPIC"
```

Require one JSON message with finite `temperature` and `humidity`. For `mqtts`, MQTTX must verify the broker certificate; never pass `--insecure`. Stop the subscriber after the reading is captured. This check isolates firmware and MQTT from dashboard problems.

## Local HTML

For the Local HTML choice, use the operating system's native file opener on the absolute path to `web/public/index.html` and ask the customer to confirm that live values appear. Prefer the file directly. Browser-automation tools may reject `file://` even when the customer's normal browser supports it; do not treat that automation restriction as a page failure. Only with the customer's consent, fall back to Python's standard-library HTTP server when their browser blocks scripts or WebSockets on `file://`, or when automated browser verification is required.

Return the local HTML path, project path, and observed reading. Stop here: do not perform any Cloudflare action.

## Remote Cloudflare

Only follow this section when the customer chose Remote URL.

1. Load the generated project `.env` into the Wrangler process without printing it or putting values in command arguments. Run Wrangler from the generated `web/` directory and confirm the token resolves exactly one expected account with `npx --yes wrangler@latest whoami`; if it exposes multiple accounts, ask the customer to scope the token to the target account.
2. Run a dry run first. Request approval immediately before the external deployment, then run `npx --yes wrangler@latest deploy`.
3. Open the returned `workers.dev` URL in a real browser, allow several seconds for MQTT over WSS, and verify:
   - the UI is entirely English;
   - status is `Receiving live data`;
   - temperature and humidity are numeric and match the topic used by the firmware.
   If browser automation is unavailable, verify HTTP success and one MQTTX message over WSS, open the URL with the operating system, and ask the customer to confirm those three UI details. Do not report the automation limitation as a page failure.
4. Return the deployed URL, project path, observed reading, and any unresolved hardware limitation.

Return the broker endpoints and, for Zero EMQX, its instance ID and lifecycle/expiry information, but never its username, password, Wi-Fi password, or Cloudflare token. Zero EMQX is disposable and suitable only for demos; when it expires there is no `GET` or recovery path, so create a new instance and regenerate credentials. Offer `wrangler delete` for cleanup after the demo, but run it only after explicit confirmation. Do not add a backend Worker unless the customer requires a private production dashboard.
