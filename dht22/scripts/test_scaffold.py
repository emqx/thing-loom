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
        assert "MQTT_MQTTS_URI=mqtts://mqtt.test:8883" in env
        assert "WIFI_PASSWORD=wifi-secret" in env
        assert "CLOUDFLARE_ACCOUNT_ID" not in env
        assert "CLOUDFLARE_API_TOKEN=cf-secret" in env
        assert json.loads(open_zero.call_args.args[0].data)["tag"] == "emqx-thing-loom"
        assert "mqtt.connect(clientId.c_str(), MQTT_USERNAME, MQTT_PASSWORD)" in firmware
        assert 'integrity="sha384-haZiwxTLortiFcYMBEEE1+8ayC+o18YtuwHZv+4WQHoPaLzRjwOV6h7Vva5iLSCZ"' in web_index
        assert '"url":"wss://mqtt.test:8084/mqtt"' in web_config
        assert "mqtt-secret" not in stdout.getvalue()
        for path in (output / ".env", output / "secrets.h", output / "web/public/mqtt-config.js"):
            assert path.stat().st_mode & 0o777 == 0o600

if __name__ == "__main__":
    main()
