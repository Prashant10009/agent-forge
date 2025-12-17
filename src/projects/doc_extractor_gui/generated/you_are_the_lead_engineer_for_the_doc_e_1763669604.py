import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import doc_extractor
import re

def sanitize_filename(filename):
    """Convert filename to safe characters only (letters, numbers, underscore)"""
    base = Path(filename).stem
    return re.sub(r'[^\w]', '_', base)

def save_result_to_json(result, original_filename):
    """Save extraction result to JSON file in outputs/ directory"""
    outputs_dir = Path(__file__).parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = sanitize_filename(original_filename)
    output_path = outputs_dir / f"{safe_name}_{timestamp}.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    return str(output_path.relative_to(Path(__file__).parent))

def display_extracted_fields(fields):
    """Render extracted fields in a structured way"""
    if not fields:
        st.info("No fields were extracted from this document")
        return
    
    st.subheader("Extracted Fields")
    st.json(fields)

def display_full_text(text):
    """Show full extracted text in scrollable area"""
    st.subheader("Full Extracted Text")
    st.text_area(
        "Document Content", 
        value=text or "No text extracted", 
        height=300,
        disabled=True
    )

def main():
    st.title("Document Extractor GUI")
    uploaded_file = st.file_uploader("Upload a document", type=None)

    if uploaded_file is not None:
        # Save to temp file for processing
        temp_path = Path("temp_upload") / uploaded_file.name
        temp_path.parent.mkdir(exist_ok=True)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            # Process document using doc_extractor
            result = doc_extractor.process(str(temp_path))
            
            # Display document type and confidence
            doc_type = result.get("document_type", "Unknown")
            confidence = result.get("classification_confidence", 0)
            st.subheader(f"Document Type: {doc_type} (confidence: {confidence:.2%})")
            
            # Display extracted content sections
            display_full_text(result.get("full_text", ""))
            display_extracted_fields(result.get("extracted_fields", {}))
            
            # Show raw JSON (collapsed by default)
            with st.expander("Raw Extraction Result"):
                st.json(result)
            
            # Save results and show path
            output_path = save_result_to_json(result, uploaded_file.name)
            st.success(f"Saved full extraction to: {output_path}")
            
        except Exception as e:
            st.error(f"Error processing document: {str(e)}")
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()

if __name__ == "__main__":
    main()