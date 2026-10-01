"""Parse Compose-like port mappings into the form docker-py expects."""

import re

# docker-py accepts a bare host port or an (ip, host port) tuple
HostBinding = int | tuple[str, int]

_MAX_PORT = 65535
_NO_PUBLISH_NETWORK_MODES = frozenset({"host", "none"})
_CONTAINER_PORT = re.compile(r"^(?P<port>\d+)(?:/(?P<proto>tcp|udp|sctp))?$")


class PortMappingError(ValueError):
    """Exception raised for errors in port mappings."""
    def __init__(self, what: str, value: str) -> None:
        super().__init__(f"invalid {what} port '{value}'")


def supports_port_publishing(network_mode: str | None) -> bool:
    """Return whether Docker allows publishing ports in the given network mode.

    Args:
        network_mode: The network mode of the Docker container.

    Returns:
        True if port publishing is supported in the given network mode, False otherwise.

    """
    if network_mode is None:
        return True
    if network_mode in _NO_PUBLISH_NETWORK_MODES:
        return False
    return not network_mode.startswith("container:")


def _parse_port(value: str, what: str) -> int:
    if not value.isdigit() or not 1 <= int(value) <= _MAX_PORT:
        raise PortMappingError(what, value)
    return int(value)


def parse_port_mapping(mapping: str) -> tuple[str, HostBinding]:
    """Parse `[[ip:]host:]container[/proto]` into (container_key, host_binding).

    A bare `8080` means host 8080 -> container 8080 (Compose-like UX).
    The container key always carries the protocol (e.g. `8080/tcp`), so
    equivalent mappings collapse to the same key.

    Args:
        mapping: The port mapping string in the form `[[ip:]host:]container[/proto]`.

    Returns:
        A tuple containing the container key (with protocol) and the host binding
            (either an int or a (ip, int) tuple).

    Raises:
        PortMappingError: If the mapping is malformed.

    """
    spec = mapping.strip()
    rest, sep, container = spec.rpartition(":")
    if not sep:
        container = spec
        rest = spec.partition("/")[0]

    # a non-matching value is never all digits, so _parse_port rejects it
    match = _CONTAINER_PORT.match(container)
    container_port = _parse_port(match["port"] if match else container, "container")
    proto = (match and match["proto"]) or "tcp"
    container_key = f"{container_port}/{proto}"

    host_ip, _, host_port_str = rest.rpartition(":")
    host_port = _parse_port(host_port_str, "host")
    host_ip = host_ip.strip("[]")  # IPv6 addresses are written as [::1]

    if host_ip:
        return container_key, (host_ip, host_port)
    return container_key, host_port
