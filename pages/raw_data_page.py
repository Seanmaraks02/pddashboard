import streamlit as st
import pandas as pd

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

# Function to get the uploaded data from session state
def get_uploaded_data():
    if "uploaded_data" in st.session_state:
        return st.session_state["uploaded_data"].copy()
    else:
        st.warning("Please upload data on the 'Upload Data' page first.")
        st.page_link("upload.py", label="Upload Data", icon=":material/upload:")
        return None

df = get_uploaded_data()

if df is not None:
    try:
        df['date'] = df['timestamp'].dt.date
        df['month'] = df['timestamp'].dt.to_period("M").astype(str)
        df['year'] = df['timestamp'].dt.year
        df['hour'] = df['timestamp'].dt.hour
    except AttributeError as e:
        st.error(f"Data processing error: {e}")
        st.stop()

with st.sidebar:
    st.logo("ai_solutions1.png")
        # Custom navigation links
    st.page_link("pages/overview.py", label="Overview",  icon=":material/home:")
    st.page_link("pages/sales_interaction_page.py", label="Sales & Interaction", icon=":material/analytics:")
    st.page_link("pages/raw_data_page.py", label="Raw Data", icon=":material/database:")
    


    st.markdown("---")
    st.title("Raw Data Filters")
    min_date = df['timestamp'].min().date()
    max_date = df['timestamp'].max().date()
    date_range = st.date_input("Select date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        df_filtered = df[(df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)].copy()
    else:
        st.warning("Please select a valid date range in the sidebar.")
        df_filtered = df.copy()
    country_list = df['country'].dropna().unique().tolist()
    selected_countries = st.multiselect("Filter by Country", options=country_list, default=[])
    if selected_countries:
        df_filtered = df_filtered[df_filtered['country'].isin(selected_countries)]
    if 'processed_by' in df.columns:
        sales_person_list = df['processed_by'].dropna().unique().tolist()
        selected_sales_persons = st.multiselect("Filter by Sales Person", options=sales_person_list, default=[])
        if selected_sales_persons:
            df_filtered = df_filtered[df_filtered['processed_by'].isin(selected_sales_persons)]
    else:
        st.warning("The 'processed_by' column is not available in the dataset.")

        # Product filter
    if 'purchased_product' in df.columns:
        # Exclude "No Purchase" from the product list
        product_list = df[df['purchased_product'] != "No Purchase"]['purchased_product'].dropna().unique().tolist()

        selected_products = st.multiselect("Filter by Product", options=product_list, default=[])
        if selected_products:
            df_filtered = df_filtered[df_filtered['purchased_product'].isin(selected_products)]

            
    # Quarter filter
    if 'timestamp' in df.columns:
        # Ensure 'timestamp' is in datetime format
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['quarter'] = df['timestamp'].dt.to_period("Q").astype(str)  # Extract quarter information (e.g., "2025Q1")
        df_filtered['quarter'] = df['quarter']
        quarter_list = df['quarter'].dropna().unique().tolist()
        selected_quarters = st.multiselect("Filter by Quarter", options=quarter_list, default=[])
        if selected_quarters:
            df_filtered = df_filtered[df_filtered['quarter'].isin(selected_quarters)]



st.title("Raw Data")
st.write("Below is the raw data based on the applied filters.")
st.dataframe(df_filtered)


def convert_df_to_csv(data_frame):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return data_frame.to_csv().encode('utf-8')

csv_data = convert_df_to_csv(df_filtered)

st.download_button(
    label="Download as CSV",
    data=csv_data,
    file_name='filtered_data.csv',
    mime='text/csv',
)
