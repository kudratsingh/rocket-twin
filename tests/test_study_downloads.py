"""PDF collection must preserve exact source bytes and reject HTML error pages."""

import io

import pytest

from scripts import wo01_fetch_study_sources as collect


def test_pdf_transport_and_byte_preservation(monkeypatch: pytest.MonkeyPatch) -> None:
    # Transport fixture only, not a purported certification PDF.
    raw = b"%PDF-1.4\ntransport fixture only\r\n"

    def fake_open(request, *, timeout):
        assert request.get_method() == "GET"
        assert request.get_header("Accept") == "application/pdf"
        assert request.get_header("User-agent").startswith("rocket-twin/")
        assert timeout == 20
        return io.BytesIO(raw)

    monkeypatch.setattr(collect, "urlopen", fake_open)
    assert collect.fetch_pdf("https://example.org/test.pdf") == raw


def test_html_success_response_is_not_saved_as_a_pdf(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        collect, "urlopen", lambda *args, **kwargs: io.BytesIO(b"<html>access denied</html>")
    )
    with pytest.raises(ValueError, match="not a PDF"):
        collect.fetch_pdf("https://example.org/test.pdf")


def test_collection_profile_limits_documents_and_curve_candidates(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys

    import yaml

    profile = tmp_path / "profile.yaml"
    profile.write_text(
        yaml.safe_dump(
            {
                "sources": {
                    "chosen": "https://example.org/a.pdf",
                    "context": "https://example.org/page",
                },
                "pdf_sources": ["chosen"],
                "curve_candidates": ["AeroTech:F22"],
            }
        )
    )
    documents = []
    curves = []
    monkeypatch.setattr(
        collect, "fetch_pdf", lambda url: documents.append(url) or b"%PDF-transport"
    )
    monkeypatch.setattr(collect, "collect_curves", lambda args: curves.extend(args) or 0)
    monkeypatch.setattr(
        sys, "argv", ["fetch", "--config", str(profile), "--output", str(tmp_path / "out")]
    )
    assert collect.main() == 0
    assert documents == ["https://example.org/a.pdf"]
    assert curves == ["--candidate", "AeroTech:F22"]
    assert not (tmp_path / "out" / "context.pdf").exists()
