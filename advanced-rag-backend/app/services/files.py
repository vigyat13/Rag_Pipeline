import os
from pathlib import Path
from typing import Tuple

import pdfplumber
import docx
import markdown

from app.core.config import get_settings

settings = get_settings()


def ensure_user_upload_dir(user_id: str) -> str:
    base = Path(settings.UPLOAD_DIR) / user_id
    base.mkdir(parents=True, exist_ok=True)
    return str(base)


def save_uploaded_file(user_id: str, filename: str, file_obj) -> Tuple[str, int]:
    user_dir = ensure_user_upload_dir(user_id)
    dest_path = Path(user_dir) / filename
    with open(dest_path, "wb") as f:
        content = file_obj.read()
        f.write(content)
    size = os.path.getsize(dest_path)
    return str(dest_path), size


def extract_text(path: str, content_type: str) -> str:
    path_obj = Path(path)
    if content_type == "application/pdf" or path_obj.suffix.lower() == ".pdf":
        text = []
        with pdfplumber.open(path_obj) as pdf:
            for page in pdf.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text)
    elif path_obj.suffix.lower() in [".docx"]:
        doc = docx.Document(path_obj)
        return "\n".join([para.text for para in doc.paragraphs])
    elif path_obj.suffix.lower() in [".md"]:
        with open(path_obj, "r", encoding="utf-8") as f:
            return f.read()
    else:
        with open(path_obj, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
