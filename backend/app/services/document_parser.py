from io import BytesIO
from typing import Optional

from docx import Document
from pypdf import PdfReader


class DocumentParserService:
    """Extract plain text from PDF, DOCX, and plain-text uploads.

    Uses local parsers first so CV upload does not depend on downloading the
    Apache Tika server JAR. Tika is tried as an optional fallback when available.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}

    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        extension = filename.lower()[filename.rfind(".") :] if "." in filename else ""
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {extension or 'unknown'}")

        if extension == ".txt":
            return self._normalize(file_bytes.decode("utf-8", errors="replace"))

        errors: list[str] = []

        if extension == ".pdf":
            text = self._extract_pdf(file_bytes, errors)
            if text:
                return text
        elif extension == ".docx":
            text = self._extract_docx(file_bytes, errors)
            if text:
                return text

        text = self._extract_with_tika(file_bytes, errors)
        if text:
            return text

        detail = "; ".join(errors) if errors else "no extractor succeeded"
        if extension == ".doc":
            raise ValueError(
                "Could not parse .doc file. Convert to PDF, DOCX, or TXT and try again. "
                f"Details: {detail}"
            )
        raise ValueError(f"No text could be extracted from the uploaded document. Details: {detail}")

    def _normalize(self, text: str) -> str:
        cleaned = " ".join(text.split())
        if not cleaned:
            raise ValueError("No text could be extracted from the uploaded document")
        return cleaned

    def _extract_pdf(self, file_bytes: bytes, errors: list[str]) -> Optional[str]:
        try:
            reader = PdfReader(BytesIO(file_bytes))
            parts = [(page.extract_text() or "") for page in reader.pages]
            text = " ".join(parts).strip()
            return self._normalize(text) if text else None
        except Exception as exc:  # noqa: BLE001 - surface parser failures as extract errors
            errors.append(f"PDF parser failed: {exc}")
            return None

    def _extract_docx(self, file_bytes: bytes, errors: list[str]) -> Optional[str]:
        try:
            document = Document(BytesIO(file_bytes))
            parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
            for table in document.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text:
                            parts.append(cell.text)
            text = " ".join(parts).strip()
            return self._normalize(text) if text else None
        except Exception as exc:  # noqa: BLE001
            errors.append(f"DOCX parser failed: {exc}")
            return None

    def _extract_with_tika(self, file_bytes: bytes, errors: list[str]) -> Optional[str]:
        try:
            from tika import parser
        except ImportError:
            errors.append("Apache Tika is not installed")
            return None

        try:
            parsed = parser.from_buffer(BytesIO(file_bytes))
            content = (parsed or {}).get("content")
            if not content:
                errors.append("Apache Tika returned no content")
                return None
            return self._normalize(content)
        except Exception as exc:  # noqa: BLE001 - network/JAR download failures are common
            errors.append(f"Apache Tika unavailable: {exc}")
            return None
