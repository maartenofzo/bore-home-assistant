
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

