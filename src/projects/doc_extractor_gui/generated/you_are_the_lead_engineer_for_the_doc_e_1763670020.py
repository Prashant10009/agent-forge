import json
import re
import streamlit as st
from pathlib import Path
from datetime import datetime
import doc_extractor

def create_output_dir():
    """Create outputs directory if it doesn't exist"""
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    return output_dir

def make_safe_filename(filename):
    """Convert filename to safe string with only letters, numbers and underscores"""
    base = Path(filename).stem
    return re.sub(r'[^\w]', '_', base)

def save_result(result, original_filename, output_dir):
    """Save result to JSON file with timestamp"""
    safe_name = make_safe_filename(original_filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{safe_name}_{timestamp}.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    return output_path

def main():
    st.title("Document Extractor")
    
    uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx", "txt"])
    
    if uploaded_file is not None:
        with st.spinner("Processing document..."):
            # Save uploaded file to temp location
            tmp_path = Path("/tmp") / uploaded_file.name
            with open(tmp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Process document
            result = doc_extractor.process(tmp_path)
            
            # Create output directory
            output_dir = create_output_dir()
            
            # Save result to JSON file
            output_path = save_result(result, uploaded_file.name, output_dir)
            
            # Display results
            st.success(f"Document processed successfully! Results saved to {output_path}")
            
            # Show full result as JSON
            st.subheader("Full Result")
            st.json(result)
            
            # Full extracted text section
            with st.expander("Full extracted text"):
                full_text = result.get("full_text", "")
                if full_text:
                    st.text_area("Extracted content", full_text, height=300)
                else:
                    st.info("No full_text returned by the extractor.")
            
            # Extracted fields section
            with st.expander("Extracted fields"):
                fields = result.get("extracted_fields", {})
                if fields:
                    st.json(fields)
                else:
                    st.info("No extracted_fields returned by the extractor.")

if __name__ == "__main__":
    main()