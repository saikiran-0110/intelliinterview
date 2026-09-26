from io import BytesIO

from docx import Document

from app.services import document_parser as document_parser_module
from app.services.document_parser import DocumentParserService, _looks_mangled


def test_extract_plain_text():
    parser = DocumentParserService()
    text = parser.extract_text(b"  Alice  \nPython engineer  ", "cv.txt")
    assert text == "Alice Python engineer"


def test_extract_docx():
    document = Document()
    document.add_paragraph("Alex Morgan")
    document.add_paragraph("Skills: FastAPI, PostgreSQL")
    buffer = BytesIO()
    document.save(buffer)

    parser = DocumentParserService()
    text = parser.extract_text(buffer.getvalue(), "cv.docx")
    assert "Alex Morgan" in text
    assert "FastAPI" in text


def test_unsupported_extension_raises():
    parser = DocumentParserService()
    try:
        parser.extract_text(b"data", "cv.xlsx")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Unsupported file type" in str(exc)


def test_empty_text_file_raises():
    parser = DocumentParserService()
    try:
        parser.extract_text(b"   \n\n  ", "blank.txt")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "No text could be extracted" in str(exc)


def test_filename_without_extension_raises():
    parser = DocumentParserService()
    try:
        parser.extract_text(b"hello", "cv")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Unsupported file type" in str(exc)


def test_invalid_pdf_falls_through_to_error(monkeypatch):
    parser = DocumentParserService()
    monkeypatch.setattr(parser, "_extract_with_tika", lambda *_args, **_kwargs: None)
    try:
        parser.extract_text(b"not-a-pdf", "resume.pdf")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "No text could be extracted" in str(exc)


def test_looks_mangled_detects_character_spaced_text():
    mangled = " ".join(list("Docker Kubernetes PostgreSQL FastAPI React TypeScript " * 3))
    assert _looks_mangled(mangled) is True


def test_looks_mangled_accepts_clean_text():
    clean = (
        "Senior software engineer with experience in Docker Kubernetes PostgreSQL "
        "FastAPI React and TypeScript across several production systems and teams "
    ) * 3
    assert _looks_mangled(clean) is False


def test_looks_mangled_short_text_is_never_flagged():
    assert _looks_mangled("a b c") is False


def test_extract_pdf_falls_back_to_tika_when_mangled(monkeypatch):
    parser = DocumentParserService()
    mangled = " ".join(list("Docker Kubernetes PostgreSQL FastAPI React TypeScript " * 3))
    clean = "Senior engineer skilled in Docker and Kubernetes production deployments."

    monkeypatch.setattr(parser, "_extract_pdf", lambda *_args, **_kwargs: mangled)
    monkeypatch.setattr(parser, "_extract_with_tika", lambda *_args, **_kwargs: clean)

    text = parser.extract_text(b"pdf-bytes", "resume.pdf")
    assert text == clean


def test_extract_pdf_keeps_mangled_text_when_tika_unavailable(monkeypatch):
    parser = DocumentParserService()
    mangled = " ".join(list("Docker Kubernetes PostgreSQL FastAPI React TypeScript " * 3))

    monkeypatch.setattr(parser, "_extract_pdf", lambda *_args, **_kwargs: mangled)
    monkeypatch.setattr(parser, "_extract_with_tika", lambda *_args, **_kwargs: None)

    text = parser.extract_text(b"pdf-bytes", "resume.pdf")
    assert text == mangled


def test_extract_pdf_layout_mode_resolves_mangled_text_without_tika(monkeypatch):
    parser = DocumentParserService()
    mangled = " ".join(list("Docker Kubernetes PostgreSQL FastAPI React TypeScript " * 3))
    clean_via_layout = "Senior engineer skilled in Docker and Kubernetes production deployments."

    def fake_extract_pdf(_file_bytes, _errors, extraction_mode="plain"):
        return clean_via_layout if extraction_mode == "layout" else mangled

    def tika_should_not_be_called(*_args, **_kwargs):
        raise AssertionError("Tika should not be tried when layout mode already resolved the text")

    monkeypatch.setattr(parser, "_extract_pdf", fake_extract_pdf)
    monkeypatch.setattr(parser, "_extract_with_tika", tika_should_not_be_called)

    text = parser.extract_text(b"pdf-bytes", "resume.pdf")
    assert text == clean_via_layout


def test_extract_with_tika_short_circuits_without_java(monkeypatch):
    monkeypatch.setattr(document_parser_module, "_java_available", None)
    monkeypatch.setattr(document_parser_module.shutil, "which", lambda _name: None)

    def from_buffer_should_not_be_called(*_args, **_kwargs):
        raise AssertionError("Tika server should never be invoked without a Java runtime")

    monkeypatch.setattr("tika.parser.from_buffer", from_buffer_should_not_be_called)

    parser = DocumentParserService()
    errors: list[str] = []
    result = parser._extract_with_tika(b"pdf-bytes", errors)

    assert result is None
    assert any("Java runtime" in message for message in errors)


def test_docx_includes_table_cells():
    document = Document()
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Skill"
    table.cell(0, 1).text = "PostgreSQL"
    buffer = BytesIO()
    document.save(buffer)

    parser = DocumentParserService()
    text = parser.extract_text(buffer.getvalue(), "cv.docx")
    assert "PostgreSQL" in text
