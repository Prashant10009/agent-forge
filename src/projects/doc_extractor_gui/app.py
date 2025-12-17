import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st

# ------------------------------------------------------------
# Make sure the repo root (which contains "src") is on sys.path
# ------------------------------------------------------------
FILE_DIR = Path(__file__).resolve()
REPO_ROOT = FILE_DIR.parents[3]  # .../agent-forge
DOCS_DIR = REPO_ROOT / "data" / "documents"
INDEX_PATH = DOCS_DIR / "index.json"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.orchestrator import Orchestrator


@st.cache_resource
def get_orchestrator() -> Orchestrator:
    return Orchestrator(workspace_dir=str(REPO_ROOT))


def load_index() -> List[Dict[str, Any]]:
    if INDEX_PATH.exists():
        try:
            return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_index(entries: List[Dict[str, Any]]) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def save_document_and_result(
    uploaded_file, tmp_path: str, result: Dict[str, Any]
) -> None:
    """
    Save the uploaded file and result JSON under data/documents,
    and update index.json.
    """
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    original_name = uploaded_file.name
    safe_name = original_name.replace(os.sep, "_")
    doc_id = f"{now}"

    # Save file
    dest_file = DOCS_DIR / f"{doc_id}_{safe_name}"
    with open(tmp_path, "rb") as src, open(dest_file, "wb") as dst:
        dst.write(src.read())

    # Save JSON
    json_path = DOCS_DIR / f"{doc_id}_{safe_name}.json"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    # Update index
    index = load_index()
    index.append(
        {
            "id": doc_id,
            "name": original_name,
            "file_path": str(dest_file.relative_to(REPO_ROOT)),
            "json_path": str(json_path.relative_to(REPO_ROOT)),
            "document_type": result.get("document_type", "unknown"),
            "uploaded_at": datetime.utcnow().isoformat() + "Z",
        }
    )
    save_index(index)


def main() -> None:
    st.set_page_config(page_title="Document Extractor", page_icon="📄", layout="wide")

    # Sidebar: list of saved documents
    with st.sidebar:
        st.header("Saved documents")
        docs = load_index()
        if not docs:
            st.caption("No documents saved yet.")
        else:
            for d in reversed(docs):
                dt = d.get("document_type", "unknown")
                st.write(f"- **{d['name']}** ({dt})")

    st.title("Document Extractor")
    st.write(
        "Upload a document (TXT, PDF, or image) to extract structured data using "
        "the main Agent Forge orchestrator. Results and files are saved under "
        "`data/documents/`."
    )

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["txt", "pdf", "png", "jpg", "jpeg", "tiff", "bmp"],
    )

    if not uploaded_file:
        return

    st.write(f"**Uploaded file:** {uploaded_file.name}")

    orch = get_orchestrator()

    suffix = Path(uploaded_file.name).suffix or ""
    tmp_path = None

    try:
        # Save upload to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        with st.spinner("Processing document with orchestrator..."):
            result = orch.run_document_extractor(tmp_path)

        # Save file + JSON + index
        save_document_and_result(uploaded_file, tmp_path, result)

        st.subheader("Structured Result")
        st.json(result)

        st.subheader("Raw JSON")
        st.code(json.dumps(result, indent=2), language="json")

    except Exception as e:
        st.error(f"An error occurred while processing the document: {e}")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


if __name__ == "__main__":
    main()
