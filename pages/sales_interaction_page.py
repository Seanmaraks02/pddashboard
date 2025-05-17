import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pycountry

st.set_page_config(page_title="Sales & Interaction Dashboard - Sales & Interaction", layout="wide")

# Constants
GAUGE_MULTIPLIER = 1.5

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
    # Add a logo at the top of the sidebar
    st.logo("ai_solutions1.png")


    st.title("Navigation")
    # Custom navigation links
    st.page_link("pages/overview.py", label="Overview", icon=":material/home:")
    st.page_link("pages/sales_interaction_page.py", label="Sales & Interaction", icon=":material/analytics:")
    st.page_link("pages/raw_data_page.py", label="Raw Data", icon=":material/database:")

    st.markdown("---")
    st.title("Sales & Interaction Filters")

    # Date range filter
    min_date = df['timestamp'].min().date()
    max_date = df['timestamp'].max().date()
    date_range = st.date_input("Select date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        df_filtered = df[(df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)].copy()
    else:
        st.warning("Please select a valid date range in the sidebar.")
        df_filtered = df.copy()

    # Country filter
    country_list = df['country'].dropna().unique().tolist()
    selected_countries = st.multiselect("Filter by Country", options=country_list, default=[])
    if selected_countries:
        df_filtered = df_filtered[df_filtered['country'].isin(selected_countries)]

    
    # Salesperson filter
    if 'processed_by' in df.columns:
        # Exclude "Unassigned" from the list of salespersons
        sales_person_list = df['processed_by'].dropna().unique().tolist()
        sales_person_list = [person for person in sales_person_list if person.lower() != "unassigned"]  # Exclude "Unassigned"

        selected_sales_persons = st.multiselect("Filter by Sales Person", options=sales_person_list, default=[])
        if selected_sales_persons:
            df_filtered = df_filtered[df_filtered['processed_by'].isin(selected_sales_persons)]

    
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

        # Create a 'quarter' column dynamically in the original DataFrame
        df['quarter'] = df['timestamp'].dt.to_period("Q").astype(str)  # Extract quarter information (e.g., "2025Q1")

        # Ensure the 'quarter' column is also in the filtered DataFrame
        df_filtered['quarter'] = df['quarter']

        # Get unique quarters for the filter
        quarter_list = df['quarter'].dropna().unique().tolist()

        # Add a multiselect filter for quarters
        selected_quarters = st.multiselect("Filter by Quarter", options=quarter_list, default=[])

        # Apply the filter if quarters are selected
        if selected_quarters:
            df_filtered = df_filtered[df_filtered['quarter'].isin(selected_quarters)]

sales_tab1, sales_tab2 = st.tabs(["Sales Performance", "Customer Interaction"])

with sales_tab1:
    # st.markdown("<h2 style='font-size:23px;'>Sale Performance Overview</h2>", unsafe_allow_html=True)
    col_sales1, col_sales2 = st.columns((1.5, 1))

    with col_sales1:
        
        # Step 1: Define gauge_data — now includes quarter + product + country filters
        gauge_data = df.copy()

        # Apply quarter filter
        if 'quarter' in df.columns and selected_quarters:
            gauge_data = gauge_data[gauge_data['quarter'].isin(selected_quarters)]

        # Apply product filter
        if 'purchased_product' in df.columns and selected_products:
            gauge_data = gauge_data[gauge_data['purchased_product'].isin(selected_products + ["No Purchase"])]

        # Apply country filter
        if 'country' in df.columns and selected_countries:
            gauge_data = gauge_data[gauge_data['country'].isin(selected_countries)]

        # Step 2: Now calculate team average sales and gauge range from the gauge_data (quarter + product + country filtered)
        if gauge_data is not None and 'processed_by' in gauge_data.columns and gauge_data['processed_by'].dropna().nunique() > 0:
            total_sales = gauge_data[gauge_data['purchased_product'] != "No Purchase"]['purchased_product'].count()
            num_salespersons = gauge_data['processed_by'].nunique()
            avg_team_sales_filtered = total_sales / num_salespersons
            max_team_gauge_value = avg_team_sales_filtered * 2

            fig_gauge = go.Figure()

            if not selected_sales_persons or len(selected_sales_persons) > 1:
                # Team-level gauge value based on all filters (quarter, product, country)
                team_value = df_filtered[df_filtered['purchased_product'] != "No Purchase"]['purchased_product'].count()
                team_divisor = df_filtered['processed_by'].nunique()
                team_value_avg = team_value / team_divisor if team_divisor else 0

                fig_gauge.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=team_value_avg,
                    title={
                        "text": "Average Team Sales<br><span style='font-size:14px; color:gray;'>Tip: Filter by salesperson for individual performance</span>",
                        "font": {"size": 16, "weight": "bold"}
                    },
                    gauge={
                        "axis": {"range": [0, max(max_team_gauge_value, 1)]},
                        "bar": {"color": "rgba(0,0,0,0)"},
                        "steps": [
                            {"range": [0, avg_team_sales_filtered * 0.8], "color": "rgba(255, 99, 71, 0.8)"},  # Softer red
                            {"range": [avg_team_sales_filtered * 0.8, avg_team_sales_filtered * 1.2], "color": "rgba(255, 165, 0, 0.8)"},  # Softer orange
                            {"range": [avg_team_sales_filtered * 1.2, max_team_gauge_value], "color": "rgba(50, 205, 50, 0.8)"},  # Softer green
                        ],
                        "threshold": {
                            "line": {"color": "black", "width": 4},
                            "thickness": 0.75,
                            "value": avg_team_sales_filtered,
                        },
                    },
                ))

            elif len(selected_sales_persons) == 1:
                selected_salesperson = selected_sales_persons[0]
                individual_sales = df_filtered[df_filtered['processed_by'] == selected_salesperson]['purchased_product'].count()

                fig_gauge.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=individual_sales,
                    title={
                        "text": f"Sales for {selected_salesperson}",
                        "font": {"size": 16}
                    },
                    gauge={
                        "axis": {"range": [0, max(max_team_gauge_value, 1)]},
                        "bar": {"color": "royalblue"},
                        "steps": [
                            {"range": [0, avg_team_sales_filtered * 0.8], "color": "rgba(255, 99, 71, 0.8)"},
                            {"range": [avg_team_sales_filtered * 0.8, avg_team_sales_filtered * 1.2], "color": "rgba(255, 165, 0, 0.8)"},
                            {"range": [avg_team_sales_filtered * 1.2, max_team_gauge_value], "color": "rgba(50, 205, 50, 0.8)"},
                        ],
                        "threshold": {
                            "line": {"color": "black", "width": 4},
                            "thickness": 0.75,
                            "value": avg_team_sales_filtered,
                        },
                    },
                ))
              # Add a legend using scatter traces
            # Add a legend for the gauge chart
            fig_gauge.add_trace(go.Scatter(
                x=[None], y=[None], mode='markers',
                marker=dict(size=20, color="rgba(255, 99, 71, 0.8)"),
                name='Bad Performance'
            ))
            fig_gauge.add_trace(go.Scatter(
                x=[None], y=[None], mode='markers',
                marker=dict(size=20, color="rgba(255, 165, 0, 0.8)"),
                name='Average Performance'
            ))
            fig_gauge.add_trace(go.Scatter(
                x=[None], y=[None], mode='markers',
                marker=dict(size=20, color="rgba(50, 205, 50, 0.8)"),
                name='Good Performance'
            ))

            fig_gauge.update_layout(height=300, margin=dict(l=5, r=10, t=70, b=20), xaxis=dict(visible=False),
                yaxis=dict(visible=False))
            st.plotly_chart(fig_gauge, use_container_width=True)

        elif df is not None and 'processed_by' in df.columns and df['processed_by'].nunique() > 0:
            st.warning("Showing overall team average performance. Filter by one Sales Person in the sidebar to see individual performance.")
        else:
            st.info("No sales performance data available or 'processed_by' column not found.")

       



        col_1,col_2 = st.columns(2)
        with col_1:
            # Ensure 'timestamp' column is in datetime format
            if 'timestamp' in df_filtered.columns:
                df_filtered['timestamp'] = pd.to_datetime(df_filtered['timestamp'], errors='coerce')
                df_purchases = df_filtered[df_filtered['purchased_product'] != 'No Purchase'].copy()

                if not df_purchases.empty:
                    # Extract the month from the timestamp
                    df_purchases['month'] = df_purchases['timestamp'].dt.month
                    month_order = list(range(1, 13))  # Ensure months are ordered Jan-Dec

                    # Group by month and count purchases
                    monthly_purchases = df_purchases.groupby('month').size().reindex(month_order, fill_value=0).reset_index(name='Number of Purchases')

                    # Convert month number to month name for better readability
                    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    monthly_purchases['Month Name'] = pd.Categorical(monthly_purchases['month'].map(lambda m: month_names[m - 1]), categories=month_names, ordered=True)

                    # Create the line graph
                    fig_monthly_purchases = px.line(
                        monthly_purchases,
                        x='Month Name',
                        y='Number of Purchases',
                        title='Monthly Purchases',
                        labels={'Month Name': 'Month', 'Number of Purchases': 'Number of Purchases'},
                        markers=True
                    )
                    fig_monthly_purchases.update_layout(height=300, width=300, margin=dict(l=20, r=20, t=50, b=20))
                    fig_monthly_purchases.update_traces(line=dict(width=2), marker=dict(size=5), fill='tozeroy')  # Adjust line and marker size
                    st.plotly_chart(fig_monthly_purchases, use_container_width=True)

                else:
                    st.info("No purchase data available to display the monthly trend.")

            else:
                st.warning("The 'timestamp' column is not available to analyze monthly purchases.")

        with col_2:
            products = df_filtered[df_filtered['purchased_product'] != "No Purchase"]['purchased_product'].value_counts().head(10)
            products_df = products.reset_index()
            products_df.columns = ['Product', 'Purchases']
            fig_products_treemap = px.treemap(
                products_df,
                path=['Product'],
                values='Purchases',
                title="Top & Least Performing Products",
                color='Purchases',
                color_continuous_scale='Viridis'
            )
            fig_products_treemap.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_products_treemap, use_container_width=True)

                  



    with col_sales2:
        side_1, side_2 = st.columns(2)
        with side_1:
            sales_channel = df_filtered[df_filtered['purchased_product'] != "No Purchase"].groupby('referrer')['purchased_product'].count().sort_values(ascending=False).head(10) # Reduced to top 5
            channel_df = sales_channel.reset_index()
            channel_df.columns = ['Channel', 'Purchases']
            fig_channel_donut = px.pie(
                channel_df,
                names='Channel',
                values='Purchases',
                title="Purchases by Channel",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_channel_donut.update_layout(height=300, showlegend=False, margin=dict(l=20, r=20, t=50, b=20))
            fig_channel_donut.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_channel_donut, use_container_width=True)

        with side_2:
            # Filter out rows with no purchase
            purchases_df = df_filtered[df_filtered['purchased_product'] != "No Purchase"].copy()

            if not purchases_df.empty and 'product_category' in purchases_df.columns:
                # Group by product category and count purchases
                purchases_by_category = purchases_df.groupby('product_category')['purchased_product'].count().sort_values(ascending=False).reset_index()
                purchases_by_category.columns = ['Product Category', 'Number of Purchases']

                # Create the bar chart
                fig_purchases_category = px.bar(
                    purchases_by_category,
                    x='Product Category',
                    y='Number of Purchases',
                    title='Purchases by Product Category',
                    labels={'Number of Purchases': 'Number of Purchases', 'Product Category': 'Product Category'},
                )
                fig_purchases_category.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig_purchases_category, use_container_width=True)

            elif not purchases_df.empty and 'product_category' not in purchases_df.columns:
                st.warning("The 'product_category' column was not found in the data. Please ensure this column exists to visualize purchases by product category.")

            else:
                st.info("No purchase data available for the selected date range.")

        
        # Function to clean country names
        def get_official_country_name(country_name):
            try:
                country = pycountry.countries.lookup(country_name)
                return country.name
            except LookupError:
                return country_name

        # Filter purchases
        df_purchases = df_filtered[df_filtered['purchased_product'] != "No Purchase"].copy()

        # Count purchases per country
        sales_country_counts = df_purchases.groupby('country')['purchased_product'].count().sort_values(ascending=False)

        # Convert to DataFrame
        sales_country_df = sales_country_counts.reset_index()
        sales_country_df.columns = ['country', 'purchases']

        # Clean country names
        sales_country_df['country'] = sales_country_df['country'].apply(get_official_country_name)

        # Create map
        fig_country_map = px.choropleth(
            sales_country_df,
            locations='country',
            locationmode='country names',
            color='purchases',
            hover_name='country',
            color_continuous_scale=px.colors.sequential.Plasma,
            labels={'purchases': 'Number of Purchases'},
            title="Purchases by Country"
        )

        fig_country_map.update_geos(
            fitbounds="locations",
            visible=False
        )

        # --- Styling the Map using update_layout ---
        fig_country_map.update_layout(
            geo=dict(
                bgcolor='lightcyan',
                lakecolor='lightblue',
                showocean=True,
                oceancolor='paleturquoise',
                showlakes=True,
                projection_scale=0.7,
                center=dict(lon=0, lat=20),
                lonaxis_range=[-180, 180],
                lataxis_range=[-90, 90],
                showcoastlines=True,
                coastlinecolor="black",
                coastlinewidth=1,
                showcountries=True,
                countrycolor="gray",
                countrywidth=0.5,
                showsubunits=True,
                subunitcolor="darkgray",
                subunitwidth=0.3
            ),
            coloraxis_colorbar=dict(
                title='Purchases',
                orientation='v',
                xanchor="left",
                x=1.02,
                yanchor="middle",
                y=0.5
            ),
            margin=dict(l=20, r=20, t=50, b=20),
            height=300,
        )
        st.plotly_chart(fig_country_map, use_container_width=True)
    





with sales_tab2:
    # st.markdown("<h2 style='font-size:23px;'>Customer Interaction Analysis</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns((2, 1))

    with col1:
        # Chart 4: Monthly Interactions
        monthly = df_filtered['month'].value_counts().sort_index()
        fig_month = px.line(
            x=monthly.index,
            y=monthly.values,
            labels={'x': 'Month', 'y': 'Interactions'},
            title="Monthly Interactions",
            markers=False
        )
        fig_month.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        fig_month.update_traces(line=dict(width=2), marker=dict(size=5), fill='tozeroy')  # Adjust line and marker size
        st.plotly_chart(fig_month, use_container_width=True)

        df_filtered['day_of_week'] = df_filtered['timestamp'].dt.day_name()
        df_filtered['hour'] = df_filtered['timestamp'].dt.hour

        # Create a pivot table: Rows = Days, Columns = Hours, Values = Interaction Counts
        heatmap_data = df_filtered.groupby(['day_of_week', 'hour']).size().unstack().reindex(
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        )

        col_d, col_h = st.columns(2)
        with col_d:
            # Plot as heatmap
            fig_heatmap = px.imshow(
                heatmap_data,
                labels=dict(x="Hour of Day", y="Day of Week", color="Interactions"),
                x=heatmap_data.columns,
                y=heatmap_data.index,
                color_continuous_scale='Viridis',
                aspect="auto",
                title="Traffic Heatmap: Day of Week vs Hour"
            )

            fig_heatmap.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_heatmap, use_container_width=True)

        with col_h:
            # Chart 5: Hourly Interactions
            hourly_counts = df_filtered['hour'].value_counts().sort_index()
            fig_hour = px.bar(
                x=hourly_counts.index,
                y=hourly_counts.values,
                labels={'x': 'Hour', 'y': 'Interactions'},
                title="Traffic by Hour of Day",
                color=hourly_counts.index,
                color_discrete_sequence=px.colors.sequential.Cividis
            )
            fig_hour.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(fig_hour, use_container_width=True)

    with col2:
        interact_category = df_filtered['product_category'].value_counts()
        fig_interact = px.bar(
            x=interact_category.index,
            y=interact_category.values,
            labels={'x': 'Category', 'y': 'Interactions'},
            title="Interaction by Product Category",
            color=interact_category.values,
            color_continuous_scale="Magma"
        )
        fig_interact.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_interact, use_container_width=True)

        # Chart 3: Accessed vs Purchased Products
        product_df = df_filtered[df_filtered['url_category'] == 'products'].copy()
        views = product_df['page_name'].value_counts()
        purchases = product_df[product_df['purchased_product'] != 'No Purchase']['page_name'].value_counts()

        combined = pd.DataFrame({
            'Viewed': views,
            'Purchased': purchases
        }).fillna(0).astype(int)

        fig_accessed_products = go.Figure(data=[
            go.Bar(name='Viewed', x=combined.index, y=combined['Viewed'], marker_color='skyblue'),
            go.Bar(name='Purchased', x=combined.index, y=combined['Purchased'], marker_color='salmon')
        ])
        fig_accessed_products.update_layout(
            barmode='group',
            title="Accessed vs Purchased Products",
            xaxis_title='Product',
            yaxis_title='Count',
            legend_title='Interaction',
            template='plotly_white',
            height=300,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_accessed_products, use_container_width=True)