import streamlit as st
import pandas as pd

st.set_page_config(page_title="Upload Data", layout="wide")
st.markdown("""
    <style>
          [data-testid="stSidebarNav"] {
        display: none;
    }
    section[data-testid="stSidebar"] {
        width: 260px;
        padding: 10px;
    }
        .block-container {
            margin-top: -4rem;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
    </style>
    
""", unsafe_allow_html=True)
with st.sidebar:
            # Custom navigation links
            
            # st.page_link("pages/overview.py", label="Overview", icon=":material/home:")
            # st.page_link("pages/sales_interaction_page.py", label="Sales & Interaction", icon=":material/analytics:")
            # st.page_link("pages/raw_data_page.py", label="Raw Data", icon=":material/database:")
            st.page_link("upload.py", label="Upload Data", icon=":material/upload:")


            st.markdown("---")  # Separator

st.title("Welcome to the Dashboard!")
st.subheader("Please upload your web data logs in CSV format to proceed.")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, parse_dates=["timestamp"])
        st.session_state["uploaded_data"] = df
        st.success("Data uploaded successfully!")
        st.info("You can now navigate to the other pages in the sidebar.")
        st.switch_page("pages/overview.py")
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
else:
    st.info("Waiting for file upload...")
