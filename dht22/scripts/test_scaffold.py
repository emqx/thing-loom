#!/usr/bin/env python3
"""Small offline check for Zero-backed project generation."""

import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import scaffold


def main() -> None:
    instance = {
        "instance_id": "emqx-test",
        "mqtts": {"host": "mqtt.test", "port": 8883, "uri": "mqtts://mqtt.test:8883"},
        "wss": {"host": "mqtt.test", "port": 8084, "uri": "wss://mqtt.test:8084/mqtt"},
        "credentials": {"username": "emqx-test", "password": "mqtt-secret"},
        "lifecycle": "idle_ttl",
        "expires_at": None,
        "idle_ttl_seconds": 3600,
    }
    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "dht22-demo"
        response = io.BytesIO(json.dumps(instance).encode())
        response.status = 201
        stdout = io.StringIO()
        with (
            patch.object(scaffold, "urlopen", return_value=response) as open_zero,
            patch.object(scaffold.getpass, "getpass", side_effect=("wifi-secret", "cf-secret")),
            patch("builtins.input", return_value="test-wifi"),
            patch.object(sys, "argv", ["scaffold.py", str(output), "--delivery", "remote"]),
            redirect_stdout(stdout),
        ):
            scaffold.main()

        env = (output / ".env").read_text()
        firmware = (output / "dht22-demo.ino").read_text()
        web_index = (output / "web/public/index.html").read_text()
        web_config = (output / "web/public/mqtt-config.js").read_text()
        assert "MQTT_HOST=mqtt.test" in env
        assert "MQTT_PORT=8883" in env
        assert "BROKER_SOURCE=zero" in env
        assert "MQTT_PROTOCOL=mqtts" in env
        assert "MQTT_MQTTS_URI=mqtts://mqtt.test:8883" in env
        assert "WIFI_PASSWORD=wifi-secret" in env
        assert "CLOUDFLARE_ACCOUNT_ID" not in env
        assert "CLOUDFLARE_API_TOKEN=cf-secret" in env
        assert json.loads(open_zero.call_args.args[0].data)["tag"] == "emqx-thing-loom"
        assert "mqtt.connect(clientId.c_str(), MQTT_USERNAME, MQTT_PASSWORD)" in firmware
        assert 'integrity="sha384-haZiwxTLortiFcYMBEEE1+8ayC+o18YtuwHZv+4WQHoPaLzRjwOV6h7Vva5iLSCZ"' in web_index
        assert '"url":"wss://mqtt.test:8084/mqtt"' in web_config
        assert "__NETWORK_" not in firmware
        assert "__TLS_" not in firmware
        assert "__CLOCK_" not in firmware
        assert "mqtt-secret" not in stdout.getvalue()
        for path in (output / ".env", output / "secrets.h", output / "web/public/mqtt-config.js"):
            assert path.stat().st_mode & 0o777 == 0o600

    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "dht22-custom"

        def validate(_, broker):
            assert not output.exists()
            assert broker["protocol"] == "mqtt"

        with (
            patch.object(scaffold, "validate_custom_broker", side_effect=validate) as check_broker,
            patch.object(scaffold.getpass, "getpass", side_effect=("wifi-secret", "broker-secret")),
            patch(
                "builtins.input",
                side_effect=(
                    "test-wifi",
                    "broker.example.com",
                    "1883",
                    "mqtt",
                    "device-user",
                    "wss://broker.example.com:8084/mqtt",
                ),
            ),
            patch.object(sys, "argv", ["scaffold.py", str(output), "--broker", "custom"]),
        ):
            scaffold.main()

        env = (output / ".env").read_text()
        firmware = (output / "dht22-custom.ino").read_text()
        web_config = (output / "web/public/mqtt-config.js").read_text()
        check_broker.assert_called_once()
        assert "BROKER_SOURCE=custom" in env
        assert "MQTT_PROTOCOL=mqtt" in env
        assert "MQTT_HOST=broker.example.com" in env
        assert "MQTT_PORT=1883" in env
        assert "#include <NetworkClient.h>" in firmware
        assert "NetworkClient network;" in firmware
        assert "setCACertBundle" not in firmware
        assert "if (!syncClock())" not in firmware
        assert '"url":"wss://broker.example.com:8084/mqtt"' in web_config

    broker = {
        "host": "broker.example.com",
        "port": 8883,
        "protocol": "mqtts",
        "websocket_uri": "wss://broker.example.com:8084/mqtt?token=test",
        "username": "device-user",
        "password": "broker-secret",
    }
    configs = []

    def connect(command, **_):
        assert "broker-secret" not in command
        assert Path(command[-1]).stat().st_mode & 0o777 == 0o600
        configs.append(json.loads(Path(command[-1]).read_text())["conn"])
        return type("Result", (), {"stdout": "Connected", "stderr": ""})()

    with (
        patch.object(scaffold.shutil, "which", return_value="/usr/local/bin/mqttx"),
        patch.object(scaffold.subprocess, "run", side_effect=connect),
    ):
        scaffold.validate_custom_broker(scaffold.argparse.ArgumentParser(), broker)
    assert [config["protocol"] for config in configs] == ["mqtts", "wss"]
    assert configs[1]["path"] == "/mqtt?token=test"

if __name__ == "__main__":
    main()
