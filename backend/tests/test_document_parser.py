from io import BytesIO

from docx import Document

from app.services.document_parser import DocumentParserService


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
