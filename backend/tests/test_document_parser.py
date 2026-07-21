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
