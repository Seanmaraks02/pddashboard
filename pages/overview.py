import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

st.set_page_config(page_title="Sales & Interaction Dashboard - Overview", layout="wide")

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
            padding-bottom: 1rem !important;
        }

        svg {
            box-shadow: 0 2px 5px rgba(54, 69, 79, 1); /* Adds shadow to charts */
        }

        .stPlotlyChart {
            box-shadow: 0 2px 5px rgba(54, 69, 79, 1); /* Adds shadow to Plotly charts */
        }

        /* Styles for the custom metric cards */
        .custom-metric-card {
            box-shadow: 0 2px 5px rgba(54, 69, 79, 1);
            border-radius: 2px;
            padding: 10px; /* Reduced padding */
            margin-bottom: 5px; /* Reduced space between cards */
           
            display: flex;
            align-items: center;
            flex-direction: column;
            justify-content: center;
        }

        .custom-metric-card .title {
            font-size: 18px; /* Reduced font size */
            color: grey;
        }

        .custom-metric-card .value {
            font-weight: bold;
            font-size: 20px; /* Reduced font size */
           
        }

        .custom-metric-card .delta-text {
            font-size: 12px; /* Reduced font size */
            font-weight: bold;
            color: #555; /* Default delta color */
        }

        /* Performance-based background/border colors for the whole card */
        .metric-good {
            border: 2px solid #00FF00; /* Green border */
            background-color: rgba(0, 255, 0, 0.1); /* Light green background */
        }
        .metric-amber {
            border: 2px solid #FFA500; /* Amber border */
            background-color: rgba(255, 165, 0, 0.1); /* Light amber background */
        }
        .metric-bad {
            border: 2px solid #FF0000; /* Red border */
            background-color: rgba(255, 0, 0, 0.1); /* Light red background */
        }

        /* Optional: Change the value text color based on performance */
        .metric-good .value, .metric-good .delta-text {
            color: #008000; /* Darker green text */
        }
        .metric-amber .value, .metric-amber .delta-text {
            color: #CC8400; /* Darker amber text */
        }
        .metric-bad .value, .metric-bad .delta-text {
            color: #CC0000; /* Darker red text */
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
        # Ensure 'timestamp' is datetime if it's not already
        if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df.dropna(subset=['timestamp'], inplace=True) # Remove rows with invalid timestamps

        # Sort by timestamp for consistent time-based filtering later
        df = df.sort_values(by='timestamp').reset_index(drop=True)

        df['date'] = df['timestamp'].dt.date
        df['month'] = df['timestamp'].dt.to_period("M").astype(str)
        df['year'] = df['timestamp'].dt.year
        df['hour'] = df['timestamp'].dt.hour
        df['quarter'] = df['timestamp'].dt.quarter.astype(str) + 'Q' + df['timestamp'].dt.year.astype(str)

    except AttributeError as e:
        st.error(f"Data processing error: {e}. Please ensure 'timestamp' column is present and in a compatible format.")
        st.stop()
    except KeyError as e:
        st.error(f"Missing expected column: {e}. Please check your data.")
        st.stop()

    with st.sidebar:
        st.title("Navigation")
        st.logo("ai_solutions1.png")
        st.page_link("pages/overview.py", label="Overview", icon=":material/home:")
        st.page_link("pages/sales_interaction_page.py", label="Sales & Interaction", icon=":material/analytics:")
        st.page_link("pages/raw_data_page.py", label="Raw Data", icon=":material/database:")

        st.markdown("---")

        st.title("Overview Filters")
        min_available_date = df['timestamp'].min().date()
        max_available_date = df['timestamp'].max().date()

        df_filtered = df.copy() 
        
        default_start_date = min_available_date
        default_end_date = max_available_date

        date_range_selection = st.date_input("Select date range",
                                             value=(default_start_date, default_end_date), 
                                             min_value=min_available_date,
                                             max_value=max_available_date)

        start_date_current = None
        end_date_current = None

        if isinstance(date_range_selection, tuple) and len(date_range_selection) == 2:
            start_date_current, end_date_current = date_range_selection
            if (start_date_current != default_start_date) or (end_date_current != default_end_date):
                df_filtered = df[(df['timestamp'].dt.date >= start_date_current) & (df['timestamp'].dt.date <= end_date_current)].copy()
        else:
            st.warning("Please select a valid date range in the sidebar to view filtered data.")

        country_list = df['country'].dropna().unique().tolist()
        selected_countries = st.multiselect("Filter by Country", options=country_list, default=[])
        if selected_countries:
            df_filtered = df_filtered[df_filtered['country'].isin(selected_countries)]

    

    st.markdown("<h2 style='font-size:25px;'>Executive Summary</h2>", unsafe_allow_html=True)

    # --- KPI METRICS ---
    metrics_con = st.container()
    
    with metrics_con:
        col1, col2, col3, col4 = st.columns(4)

        # --- Define Your Fixed Targets / Benchmarks Here ---
        TARGETS = {
            "Total Visits": {"annual": 450000, "monthly": 41600, "daily": 1360},
            "Total Purchases": {"annual": 100000, "monthly": 8700, "daily": 286},
            "Scheduled Demo Requests": {"annual": 25000, "monthly": 2600, "daily": 85}, 
            
            "Demo Conversion Rate": 3 
        }
        
        # Define thresholds for color coding based on target (as percentages or absolute points of the target)
        THRESHOLDS = {
            "Total Visits": {"good_factor": 1.10, "amber_lower_factor": 0.95},
            "Total Purchases": {"good_factor": 1.08, "amber_lower_factor": 0.96},
            "Scheduled Demo Requests": {"good_factor": 1.05, "amber_lower_factor": 0.95}, 
            "Demo Conversion Rate": {"good_add": 1.0, "amber_lower_add": -0.5}, 
             
        }

        # --- Helper function to determine the appropriate target based on filtered data duration ---
        def get_appropriate_target_value(kpi_name, filtered_df, targets_dict, start_date, end_date):
            if not isinstance(targets_dict.get(kpi_name), dict):
                return targets_dict.get(kpi_name, 0) 

            if filtered_df.empty or start_date is None or end_date is None:
                return 0 
            
            duration = (end_date - start_date).days + 1 

            if duration <= 1: 
                return targets_dict[kpi_name].get("daily", 0)
            elif duration <= 31: 
                return targets_dict[kpi_name].get("monthly", 0)
            elif duration > 300: 
                return targets_dict[kpi_name].get("annual", 0)
            else: 
                return targets_dict[kpi_name].get("monthly", 0)


        # --- Helper function to calculate performance against target and determine CSS class and delta text ---
        def get_performance_details(kpi_name, current_value, filtered_df, targets_dict, thresholds_dict, start_date, end_date):
            target_value = get_appropriate_target_value(kpi_name, filtered_df, targets_dict, start_date, end_date)
            
            delta_text = "N/A"
            css_class = "metric-off" # Default to no specific color if no target or logic not met

            if target_value == 0:
                # If no target, provide a simple delta and 'off' class
                delta_text = "Target N/A"
                if current_value > 0:
                    delta_text = f"Value: {current_value:,}" # Just show value if no target
                return delta_text, "metric-off" 

            difference = current_value - target_value
            
            if kpi_name == "Demo Conversion Rate" or kpi_name == "Avg Visiting Hour":
                # For metrics with absolute point thresholds
                good_threshold = target_value + thresholds_dict[kpi_name]["good_add"]
                amber_lower_threshold = target_value + thresholds_dict[kpi_name]["amber_lower_add"]

                if current_value >= good_threshold:
                    css_class = "metric-good"
                elif current_value >= amber_lower_threshold:
                    css_class = "metric-amber"
                else:
                    css_class = "metric-bad"
                
                # Format delta based on points or hours for Avg Visiting Hour
                if kpi_name == "Demo Conversion Rate":
                    delta_text = f"{difference:+.2f} pts"
                elif kpi_name == "Avg Visiting Hour":
                    delta_text = f"{difference:+.2f} hrs"


            else:
                # For metrics with percentage factor thresholds
                good_factor = thresholds_dict.get(kpi_name, {}).get("good_factor", 1.0) 
                amber_lower_factor = thresholds_dict.get(kpi_name, {}).get("amber_lower_factor", 1.0) 

                good_threshold = target_value * good_factor
                amber_lower_threshold = target_value * amber_lower_factor

                if current_value >= good_threshold:
                    css_class = "metric-good"
                elif current_value >= amber_lower_threshold:
                    css_class = "metric-amber"
                else:
                    css_class = "metric-bad"

                percent_diff = (difference / target_value) * 100 if target_value != 0 else (100 if difference > 0 else 0)
                delta_text = f"{percent_diff:+.2f}%"

            return delta_text, css_class

        # --- KPI Calculations for Current Period ---
        current_total_visits = df_filtered['session_id'].nunique()
        current_total_purchases = df_filtered[df_filtered['purchased_product'] != "No Purchase"].shape[0]
        current_demo_count = df_filtered[df_filtered['page_name'].str.lower().str.contains("demo")].shape[0]
        current_avg_visiting_hour = round(df_filtered['hour'].mean(), 2) if not df_filtered.empty else 0
        
        current_total_visits_for_conversion = df_filtered['session_id'].nunique()
        current_demo_requests_for_conversion = df_filtered[df_filtered['page_name'].str.lower() == "demo request"].shape[0]
        current_conversion_rate = (current_demo_requests_for_conversion / current_total_visits_for_conversion) * 100 if current_total_visits_for_conversion > 0 else 0

        # Function to render custom metric card
        def render_metric_card(parent_col, title, value, kpi_name, df_filtered, targets, thresholds, start_date, end_date, formatter="{:,}"):
            delta_text, css_class = get_performance_details(kpi_name, value, df_filtered, targets, thresholds, start_date, end_date)
            
            # Apply specific formatting for value based on KPI
            display_value = ""
            if kpi_name == "Avg Visiting Hour":
                display_value = f"{value:.2f}"
            elif kpi_name == "Demo Conversion Rate":
                display_value = f"{value:.2f}%"
            else:
                display_value = formatter.format(value)

            with parent_col:
                st.markdown(f"""
                <div class="custom-metric-card {css_class}">
                    <div class="title">{title}</div>
                    <div class="value">{display_value}</div>
                    <div class="delta-text">{delta_text}</div>
                </div>
                """, unsafe_allow_html=True)

        render_metric_card(col1, "Total Visits", current_total_visits, "Total Visits", df_filtered, TARGETS, THRESHOLDS, start_date_current, end_date_current)
        render_metric_card(col2, "Total Purchases", current_total_purchases, "Total Purchases", df_filtered, TARGETS, THRESHOLDS, start_date_current, end_date_current)
        render_metric_card(col3, "Scheduled Demos", current_demo_count, "Scheduled Demo Requests", df_filtered, TARGETS, THRESHOLDS, start_date_current, end_date_current)
        render_metric_card(col4, "Conversion Rate", current_conversion_rate, "Demo Conversion Rate", df_filtered, TARGETS, THRESHOLDS, start_date_current, end_date_current)


    first, second = st.columns((1.5, 2))

    with first:
        daily_visits = df_filtered.groupby(df_filtered['timestamp'].dt.date)['session_id'].nunique().reset_index()
        daily_visits.columns = ['Date', 'Unique Visits']

        fig_visits_area = px.area(
            daily_visits,
            x='Date',
            y='Unique Visits',
            labels={'Unique Visits': 'Number of Visitors', 'Date': 'Date'},
            line_shape='spline',
            title='Website Visits Over Time'
        )
        fig_visits_area.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_visits_area, use_container_width=True)

        purchases_df = df_filtered[df_filtered['purchased_product'] != "No Purchase"].copy()

        if not purchases_df.empty:
            purchases_over_time = purchases_df.groupby([purchases_df['timestamp'].dt.to_period('M').astype(str), 'referrer'])['purchased_product'].count().reset_index()
            purchases_over_time.columns = ['Month', 'Referrer', 'Number of Purchases']

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
            product_views_funnel = df_filtered[df_filtered['url_category'] == 'products']['session_id'].nunique()
            total_purchases_funnel = df_filtered[df_filtered['purchased_product'] != "No Purchase"]['session_id'].nunique()

            funnel_data_primary = pd.DataFrame({
                'stage': ['Visit Website', 'View Product', 'Purchase'],
                'count': [total_visits_funnel, product_views_funnel, total_purchases_funnel]
            })

            fig_funnel_primary = px.funnel(funnel_data_primary, x='count', y='stage', title="Purchase Funnel",)
            fig_funnel_primary.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_funnel_primary, use_container_width=True)

            if 'user_id' in df.columns:
                returning_customers_filtered = df_filtered.groupby('user_id').size()
                returning_customers_filtered = returning_customers_filtered[returning_customers_filtered > 1].index

                new_customer_count_filtered = df_filtered[~df_filtered['user_id'].isin(returning_customers_filtered)]['user_id'].nunique()
                returning_customer_count_filtered = df_filtered[df_filtered['user_id'].isin(returning_customers_filtered)]['user_id'].nunique()

                customer_data = pd.DataFrame({
                    'Customer Type': ['New', 'Returning'],
                    'Number of Customers': [new_customer_count_filtered, returning_customer_count_filtered]
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

            interest_data_normal['Interest Score (k)'] = interest_data_normal['Interest Score'].apply(lambda x: f'{x / 1000:.1f}k' if x >= 1000 else str(x))

            fig_interest_horizontal_normal = px.bar(
                interest_data_normal,
                x='Interest Score',
                y='Solution',
                orientation='h',
                title='Interest in Key Products',
                labels={'Interest Score': 'Number of Visitors', 'Solution': 'Product'},
                text='Interest Score (k)',
            )
            fig_interest_horizontal_normal.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
            fig_interest_horizontal_normal.update_traces(textposition='inside')
            st.plotly_chart(fig_interest_horizontal_normal, use_container_width=True)

            purchases_with_sales = df_filtered[(df_filtered['purchased_product'] != 'No Purchase') & (df_filtered['processed_by'] != 'Unassigned')]

            if not purchases_with_sales.empty:
                purchases_by_member = purchases_with_sales.groupby('processed_by')['purchased_product'].count().sort_values(ascending=False).reset_index()
                purchases_by_member.columns = ['Sales Team Member', 'Number of Purchases']

                fig_purchases_by_member = px.bar(
                    purchases_by_member,
                    x='Sales Team Member',
                    y='Number of Purchases',
                    title='Total Purchases by Sales Team Member',
                    labels={'Sales Team Member': 'Sales Team Member', 'Number of Purchases': 'Number of Purchases'},
                    color_continuous_scale=None
                )
                fig_purchases_by_member.update_layout(height=250, showlegend=False, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig_purchases_by_member, use_container_width=True)
            else:
                st.info("No purchases have been attributed to specific sales team members in the current data.")

else:
    st.info("Please upload data on the 'Upload Data' page first.")
    st.stop()
