import json
from pathlib import Path
from typing import Any, Dict

import streamlit as st

try:
    import doc_extractor
except ImportError as e:
    st.error(f"Missing required module 'doc_extractor': {e}")
    raise

@st.cache_data
def load_document(path: Path) -> Dict[str, Any]:
    """
    Calls the backend doc_extractor.process function and returns its result.
    """
    return doc_extractor.process(str(path))

def display_results(result: Dict[str, Any]) -> None:
    """
    Render the result dictionary in a Streamlit-friendly format.
    """
    st.subheader("Document Extraction Result")
    st.json(result)

    # Detailed view for each field if available
    if "extracted_fields" in result:
        st.subheader("Extracted Fields")
        for key, value in result["extracted_fields"].items():
            st.markdown(f'**{key}**: {json.dumps(value, indent=2)}')

    if "metadata" in result:
        st.subheader("Metadata")
        for key, value in result["metadata"].items():
            st.markdown(f'**{key}**: {json.dumps(value, indent=2)}')

def main() -> None:
    st.title("Doc Extractor GUI")
    st.write("Upload a document or provide a file path to extract information.")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            label="Upload a file",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=False,
        )

    with col2:
        path_input = st.text_input(
            label="Or enter a file path",
            placeholder="C:/path/to/document.pdf",
        )
        run_button = st.button("Process")

    if run_button:
        if uploaded_file is not None:
            # Write the uploaded file to a temporary location to obtain a path
            temp_path = Path("./temp_uploaded_file")
            temp_path.write_bytes(uploaded_file.getvalue())
            path = temp_path
        elif path_input:
            path = Path(path_input)
        else:
            st.warning("Please provide a file by upload or path input.")
            return

        if not path.exists():
            st.error(f"Path does not exist: {path}")
            return

        try:
            result = load_document(path)
            display_results(result)
        except Exception as exc:
            st.error(f"An error occurred while processing the document: {exc}")

        finally:
            # Clean up temporary file if it was created
            if 'temp_path' in locals() and temp_path.exists():
                temp_path.unlink(missing_ok=True)

if __name__ == "__main__":
    main()