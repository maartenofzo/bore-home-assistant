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

Configure the integration in the Home Assistant UI.

### Configuration Options

| Option | Required | Default | Description |
|---|---|---|---|
| `to` | Yes | | The remote `bore` server to connect to (e.g., `bore.example.com`). |
| `local_port` | Yes | | The local port to expose. |
| `local_host` | No | `localhost` | The local host to expose. |
| `port` | No | `7835` | The port on the remote `bore` server to connect to. |
| `secret` | No | | A secret to authenticate with the `bore` server. |
| `check_url` | No | | A URL to check the health of the tunnel. If not provided, the integration will construct a URL from the `to` and `port` options. The default protocol is `https`. If you provide a URL, you must include the protocol (e.g., `http://example.com`). |
| `update_interval` | No | `5 minutes` | The interval at which to check the health of the tunnel. |

## Security Considerations

When using this integration, it's important to be aware of the security implications of exposing your Home Assistant instance to the internet.

### Plain HTTP Tunnels

If your Home Assistant instance is not configured with SSL/TLS (i.e., it's running on plain HTTP), the tunnel created by this integration will be **insecure**. All traffic, including credentials, will be sent in cleartext.

In this case, it is strongly recommended to secure the connection using other means. For example, you could set up a VPN like [WireGuard](https://www.wireguard.com/) between your Home Assistant machine and the remote server, and then run the `bore` tunnel over the VPN. However, if you have a VPN, you might not need this integration at all.

### SSL/TLS Tunnels

Even if your Home Assistant instance is running with SSL/TLS, directly exposing it to the internet can still be risky. It makes your Home Assistant instance a direct target for attackers.

For improved security, the recommended approach is to use this integration to create a tunnel to another machine on your local network that is running a reverse proxy (e.g., Nginx, Caddy, or Traefik). This reverse proxy can then forward traffic to your Home Assistant instance.


By not exposing Home Assistant directly, you reduce its attack surface.

### How it Works

This integration starts and manages a `bore` client process using the provided configuration. It is equivalent to running the following command:

```bash
bore local <local_port> --to <to> --local-host <local_host> --port <port> --secret <secret>
```

The integration then monitors the `bore` process and the tunnel's health.

### Connection Status

The integration provides a sensor entity that displays the connection status of your `bore` tunnel. A green checkmark icon (`mdi:check-circle`) indicates a healthy connection, while a red cross icon (`mdi:close-circle`) signifies an error or disconnection.

### Logging

All output from the `bore` CLI application is captured and made available as logs within Home Assistant, allowing for easy debugging and monitoring.

### Connection Health Check

The integration periodically performs a health check to ensure the tunnel is working correctly.

If you provide a `check_url`, the integration will send an HTTP GET request to this URL. A response with a status code in the 200-299 range is considered a success.

If you do not provide a `check_url`, the integration will construct a URL for you. It will use the `to` server and the port assigned by the `bore` server. The URL will be of the form `https://<to>:<assigned_port>`. If your local service is not running on HTTPS, you must provide a `check_url` with the `http://` protocol.

If the health check fails, the integration will automatically restart the `bore` process to re-establish the connection.