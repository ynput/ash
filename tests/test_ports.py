import pytest

from ash.ports import parse_port_mapping, supports_port_publishing


@pytest.mark.parametrize(
    ("mapping", "expected"),
    [
        ("8080", ("8080/tcp", 8080)),
        ("8080/udp", ("8080/udp", 8080)),
        ("9000:80", ("80/tcp", 9000)),
        ("9000:80/udp", ("80/udp", 9000)),
        (" 9000:80 ", ("80/tcp", 9000)),
        ("127.0.0.1:9000:80", ("80/tcp", ("127.0.0.1", 9000))),
        ("[::1]:9000:80", ("80/tcp", ("::1", 9000))),
    ],
)
def test_parse_port_mapping(mapping: str, expected: tuple[str, object]) -> None:
    assert parse_port_mapping(mapping) == expected


@pytest.mark.parametrize(
    "mapping",
    [
        "",
        "8080:",
        ":80",
        "abc:80",
        "8080:abc",
        "8080:80/http",
        "0:80",
        "70000:80",
        "8000-8010:8000-8010",
    ],
)
def test_parse_port_mapping_invalid(mapping: str) -> None:
    with pytest.raises(ValueError, match="invalid"):
        parse_port_mapping(mapping)


@pytest.mark.parametrize(
    ("network_mode", "expected"),
    [
        (None, True),
        ("bridge", True),
        ("my-network", True),
        ("host", False),
        ("none", False),
        ("container:abc123", False),
    ],
)
def test_supports_port_publishing(network_mode: str | None, expected: bool) -> None:  # noqa: FBT001
    assert supports_port_publishing(network_mode) is expected
