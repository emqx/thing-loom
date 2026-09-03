#!/usr/bin/env python3
"""Create matching ESP32 SEN0193 firmware and a local-or-remote dashboard."""

import argparse
import getpass
import json
import re
import secrets
import shlex
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "assets" / "project"
ZERO_TAG = "emqx-thing-loom"


def provision_zero(lifecycle: str) -> dict:
    request = Request(
        "https://zero.emqx.io/v1/instances",
        data=json.dumps({"tag": ZERO_TAG, "lifecycle": lifecycle}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            if response.status != 201:
                raise RuntimeError(f"Zero EMQX returned HTTP {response.status}")
            instance = json.load(response)
    except HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"Zero EMQX returned HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Cannot reach Zero EMQX: {error.reason}") from error

    try:
        strings = (
            instance["instance_id"],
            instance["mqtts"]["host"],
            instance["mqtts"]["uri"],
            instance["wss"]["uri"],
            instance["credentials"]["username"],
            instance["credentials"]["password"],
            instance["lifecycle"],
        )
    except (KeyError, TypeError) as error:
        raise RuntimeError("Zero EMQX returned an incomplete response") from error
    if not all(isinstance(value, str) and value for value in strings):
        raise RuntimeError("Zero EMQX returned invalid connection details")
    port = instance["mqtts"]["port"]
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise RuntimeError("Zero EMQX returned an invalid MQTTS port")
    if not instance["mqtts"]["uri"].startswith("mqtts://") or not instance["wss"]["uri"].startswith("wss://"):
        raise RuntimeError("Zero EMQX returned non-TLS connection details")
    if instance["lifecycle"] not in ("fixed_ttl", "idle_ttl"):
        raise RuntimeError("Zero EMQX returned an unknown lifecycle")
    if instance["lifecycle"] == "fixed_ttl" and not isinstance(instance.get("expires_at"), str):
        raise RuntimeError("Zero EMQX omitted the fixed expiry")
    if instance["lifecycle"] == "idle_ttl" and not isinstance(instance.get("idle_ttl_seconds"), int):
        raise RuntimeError("Zero EMQX omitted the idle TTL")
    return instance


def prompt_custom_broker(parser: argparse.ArgumentParser, delivery: str) -> dict:
    host = input("MQTT broker host: ").strip()
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]
    if not host or any(char.isspace() or char in "/?#@" for char in host):
        parser.error("MQTT broker host must be a hostname or IP address without a URL scheme")
    try:
        port = int(input("MQTT port: "))
    except ValueError:
        parser.error("MQTT port must be an integer")
    if not 1 <= port <= 65535:
        parser.error("MQTT port must be between 1 and 65535")
    protocol = input("MQTT protocol [mqtts/mqtt] (mqtts): ").strip().lower() or "mqtts"
    if protocol not in ("mqtt", "mqtts"):
        parser.error("MQTT protocol must be mqtt or mqtts")
    if protocol == "mqtt":
        print("Warning: mqtt sends broker credentials and telemetry without TLS encryption")
    username = input("MQTT username: ")
    password = getpass.getpass("MQTT password: ")
    if not username or not password or "\0" in username or "\0" in password:
        parser.error("MQTT username and password are required and cannot contain NUL bytes")
    websocket_url = input("MQTT WebSocket URL (ws:// or wss://): ").strip()
    try:
        websocket = urlsplit(websocket_url)
        websocket.port
    except ValueError:
        parser.error("MQTT WebSocket URL has an invalid port")
    if websocket.scheme not in ("ws", "wss") or not websocket.hostname or websocket.fragment:
        parser.error("MQTT WebSocket URL must be a valid ws:// or wss:// URL without a fragment")
    if delivery == "remote" and websocket.scheme != "wss":
        parser.error("remote dashboards require a wss:// MQTT WebSocket URL")
    if websocket.scheme == "ws":
        print("Warning: ws sends dashboard credentials and telemetry without TLS encryption")
    uri_host = f"[{host}]" if ":" in host else host
    return {
        "host": host,
        "port": port,
        "protocol": protocol,
        "uri": f"{protocol}://{uri_host}:{port}",
        "websocket_uri": websocket_url,
        "username": username,
        "password": password,
    }


def validate_custom_broker(parser: argparse.ArgumentParser, broker: dict) -> None:
    mqttx = shutil.which("mqttx")
    if not mqttx:
        parser.error("MQTTX CLI is required to validate a custom broker before generation")
    websocket = urlsplit(broker["websocket_uri"])
    websocket_path = websocket.path or "/"
    if websocket.query:
        websocket_path += f"?{websocket.query}"
    endpoints = (
        ("device MQTT", broker["host"], broker["port"], broker["protocol"], "/mqtt"),
        (
            "dashboard WebSocket",
            websocket.hostname,
            websocket.port or (443 if websocket.scheme == "wss" else 80),
            websocket.scheme,
            websocket_path,
        ),
    )
    for label, host, port, protocol, path in endpoints:
        options = {
            "conn": {
                "mqttVersion": 4,
                "hostname": host,
                "port": port,
                "clientId": f"thing-loom-check-{secrets.token_hex(4)}",
                "clean": True,
                "keepalive": 30,
                "username": broker["username"],
                "password": broker["password"],
                "protocol": protocol,
                "path": path,
                "reconnectPeriod": 0,
                "maximumReconnectTimes": 0,
                "reqProblemInfo": True,
                "debug": False,
            }
        }
        with tempfile.NamedTemporaryFile("w", prefix="thing-loom-mqttx-", suffix=".json") as config:
            json.dump(options, config)
            config.flush()
            try:
                result = subprocess.run(
                    [mqttx, "conn", "--load-options", config.name],
                    capture_output=True,
                    text=True,
                    timeout=8,
                    check=False,
                )
                output = result.stdout + result.stderr
            except subprocess.TimeoutExpired as error:
                stdout = error.stdout or ""
                stderr = error.stderr or ""
                if isinstance(stdout, bytes):
                    stdout = stdout.decode(errors="replace")
                if isinstance(stderr, bytes):
                    stderr = stderr.decode(errors="replace")
                output = stdout + stderr
        if "Connected" not in output:
            parser.error(f"MQTTX could not connect to the custom broker's {label} endpoint")
        print(f"MQTTX validated custom broker {label} endpoint")


def env_line(name: str, value: object) -> str:
    return f"{name}={shlex.quote(str(value))}\n"


def write_secret(path: Path, content: str) -> None:
    path.touch(mode=0o600)
    path.chmod(0o600)
    path.write_text(content)


def update_wifi(parser: argparse.ArgumentParser, output: Path) -> None:
    env_path = output / ".env"
    secrets_path = output / "secrets.h"
    if not env_path.is_file() or not secrets_path.is_file():
        parser.error(f"existing project is incomplete: {output}")
    ssid = input("Wi-Fi SSID: ")
    password = getpass.getpass("Wi-Fi password: ")
    if not ssid or not password or "\0" in ssid or "\0" in password:
        parser.error("Wi-Fi SSID and password are required and cannot contain NUL bytes")

    secrets_text = secrets_path.read_text()
    for name, value in (("WIFI_SSID", ssid), ("WIFI_PASSWORD", password)):
        secrets_text, count = re.subn(
            rf"^const char {name}\[\] = .*;$",
            f"const char {name}[] = {json.dumps(value, ensure_ascii=False)};",
            secrets_text,
            flags=re.MULTILINE,
        )
        if count != 1:
            parser.error(f"could not update {name} in {secrets_path}")
    env_lines = env_path.read_text().splitlines()
    for name, value in (("WIFI_SSID", ssid), ("WIFI_PASSWORD", password)):
        matches = [index for index, line in enumerate(env_lines) if line.startswith(f"{name}=")]
        if len(matches) != 1:
            parser.error(f"could not update {name} in {env_path}")
        env_lines[matches[0]] = env_line(name, value).rstrip("\n")
    write_secret(secrets_path, secrets_text)
    write_secret(env_path, "\n".join(env_lines) + "\n")
    print(f"Updated Wi-Fi credentials: {output.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--worker-name")
    parser.add_argument("--pin", type=int, default=0)
    parser.add_argument("--dry-mv", type=int, default=2500)
    parser.add_argument("--wet-mv", type=int, default=1250)
    parser.add_argument("--delivery", choices=("local", "remote"), default="local")
    parser.add_argument("--broker", choices=("zero", "custom"), default="zero")
    parser.add_argument("--zero-lifecycle", choices=("fixed_ttl", "idle_ttl"), default="idle_ttl")
    parser.add_argument("--update-wifi", action="store_true")
    args = parser.parse_args()

    if args.update_wifi:
        update_wifi(parser, args.output)
        return
    if args.output.exists():
        parser.error(f"output already exists: {args.output}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,62}", args.output.name):
        parser.error("output folder name must be Arduino-safe and at most 63 characters")
    if not 0 <= args.pin <= 6:
        parser.error("SEN0193 requires an ESP32-C6 ADC pin between GPIO 0 and 6")
    if not 0 <= args.wet_mv < args.dry_mv <= 3300:
        parser.error("calibration must satisfy 0 <= wet-mv < dry-mv <= 3300")

    suffix = secrets.token_hex(4)
    topic = "sen0193/readings"
    worker = args.worker_name or f"esp32-sen0193-{suffix}"
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", worker):
        parser.error("worker name must be 1-63 lowercase letters, digits, or hyphens")

    ssid = input("Wi-Fi SSID: ")
    password = getpass.getpass("Wi-Fi password: ")
    if "\0" in ssid or "\0" in password:
        parser.error("Wi-Fi credentials cannot contain NUL bytes")
    if not ssid or not password:
        parser.error("Wi-Fi SSID and password are required")

    instance = None
    if args.broker == "custom":
        broker = prompt_custom_broker(parser, args.delivery)
        validate_custom_broker(parser, broker)

    cloudflare_api_token = ""
    if args.delivery == "remote":
        cloudflare_api_token = getpass.getpass("Cloudflare API token: ")
        if not cloudflare_api_token:
            parser.error("Cloudflare API token is required for remote delivery")

    if args.broker == "zero":
        try:
            instance = provision_zero(args.zero_lifecycle)
        except RuntimeError as error:
            parser.error(str(error))
        mqtts = instance["mqtts"]
        broker = {
            "host": mqtts["host"],
            "port": mqtts["port"],
            "protocol": "mqtts",
            "uri": mqtts["uri"],
            "websocket_uri": instance["wss"]["uri"],
            **instance["credentials"],
        }

    args.output.mkdir(parents=True)
    shutil.copytree(TEMPLATE_DIR / "web", args.output / "web")
    shutil.copy2(TEMPLATE_DIR / ".gitignore", args.output / ".gitignore")

    replacements = {
        "__MQTT_TOPIC__": topic,
        "__WORKER_NAME__": worker,
        "__COMPATIBILITY_DATE__": date.today().isoformat(),
        "__SENSOR_PIN__": str(args.pin),
        "__DRY_MV__": str(args.dry_mv),
        "__WET_MV__": str(args.wet_mv),
        "__NETWORK_HEADER__": "NetworkClientSecure.h" if broker["protocol"] == "mqtts" else "NetworkClient.h",
        "__NETWORK_CLASS__": "NetworkClientSecure" if broker["protocol"] == "mqtts" else "NetworkClient",
        "__TLS_DECLARATIONS__": (
            'extern const uint8_t x509_crt_bundle_start[] asm("_binary_x509_crt_bundle_start");\n'
            'extern const uint8_t x509_crt_bundle_end[] asm("_binary_x509_crt_bundle_end");'
            if broker["protocol"] == "mqtts" else ""
        ),
        "__TLS_SETUP__": (
            "network.setCACertBundle(x509_crt_bundle_start, x509_crt_bundle_end - x509_crt_bundle_start);"
            if broker["protocol"] == "mqtts" else ""
        ),
        "__CLOCK_GUARD__": (
            "if (!syncClock()) {\n    delay(2000);\n    return;\n  }"
            if broker["protocol"] == "mqtts" else ""
        ),
    }
    firmware = (TEMPLATE_DIR / "firmware.ino.tmpl").read_text()
    for old, new in replacements.items():
        firmware = firmware.replace(old, new)
    (args.output / f"{args.output.name}.ino").write_text(firmware)

    for path in (args.output / "web").rglob("*"):
        if path.is_file():
            content = path.read_text()
            for old, new in replacements.items():
                content = content.replace(old, new)
            path.write_text(content)

    write_secret(
        args.output / "secrets.h",
        "#pragma once\n\n"
        f"const char WIFI_SSID[] = {json.dumps(ssid, ensure_ascii=False)};\n"
        f"const char WIFI_PASSWORD[] = {json.dumps(password, ensure_ascii=False)};\n"
        f"const char MQTT_HOST[] = {json.dumps(broker['host'])};\n"
        f"const uint16_t MQTT_PORT = {broker['port']};\n"
        f"const char MQTT_USERNAME[] = {json.dumps(broker['username'])};\n"
        f"const char MQTT_PASSWORD[] = {json.dumps(broker['password'])};\n",
    )

    write_secret(
        args.output / "web" / "public" / "mqtt-config.js",
        "window.MQTT_CONFIG = Object.freeze("
        + json.dumps(
            {
                "url": broker["websocket_uri"],
                "username": broker["username"],
                "password": broker["password"],
                "topic": topic,
            },
            separators=(",", ":"),
        )
        + ");\n",
    )

    write_secret(
        args.output / ".env",
        "# Generated locally. Do not commit or share this file.\n"
        + env_line("DELIVERY", args.delivery)
        + env_line("BROKER_SOURCE", args.broker)
        + env_line("WIFI_SSID", ssid)
        + env_line("WIFI_PASSWORD", password)
        + env_line("ZERO_INSTANCE_ID", instance["instance_id"] if instance else "")
        + env_line("ZERO_LIFECYCLE", instance["lifecycle"] if instance else "")
        + env_line("ZERO_EXPIRES_AT", (instance.get("expires_at") or "") if instance else "")
        + env_line("ZERO_IDLE_TTL_SECONDS", (instance.get("idle_ttl_seconds") or "") if instance else "")
        + env_line("MQTT_HOST", broker["host"])
        + env_line("MQTT_PORT", broker["port"])
        + env_line("MQTT_PROTOCOL", broker["protocol"])
        + env_line("MQTT_URI", broker["uri"])
        + env_line("MQTT_MQTTS_URI", broker["uri"] if broker["protocol"] == "mqtts" else "")
        + env_line("MQTT_WSS_URI", broker["websocket_uri"])
        + env_line("MQTT_USERNAME", broker["username"])
        + env_line("MQTT_PASSWORD", broker["password"])
        + env_line("MQTT_TOPIC", topic)
        + env_line("CLOUDFLARE_API_TOKEN", cloudflare_api_token),
    )
    print(f"Project: {args.output.resolve()}")
    print(f"Broker: {'Zero EMQX' if instance else 'custom'}")
    if instance:
        print(f"Zero EMQX instance: {instance['instance_id']}")
    print(f"MQTT endpoint: {broker['uri']}")
    print(f"WebSocket endpoint: {broker['websocket_uri']}")
    if instance:
        if instance.get("expires_at"):
            print(f"Expires at: {instance['expires_at']}")
        else:
            print(f"Idle TTL: {instance['idle_ttl_seconds']} seconds")
    print(f"MQTT topic: {topic}")
    print(f"Worker name: {worker}")


if __name__ == "__main__":
    main()
