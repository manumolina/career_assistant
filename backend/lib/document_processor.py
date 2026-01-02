import io
import zipfile
from urllib.parse import urlparse

import docx
import httpx
import PyPDF2
from fastapi import HTTPException, UploadFile


def is_valid_file_type(
    content: bytes, content_type: str = "", filename: str = ""
) -> bool:
    """Check if file is PDF, DOC, DOCX, or TXT"""
    filename_lower = filename.lower() if filename else ""

    # Check by extension
    if filename_lower.endswith((".pdf", ".doc", ".docx", ".txt")):
        return True

    # Check by content type
    valid_content_types = [
        "application/pdf",
        "application/msword",  # DOC
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
        "text/plain",
        "text/plain; charset=utf-8",
        "text/plain; charset=us-ascii",
    ]
    if content_type.lower() in valid_content_types:
        return True

    # Check by magic bytes
    # PDF
    if content.startswith(b"%PDF"):
        return True
    # DOCX (ZIP-based)
    if content.startswith(b"PK\x03\x04"):
        # DOCX files are ZIP archives, check if it's a DOCX
        try:
            zip_file = zipfile.ZipFile(io.BytesIO(content))
            if "word/document.xml" in zip_file.namelist():
                return True
        except Exception:
            pass
    # DOC (OLE2 format - starts with specific bytes)
    if content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return True
    # TXT - plain text (check if decodable as UTF-8 or ASCII)
    try:
        content.decode("utf-8")
        return True
    except Exception:
        pass

    return False


def is_pdf_content(
    content: bytes, content_type: str = "", filename: str = ""
) -> bool:
    """Check if content is a PDF based on content type, filename, or magic bytes."""
    return (
        content_type == "application/pdf"
        or filename.lower().endswith(".pdf")
        or content.startswith(b"%PDF")
    )


def is_docx_content(
    content: bytes, content_type: str = "", filename: str = ""
) -> bool:
    """Check if content is a DOCX based on content type, filename, or magic bytes."""
    return (
        content_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or filename.lower().endswith(".docx")
        or content.startswith(b"PK\x03\x04")
    )


def is_doc_content(
    content: bytes, content_type: str = "", filename: str = ""
) -> bool:
    """Check if content is a DOC (old format) based on content type, filename, or magic bytes."""
    return (
        content_type == "application/msword"
        or filename.lower().endswith(".doc")
        or content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")  # OLE2 magic bytes
    )


def is_txt_content(
    content: bytes, content_type: str = "", filename: str = ""
) -> bool:
    """Check if content is a text file."""
    filename_lower = filename.lower() if filename else ""
    return (
        filename_lower.endswith(".txt")
        or content_type.startswith("text/plain")
        # Try to decode as text (simple heuristic)
        or (
            not is_pdf_content(content, content_type, filename)
            and not is_docx_content(content, content_type, filename)
            and not is_doc_content(content, content_type, filename)
        )
    )


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF content."""
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text_parts = []

        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            except Exception as e:
                print(f"Error extracting text from PDF page {page_num}: {str(e)}")
                continue

        if not text_parts:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not extract text from PDF. "
                    "The PDF might be image-based or encrypted."
                ),
            )
        return "\n\n".join(text_parts)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error reading PDF: {str(e)}"
        )


def extract_text_from_docx(docx_content: bytes) -> str:
    """Extract text from DOCX content."""
    try:
        docx_file = io.BytesIO(docx_content)
        docx_reader = docx.Document(docx_file)
        text_parts = []
        for paragraph in docx_reader.paragraphs:
            text_parts.append(paragraph.text)
        return "\n\n".join(text_parts)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error reading DOCX: {str(e)}"
        )
    except HTTPException:
        raise


def extract_text_from_doc(_doc_content: bytes) -> str:
    """Extract text from DOC (old format) content."""
    # Note: This requires python-docx2txt or similar library
    # For now, we'll raise an error suggesting to convert to DOCX
    raise HTTPException(
        status_code=400,
        detail=(
            "Los archivos DOC (formato antiguo) no están soportados. "
            "Por favor, convierte el archivo a DOCX, PDF o TXT."
        ),
    )


def decode_text_content(content: bytes) -> str:
    """Decode bytes content as text, trying UTF-8 first, then latin-1."""
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return content.decode("latin-1")
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Could not decode file as text: {str(e)}",
            )


async def fetch_content_from_link(link: str) -> tuple[bytes, str]:
    """Fetch content from a URL and return content bytes and content type."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(link, timeout=30.0, follow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            return response.content, content_type
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Error fetching link (HTTP {e.response.status_code}): "
                    f"{str(e)}"
                ),
            )
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error fetching link: {str(e)}"
            )


async def extract_text_from_input(
    file: UploadFile | None, link: str | None
) -> str:
    """Extract text from file or link. Supports PDF, DOC, DOCX, and TXT files only."""
    if file:
        content = await file.read()
        file_type = file.content_type or ""
        file_name = file.filename or ""

        # Validate file type first
        if not is_valid_file_type(content, file_type, file_name):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Tipo de archivo no soportado. Solo se aceptan archivos "
                    f"PDF, DOC, DOCX o TXT. Archivo recibido: {file_name}"
                ),
            )

        if is_pdf_content(content, file_type, file_name):
            return extract_text_from_pdf(content)
        elif is_docx_content(content, file_type, file_name):
            return extract_text_from_docx(content)
        elif is_doc_content(content, file_type, file_name):
            return extract_text_from_doc(content)
        else:
            # Assume it's a text file
            return decode_text_content(content)

    elif link:
        content, content_type = await fetch_content_from_link(link)
        parsed_url = urlparse(link)
        filename = parsed_url.path.split("/")[-1] if parsed_url.path else ""

        # Validate file type first
        if not is_valid_file_type(content, content_type, filename):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Tipo de archivo no soportado desde el enlace. "
                    "Solo se aceptan archivos PDF, DOC, DOCX o TXT."
                ),
            )

        if is_pdf_content(content, content_type, parsed_url.path):
            return extract_text_from_pdf(content)
        elif is_docx_content(content, content_type, parsed_url.path):
            return extract_text_from_docx(content)
        elif is_doc_content(content, content_type, parsed_url.path):
            return extract_text_from_doc(content)
        else:
            return decode_text_content(content)

    else:
        raise HTTPException(
            status_code=400, detail="Either file or link must be provided"
        )

