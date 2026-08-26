#!/usr/bin/env python3
"""Create matching ESP32 DHT22 firmware and a local-or-remote dashboard."""

import argparse
import getpass
import json
import re
import secrets
import shlex
import shutil
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
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


def env_line(name: str, value: object) -> str:
    return f"{name}={shlex.quote(str(value))}\n"


def write_secret(path: Path, content: str) -> None:
    path.touch(mode=0o600)
    path.chmod(0o600)
    path.write_text(content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--worker-name")
    parser.add_argument("--pin", type=int, default=4)
    parser.add_argument("--delivery", choices=("local", "remote"), default="local")
    parser.add_argument("--zero-lifecycle", choices=("fixed_ttl", "idle_ttl"), default="idle_ttl")
    args = parser.parse_args()

    if args.output.exists():
        parser.error(f"output already exists: {args.output}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,62}", args.output.name):
        parser.error("output folder name must be Arduino-safe and at most 63 characters")
    if not 0 <= args.pin <= 30:
        parser.error("pin must be between 0 and 30")

    suffix = secrets.token_hex(4)
    topic = "dht22/readings"
    worker = args.worker_name or f"esp32-dht22-{suffix}"
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", worker):
        parser.error("worker name must be 1-63 lowercase letters, digits, or hyphens")

    ssid = input("Wi-Fi SSID: ")
    password = getpass.getpass("Wi-Fi password: ")
    if "\0" in ssid or "\0" in password:
        parser.error("Wi-Fi credentials cannot contain NUL bytes")
    if not ssid or not password:
        parser.error("Wi-Fi SSID and password are required")

    cloudflare_api_token = ""
    if args.delivery == "remote":
        cloudflare_api_token = getpass.getpass("Cloudflare API token: ")
        if not cloudflare_api_token:
            parser.error("Cloudflare API token is required for remote delivery")

    try:
        instance = provision_zero(args.zero_lifecycle)
    except RuntimeError as error:
        parser.error(str(error))

    mqtts = instance["mqtts"]
    wss = instance["wss"]
    mqtt_credentials = instance["credentials"]

    args.output.mkdir(parents=True)
    shutil.copytree(TEMPLATE_DIR / "web", args.output / "web")
    shutil.copy2(TEMPLATE_DIR / ".gitignore", args.output / ".gitignore")

    replacements = {
        "__MQTT_TOPIC__": topic,
        "__WORKER_NAME__": worker,
        "__COMPATIBILITY_DATE__": date.today().isoformat(),
        "__DHT_PIN__": str(args.pin),
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

    secrets_file = args.output / "secrets.h"
    write_secret(
        secrets_file,
        "#pragma once\n\n"
        f"const char WIFI_SSID[] = {json.dumps(ssid, ensure_ascii=False)};\n"
        f"const char WIFI_PASSWORD[] = {json.dumps(password, ensure_ascii=False)};\n"
        f"const char MQTT_HOST[] = {json.dumps(mqtts['host'])};\n"
        f"const uint16_t MQTT_PORT = {mqtts['port']};\n"
        f"const char MQTT_USERNAME[] = {json.dumps(mqtt_credentials['username'])};\n"
        f"const char MQTT_PASSWORD[] = {json.dumps(mqtt_credentials['password'])};\n"
    )

    mqtt_config = args.output / "web" / "public" / "mqtt-config.js"
    write_secret(
        mqtt_config,
        "window.MQTT_CONFIG = Object.freeze("
        + json.dumps(
            {
                "url": wss["uri"],
                "username": mqtt_credentials["username"],
                "password": mqtt_credentials["password"],
                "topic": topic,
            },
            separators=(",", ":"),
        )
        + ");\n"
    )

    env = args.output / ".env"
    write_secret(
        env,
        "# Generated locally. Do not commit or share this file.\n"
        + env_line("DELIVERY", args.delivery)
        + env_line("WIFI_SSID", ssid)
        + env_line("WIFI_PASSWORD", password)
        + env_line("ZERO_INSTANCE_ID", instance["instance_id"])
        + env_line("ZERO_LIFECYCLE", instance["lifecycle"])
        + env_line("ZERO_EXPIRES_AT", instance.get("expires_at") or "")
        + env_line("ZERO_IDLE_TTL_SECONDS", instance.get("idle_ttl_seconds") or "")
        + env_line("MQTT_HOST", mqtts["host"])
        + env_line("MQTT_PORT", mqtts["port"])
        + env_line("MQTT_MQTTS_URI", mqtts["uri"])
        + env_line("MQTT_WSS_URI", wss["uri"])
        + env_line("MQTT_USERNAME", mqtt_credentials["username"])
        + env_line("MQTT_PASSWORD", mqtt_credentials["password"])
        + env_line("MQTT_TOPIC", topic)
        + env_line("CLOUDFLARE_API_TOKEN", cloudflare_api_token)
    )
    print(f"Project: {args.output.resolve()}")
    print(f"Zero EMQX instance: {instance['instance_id']}")
    print(f"MQTTS endpoint: {mqtts['uri']}")
    print(f"WSS endpoint: {wss['uri']}")
    if instance.get("expires_at"):
        print(f"Expires at: {instance['expires_at']}")
    else:
        print(f"Idle TTL: {instance['idle_ttl_seconds']} seconds")
    print(f"MQTT topic: {topic}")
    print(f"Worker name: {worker}")


if __name__ == "__main__":
    main()
