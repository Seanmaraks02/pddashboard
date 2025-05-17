import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Sales & Interaction Dashboard - Overview", layout="wide")

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
            color: red;
        }
        section[data-testid="stSidebar"] {
            width: 260px;
            padding: 10px;
        }
        .block-container {
            margin-top: -4rem;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
              padding-bottom: 1rem !important;
        }

        svg {
            box-shadow: 0 2px 5px rgba(54, 69, 79, 1); /* Adds shadow to charts */
        }

        .stPlotlyChart {
            box-shadow: 0 2px 5px rgba(54, 69, 79, 1); /* Adds shadow to Plotly charts */
        }

        div[data-testid="stMetric"] {
            box-shadow: 0 2px 5px rgba(54, 69, 79, 1);
        }
    </style>
""", unsafe_allow_html=True)

# Function to get the uploaded data from session state
def get_uploaded_data():
    if "uploaded_data" in st.session_state:
        return st.session_state["uploaded_data"].copy()
    else:
        st.warning("Please upload data on the 'Upload Data' page first.")
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
        st.title("Navigation")
        # Custom navigation links
        st.logo("ai_solutions1.png")
        st.page_link("pages/overview.py", label="Overview", icon=":material/home:")
        st.page_link("pages/sales_interaction_page.py", label="Sales & Interaction", icon=":material/analytics:")
        st.page_link("pages/raw_data_page.py", label="Raw Data", icon=":material/database:")
        

        st.markdown("---")  # Separator

        st.title("Overview Filters")
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

    st.markdown("<h2 style='font-size:25px;'>Executive Summary</h2>", unsafe_allow_html=True)
    # SECTION 1: KPI METRICS
    metrics_con = st.container()
    st.markdown(
        """
        <style>
        [data-testid="stMetricValue"] {
            font-size: 30px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with metrics_con:
        col1, col2, col3, col4, col5= st.columns(5)

        with col1:
            st.metric("Total Visits", df_filtered['session_id'].nunique(), border=True)

        with col2:
            st.metric("Total Purchases", df_filtered[df_filtered['purchased_product'] != "No Purchase"].shape[0], border=True)

        with col3:
            demo_requests = df_filtered[df_filtered['page_name'].str.lower().str.contains("demo")]
            demo_count = demo_requests.shape[0]
            st.metric(label="Scheduled Demo Requests", value=demo_count, border=True)

        with col4:
            st.metric("Avg Visiting Hour", round(df_filtered['hour'].mean(), 2), border=True)

        with col5:
            total_visits = df_filtered['session_id'].nunique()
            demo_count = df_filtered[df_filtered['page_name'].str.lower() == "demo request"].shape[0]
            conversion_rate = (demo_count / total_visits) * 100 if total_visits > 0 else 0
            st.metric("Demo Conversion Rate", f"{conversion_rate:.2f}%", border=True)

    first, second = st.columns ((1.5,2))

    with first:
        daily_visits = df_filtered.groupby(df_filtered['timestamp'].dt.date)['session_id'].nunique().reset_index()
        daily_visits.columns = ['Date', 'Unique Visits']

        fig_visits_area = px.area(
            daily_visits,
            x='Date',
            y='Unique Visits',
            labels={'Unique Visits': 'Number of Visitors', 'Date': 'Date'},
            line_shape='spline',
            title='Website Visits Over Time' # Optional title
        )
        fig_visits_area.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_visits_area, use_container_width=True)

    # Filter out rows with no purchase
        purchases_df = df_filtered[df_filtered['purchased_product'] != "No Purchase"].copy()

        if not purchases_df.empty:
            # Group by month and referrer, then count purchases
            purchases_over_time = purchases_df.groupby([purchases_df['timestamp'].dt.to_period('M').astype(str), 'referrer'])['purchased_product'].count().reset_index()
            purchases_over_time.columns = ['Month', 'Referrer', 'Number of Purchases']

            # Create the line chart with color-coded lines for each referrer
            fig_purchases_referrer_simple = px.line(
                purchases_over_time,
                x='Month',
                y='Number of Purchases',
                color='Referrer',
                title='Monthly Purchases by Referrer',
                labels={'Number of Purchases': 'Number of Purchases', 'Month': 'Month', 'Referrer': 'Traffic Source'},
                markers=True,
            )
            fig_purchases_referrer_simple.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_purchases_referrer_simple, use_container_width=True)
        else:
            st.info("No purchase data available for the selected date range.")

    with second:
        funnel, interest = st.columns(2)

        with funnel:
            total_visits_funnel = df_filtered['session_id'].nunique()
            product_views_funnel = df_filtered[df_filtered['url_category'] == 'products']['session_id'].nunique() # Unique sessions on product pages
            total_purchases_funnel = df_filtered[df_filtered['purchased_product'] != "No Purchase"]['session_id'].nunique() # Unique sessions with a purchase

            funnel_data_primary = pd.DataFrame({
                'stage': ['Visit Website', 'View Product', 'Purchase'],
                'count': [total_visits_funnel, product_views_funnel, total_purchases_funnel]
            })

            fig_funnel_primary = px.funnel(funnel_data_primary, x='count', y='stage',title="Purchase Funnel",)
            fig_funnel_primary.update_layout(height=250,margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_funnel_primary, use_container_width=True)

            if 'user_id' in df.columns:
                # Identify returning customers (users with more than one entry)
                returning_customers = df.groupby('user_id').size()
                returning_customers = returning_customers[returning_customers > 1].index

                # Count new customers (users whose ID is NOT in the returning customers list)
                new_customer_count = df[~df['user_id'].isin(returning_customers)]['user_id'].nunique()

                # Count returning customers (unique users whose ID IS in the returning customers list)
                returning_customer_count = df[df['user_id'].isin(returning_customers)]['user_id'].nunique()

                # Create a DataFrame for the pie chart
                customer_data = pd.DataFrame({
                    'Customer Type': ['New', 'Returning'],
                    'Number of Customers': [new_customer_count, returning_customer_count]
                })

                fig_returning_new = px.pie(
                    customer_data,
                    names='Customer Type',
                    values='Number of Customers',
                    title='Returning vs. New Customers',
                    hole=0.7,
                    color_discrete_sequence=px.colors.qualitative.Set3,
                    labels={'Customer Type': 'Customer Type', 'Number of Customers': 'Number of Customers'}
                )
                fig_returning_new.update_traces(textinfo='percent+label')
                fig_returning_new.update_layout( height=250, showlegend=False, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig_returning_new, use_container_width=True)
            else:
                st.warning("The 'user_id' column is not available to determine returning vs. new customers.")

        with interest:
            interest_con = st.container()
            ai_assistant_interest = int(df_filtered[df_filtered['page_name'].str.lower().str.contains("virtual assistant")]['user_id'].nunique())
            prototyping_interest = int(df_filtered[
                df_filtered['page_name'].str.lower().str.contains("ui/ux design generator") |
                df_filtered['page_name'].str.lower().str.contains("prototyping tool")
            ]['user_id'].nunique())
            crm_interest = int(df_filtered[df_filtered['page_name'].str.lower().str.contains("sales & crm optimization")]['user_id'].nunique())
            software_testing_interest = int(df_filtered[df_filtered['page_name'].str.lower().str.contains("software testing tool")]['user_id'].nunique())
            hr_interest = int(df_filtered[df_filtered['page_name'].str.lower().str.contains("hr & recruitment tool")]['user_id'].nunique())
            document_processor_interest = int(df_filtered[df_filtered['page_name'].str.lower().str.contains("document processor license")]['user_id'].nunique())
            analytics_interest = int(df_filtered[df_filtered['page_name'].str.lower().str.contains("predictive analytics platform")]['user_id'].nunique())

            interest_data_normal = pd.DataFrame({
                "Solution": [
                    "AI Assistant",
                    "Prototyping Tools",
                    "Sales & CRM Optimization",
                    "HR & Recruitment Tool",
                    "Document Processor License",
                    "Predictive Analytics Platform",
                    "Software Testing Tool",
                ],
                "Interest Score": [
                    ai_assistant_interest,
                    prototyping_interest,
                    crm_interest,
                    hr_interest,
                    document_processor_interest,
                    analytics_interest,
                    software_testing_interest,
                ],
            })

            # Format the 'Interest Score' column to display in thousands with 'k'
            interest_data_normal['Interest Score (k)'] = interest_data_normal['Interest Score'].apply(lambda x: f'{x / 1000:.1f}k' if x >= 1000 else str(x))

            fig_interest_horizontal_normal = px.bar(
                interest_data_normal,
                x='Interest Score',
                y='Solution',
                orientation='h',
                title='Interest in Key AI Solutions',
                labels={'Interest Score': 'Number of Visitors', 'Solution': 'AI Solution'},
                text='Interest Score (k)',
            )
            fig_interest_horizontal_normal.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
            fig_interest_horizontal_normal.update_traces(textposition='inside')
            st.plotly_chart(fig_interest_horizontal_normal, use_container_width=True)

            # Filter for rows where a purchase occurred and was processed by a team member
            purchases_with_sales = df[(df['purchased_product'] != 'No Purchase') & (df['processed_by'] != 'Unassigned')]

            if not purchases_with_sales.empty:
                # Group by 'processed_by' and count the number of purchases
                purchases_by_member = purchases_with_sales.groupby('processed_by')['purchased_product'].count().sort_values(ascending=False).reset_index()
                purchases_by_member.columns = ['Sales Team Member', 'Number of Purchases']

                # Create a bar chart
                fig_purchases_by_member = px.bar(
                    purchases_by_member,
                    x='Sales Team Member',
                    y='Number of Purchases',
                    title='Total Purchases by Sales Team Member',
                    labels={'Sales Team Member': 'Sales Team Member', 'Number of Purchases': 'Number of Purchases'},
                    color_continuous_scale=None
                )
                fig_purchases_by_member.update_layout(height=250, showlegend = False, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig_purchases_by_member, use_container_width=True)
            else:
                st.info("No purchases have been attributed to specific sales team members in the current data.")

else:
    st.info("Please upload data on the 'Upload Data' page first.")
    st.stop()