"""Synthetic triangular motor fixture: never use this as a real motor curve."""

import hashlib
from datetime import date
from pathlib import Path

import pytest
import yaml

from scripts.wo01_import_motor import import_motor
from src.vehicle.motors import parse_rasp

SYNTHETIC = "; synthetic test data only\nTEST 29 100 P .05 .1 TEST\n1 20\n2 0\n"


def test_curve_impulse_depletion_and_import(tmp_path: Path) -> None:
    curve = parse_rasp(SYNTHETIC)
    assert curve.diameter_m == pytest.approx(0.029)
    assert curve.total_impulse_ns == pytest.approx(20)
    assert curve.average_thrust_n == pytest.approx(10)
    assert [curve.thrust_n(t) for t in [-1, 0.5, 1, 1.5, 3]] == pytest.approx([0, 10, 20, 10, 0])
    assert [curve.burned_fraction(t) for t in [-1, 0.5, 1, 1.5, 3]] == pytest.approx(
        [0, 0.125, 0.5, 0.875, 1]
    )
    raw = SYNTHETIC.replace("\n", "\r\n").encode()
    output = tmp_path / "test.eng"
    import_motor(
        raw,
        output,
        "https://example.org/test",
        "https://example.org/cert",
        "TEST-ONLY",
        date(2020, 1, 1),
    )
    assert output.read_bytes() == raw
    metadata = yaml.safe_load(output.with_suffix(".yaml").read_text())
    assert metadata["sha256"] == hashlib.sha256(raw).hexdigest()
    with pytest.raises(FileExistsError):
        import_motor(raw, output, "source", "certificate", "TEST-ONLY", date(2020, 1, 1))


@pytest.mark.parametrize(
    "bad",
    [
        "",
        SYNTHETIC.replace("1 20", "1 nan"),
        SYNTHETIC.replace("1 20", "1 -20"),
        SYNTHETIC.replace("2 0", "1 0"),
        SYNTHETIC.replace("2 0", "2 1"),
        SYNTHETIC.replace(".05 .1", ".2 .1"),
        SYNTHETIC + "OTHER 29 100 P .05 .1 TEST\n",
    ],
)
def test_corrupt_motor_data_is_rejected(bad: str) -> None:
    with pytest.raises(ValueError):
        parse_rasp(bad)


def test_api_collection_preserves_bytes_and_marks_review_pending(tmp_path: Path) -> None:
    import base64

    from scripts.wo01_fetch_motors import save_downloads

    raw = SYNTHETIC.encode()
    response = {
        "results": [{"data": base64.b64encode(raw).decode(), "source": "cert", "format": "RASP"}]
    }
    inventory = save_downloads(
        tmp_path, "https://www.thrustcurve.org/api/v1/download.json", response
    )
    assert Path(inventory[0]["file"]).read_bytes() == raw
    assert inventory[0]["review_status"].startswith("unreviewed")
    assert inventory[0]["api_metadata"] == {"source": "cert", "format": "RASP"}
    with pytest.raises(ValueError):
        save_downloads(tmp_path, "source", {"results": []})


def test_api_transport_uses_documented_json_post(monkeypatch: pytest.MonkeyPatch) -> None:
    import io
    import json

    from scripts import wo01_fetch_motors as fetch

    def fake_open(request, *, timeout):
        assert request.method == "POST"
        assert request.full_url == fetch.API + "/search.json"
        assert json.loads(request.data) == {"manufacturer": "Estes", "commonName": "F15"}
        headers = {k.lower(): v for k, v in request.header_items()}
        assert headers["content-type"] == "application/json"
        assert headers["accept"] == "application/json"
        assert headers["user-agent"].startswith("rocket-twin/")
        assert timeout == 20
        return io.BytesIO(b'{"results":[]}')

    monkeypatch.setattr(fetch, "urlopen", fake_open)
    assert fetch.request_json(
        fetch.API + "/search.json", {"manufacturer": "Estes", "commonName": "F15"}
    ) == {"results": []}


def test_forbidden_response_has_bounded_diagnostic(monkeypatch: pytest.MonkeyPatch) -> None:
    import io
    from email.message import Message
    from urllib.error import HTTPError

    from scripts import wo01_fetch_motors as fetch

    headers = Message()
    headers["Server"] = "test-edge"
    headers["Set-Cookie"] = "private-cookie"
    calls = []

    def deny(request, *, timeout):
        calls.append(request)
        raise HTTPError(request.full_url, 403, "Forbidden", headers, io.BytesIO(b"blocked" * 1000))

    monkeypatch.setattr(fetch, "urlopen", deny)
    with pytest.raises(fetch.APIRequestError) as caught:
        fetch.request_json(fetch.API + "/search.json", {"commonName": "F15"})
    diagnostic = caught.value.diagnostic
    assert diagnostic["http_status"] == 403
    assert len(diagnostic["response_body_excerpt"]) == 4096
    assert diagnostic["response_headers"] == {"Server": "test-edge"}
    assert len(calls) == 1


def test_collection_stops_after_forbidden_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts import wo01_fetch_motors as fetch

    calls = []

    def deny(url, payload):
        calls.append(url)
        raise fetch.APIRequestError("HTTP 403", {"http_status": 403})

    monkeypatch.setattr(fetch, "request_json", deny)
    monkeypatch.setattr("sys.argv", ["wo01_fetch_motors.py", "--output", str(tmp_path)])
    assert fetch.main() == 1
    assert len(calls) == 1
    assert (tmp_path / "Estes_F15" / "error.json").exists()
    assert not (tmp_path / "AeroTech_F10").exists()
