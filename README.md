
# Bore Home Assistant Integration

This integration allows you to control a [bore](https://github.com/ekzhang/bore) client from Home Assistant.

## Installation

1.  Install the `bore` client. See the [bore documentation](https://github.com/ekzhang/bore) for instructions.
2.  Install this integration using [HACS](https://hacs.xyz/).
3.  Add the integration in Home Assistant.

### Docker

If you are running Home Assistant in a Docker container, you can mount the `bore` binary into the container using a volume mount.

In your `docker-compose.yml` file, add the following volume to your Home Assistant service:

```yaml
volumes:
  - /path/to/your/bore/binary:/usr/local/bin/bore
```

Replace `/path/to/your/bore/binary` with the actual path to the `bore` binary on your host machine.

## Configuration

Configure the integration in the Home Assistant UI. All options from the `bore local` command are supported.

## How it Works

This integration sets up and manages a `bore` tunnel client. You can configure all options available to the `bore local` command directly within Home Assistant.

### Connection Status

The integration provides a sensor entity that displays the connection status of your `bore` tunnel. A green checkmark icon (`mdi:check-circle`) indicates a healthy connection, while a red cross icon (`mdi:close-circle`) signifies an error or disconnection.

### Logging

All output from the `bore` CLI application is captured and made available as logs within Home Assistant, allowing for easy debugging and monitoring.

### Connection Health Check

The integration periodically performs a configurable connection health check. This check can be configured to:

*   **Ping a specific URL:** If a `check_url` is provided, the integration will perform an HTTP GET request to this URL and expect a 200 OK response.
*   **Ping the remote server:** If no `check_url` is provided, the integration will perform an HTTP GET request to the configured remote `bore` server and the assigned port (either from configuration or extracted from successful `bore` logs).

If the health check fails (e.g., due to a timeout or non-200 response), the integration will attempt to restart the `bore` tunnel to re-establish a healthy connection.

