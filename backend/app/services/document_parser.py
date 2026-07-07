from io import BytesIO

from tika import parser


class DocumentParserService:
    """Extract plain text from PDF, DOCX, and plain-text uploads using Apache Tika."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}

    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        extension = filename.lower()[filename.rfind(".") :] if "." in filename else ""
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {extension or 'unknown'}")

        if extension == ".txt":
            text = file_bytes.decode("utf-8", errors="replace").strip()
            if not text:
                raise ValueError("No text could be extracted from the uploaded document")
            return " ".join(text.split())

        parsed = parser.from_buffer(BytesIO(file_bytes))
        content = parsed.get("content")
        if not content:
            raise ValueError("No text could be extracted from the uploaded document")

        return " ".join(content.split())
