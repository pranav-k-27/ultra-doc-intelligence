"""
Streamlit UI: Simple, professional interface
"""
import streamlit as st
import requests
import json
import os

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="Ultra Doc Intelligence",
    page_icon="🚚",
    layout="wide"
)

# Title
st.title("🚚 Ultra Doc Intelligence")
st.markdown("*AI-powered logistics document analysis*")
st.divider()

# Initialize session state
if 'reference_id' not in st.session_state:
    st.session_state.reference_id = ""

# Sidebar - Upload
with st.sidebar:
    st.header("📄 Upload Document")
    st.markdown("Upload logistics documents (Rate Confirmation, BOL, etc.)")
    
    uploaded_file = st.file_uploader(
        "Choose PDF file",
        type=['pdf'],
        help="Upload Rate Confirmation or Bill of Lading"
    )
    
    if uploaded_file and st.button("🚀 Process Document", use_container_width=True):
        with st.spinner("Processing document..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                response = requests.post(f"{API_URL}/upload", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ Processed successfully!")
                    st.info(f"**Reference ID:** {result.get('reference_id', 'N/A')}")
                    st.info(f"**Document Type:** {result.get('doc_type', 'N/A')}")
                    st.info(f"**Chunks Created:** {result.get('chunks', 0)}")
                    
                    if result.get('reference_id'):
                        st.session_state.reference_id = result['reference_id']
                else:
                    st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
            
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API. Make sure to run: `python app.py`")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    
    # ADD CLEAR BUTTON HERE ⬇️
    # ADD CLEAR BUTTON HERE ⬇️
    if st.button("🗑️ Clear All Data", use_container_width=True, type="secondary", key='clear_btn'):
        st.warning("⚠️ **To clear all data, follow these steps:**")
        st.markdown("""
        **Step 1:** Stop the API
        - Go to the terminal running `python app.py`
        - Press `Ctrl+C`
        
        **Step 2:** Delete the database folder
        """)
        st.code("""rmdir /s /q data\\chroma_db
    mkdir data\\chroma_db""", language="bash")
        
        st.markdown("**Step 3:** Restart the API")
        st.code("python app.py", language="bash")
        
        st.info("💡 **Why?** The API keeps database files open, so they must be closed before deletion.")
        
        # Clear session state (this is safe)
        st.session_state.reference_id = ""

    st.divider()
    st.markdown("### 💡 Quick Guide")
    st.markdown("""
    1. **Upload** a logistics PDF
    2. **Ask questions** about it
    3. **Extract** structured data
    """)

# Main area - Tabs
tab1, tab2 = st.tabs(["💬 Ask Questions", "📊 Extract Data"])

# Tab 1: Ask Questions
with tab1:
    st.subheader("Ask Questions About Your Documents")
    
    # Question input
    question = st.text_input(
        "Your question:",
        placeholder="e.g., What is the carrier rate?",
        help="Ask natural language questions about uploaded documents"
    )
    
    reference_id_input = st.text_input(
        "Reference ID (optional):",
        value=st.session_state.reference_id,
        placeholder="e.g., LD53657"
    )
    
    # Example questions - Simple version that works
    st.markdown("**Quick Examples:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("- What is the carrier rate?")
        st.markdown("- Who is the carrier?")
    with col2:
        st.markdown("- When is the pickup scheduled?")
        st.markdown("- What is the delivery address?")
    with col3:
        st.markdown("- What commodity is being shipped?")
        st.markdown("- What is the weight?")
    
    st.markdown("---")
    
    ask_clicked = st.button("🔍 Ask", type="primary", use_container_width=True, key='ask_btn')

    if ask_clicked and question:
        with st.spinner("Searching documents..."):
            try:
                data = {
                    "question": question,
                    "reference_id": reference_id_input if reference_id_input else None
                }
                response = requests.post(f"{API_URL}/ask", data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display answer
                    st.markdown("### 📝 Answer")
                    st.write(result['answer'])
                    
                    # Display confidence
                    conf = result['confidence']
                    if conf > 0.7:
                        color = "🟢"
                        label = "High"
                    elif conf > 0.5:
                        color = "🟡"
                        label = "Medium"
                    else:
                        color = "🔴"
                        label = "Low"
                    
                    st.metric("Confidence Score", f"{color} {conf}", label)
                    
                    # Display sources
                    if result.get('sources'):
                        st.markdown("### 📚 Sources")
                        for i, source in enumerate(result['sources'], 1):
                            with st.expander(f"Source {i} - {source.get('doc_type', 'unknown')} ({source.get('section', 'unknown')})"):
                                st.text(source['content'])
                                st.caption(f"Distance: {source.get('distance', 'N/A')}")
                else:
                    st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
            
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API. Make sure to run: `python app.py`")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Tab 2: Extract Data
# Tab 2: Extract Data
with tab2:
    st.subheader("Extract Structured Data")
    
    extract_ref_id = st.text_input(
        "Reference ID for extraction:",
        value=st.session_state.reference_id,
        placeholder="e.g., LD53657",
        key="extract_ref_id"
    )
    
    if st.button("🔄 Extract Data", type="primary", use_container_width=True):
        if not extract_ref_id:
            st.error("❌ Please enter a Reference ID")
        else:
            with st.spinner("Extracting structured data..."):
                try:
                    
                    
                    data = {"reference_id": extract_ref_id}
                    response = requests.post(f"{API_URL}/extract", data=data)
                    
                    
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.markdown("### 📋 Extracted Fields")
                        st.json(result)
                        
                        # Download button
                        json_str = json.dumps(result, indent=2)
                        st.download_button(
                            label="⬇️ Download JSON",
                            data=json_str,
                            file_name=f"{extract_ref_id}_extracted.json",
                            mime="application/json",
                            use_container_width=True
                        )
                        
                        # Display summary
                        st.markdown("### 📊 Field Summary")
                        col1, col2 = st.columns(2)
                        
                        fields = [
                            "shipment_id", "shipper", "consignee", "pickup_datetime",
                            "delivery_datetime", "equipment_type", "mode", "rate",
                            "currency", "weight", "carrier_name"
                        ]
                        
                        for i, field in enumerate(fields):
                            with col1 if i % 2 == 0 else col2:
                                value = result.get(field, "null")
                                status = "✅" if value and value != "null" and value != "None" else "❌"
                                st.text(f"{status} {field}: {value}")
                    else:
                        error_detail = response.json().get('detail', 'Unknown error')
                        st.error(f"❌ API Error: {error_detail}")
                        st.code(response.text)  # DEBUG - show raw response
                
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API. Make sure API is running!")
                except Exception as e:
                    st.error(f"❌ Unexpected Error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())  # DEBUG - show full error

# Footer
st.divider()
st.caption("Ultra Doc Intelligence v1.0 | Built for logistics document analysis")