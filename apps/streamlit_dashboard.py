import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logging
from typing import List, Dict
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
import streamlit as st
from src.db import engine
from src.config import DATABASE_URL

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def app():
    # Page configuration
    st.set_page_config(
        page_title="Ticket Analytics Dashboard", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for professional styling
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
        }
        
        .kpi-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .kpi-value {
            font-size: 2rem;
            font-weight: bold;
            margin: 0;
        }
        
        .kpi-label {
            font-size: 0.9rem;
            opacity: 0.9;
            margin: 0.25rem 0 0 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .ticket-card {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: box-shadow 0.2s ease;
        }
        
        .ticket-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .badge {
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            display: inline-block;
            margin: 0.125rem;
        }
        
        .badge-high, .badge-p1 { background-color: #fef2f2; color: #dc2626; }
        .badge-medium, .badge-p2 { background-color: #fffbeb; color: #d97706; }
        .badge-low, .badge-p3 { background-color: #f0fdf4; color: #16a34a; }
        
        .badge-positive { background-color: #f0fdf4; color: #16a34a; }
        .badge-negative { background-color: #fef2f2; color: #dc2626; }
        .badge-neutral { background-color: #f1f5f9; color: #475569; }
        
        .section-header {
            font-size: 1.75rem;
            font-weight: 600;
            color: #374151;
            margin: 2rem 0 1.5rem 0;
            padding-bottom: 0.75rem;
        }
        
        .analytics-grid {
            margin-top: 1rem;
        }
        
        .chart-container {
            background-color: white;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 1rem;
        }
        
        .download-section {
            background-color: #f8fafc;
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
            text-align: center;
            border: 1px solid #e2e8f0;
        }
        
        .stTabs > div > div > div > div {
            padding-top: 1rem;
        }
        
        /* Fix tab indicator thickness */
        .stTabs [data-baseweb="tab-highlight"] {
            height: 2px !important;
        }
        
        /* Better tab styling */
        .stTabs [data-baseweb="tab"] {
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .metric-row {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

    @st.cache_data(ttl=300)
    def load_tickets():
        """Load tickets with caching for performance"""
        try:
            query = "SELECT * FROM tickets ORDER BY created_at DESC"
            return pd.read_sql(query, engine)
        except Exception as e:
            st.error(f"Error loading tickets: {str(e)}")
            return pd.DataFrame()

    def filter_tickets(df, topic, sentiment, priority, search_text):
        """Apply filters to ticket dataframe"""
        if df.empty:
            return df
            
        filtered = df.copy()
        if topic:
            filtered = filtered[filtered['topic'].isin(topic)]
        if sentiment:
            filtered = filtered[filtered['sentiment'].isin(sentiment)]
        if priority:
            filtered = filtered[filtered['priority'].isin(priority)]
        if search_text:
            filtered = filtered[
                filtered['subject'].str.contains(search_text, case=False, na=False) |
                filtered['user_query'].str.contains(search_text, case=False, na=False)
            ]
        return filtered

    # Header
    st.markdown('<h1 class="main-header">Ticket Analytics Dashboard</h1>', unsafe_allow_html=True)

    # Load data
    tickets_df = load_tickets()

    if tickets_df.empty:
        st.error("No tickets data available. Please check your database connection.")
        st.stop()

    # Sidebar filters
    with st.sidebar:
        st.markdown("### Filters & Search")
        
        topic_filter = st.multiselect(
            "Filter by Topic", 
            options=sorted(tickets_df['topic'].unique()) if not tickets_df.empty else [],
            help="Select topics to filter tickets"
        )
        
        sentiment_filter = st.multiselect(
            "Filter by Sentiment", 
            options=sorted(tickets_df['sentiment'].unique()) if not tickets_df.empty else [],
            help="Select sentiment categories"
        )
        
        priority_filter = st.multiselect(
            "Filter by Priority", 
            options=sorted(tickets_df['priority'].unique()) if not tickets_df.empty else [],
            help="Select priority levels"
        )
        
        search_text = st.text_input(
            "Search Tickets", 
            placeholder="Search subject or query...",
            help="Search through ticket content"
        )
        
        # Filter summary
        if any([topic_filter, sentiment_filter, priority_filter, search_text]):
            st.info(f"Active filters: {len([f for f in [topic_filter, sentiment_filter, priority_filter, search_text] if f])}")
        
        if st.button("Clear All Filters", use_container_width=True):
            st.experimental_rerun()

    # Apply filters
    filtered_df = filter_tickets(tickets_df, topic_filter, sentiment_filter, priority_filter, search_text)

    # Main tabs
    tab1, tab2 = st.tabs(["All Tickets", "Analytics Dashboard"])

    # --- Tab 1: All Tickets ---
    with tab1:
        st.markdown('<div class="section-header">Ticket Management</div>', unsafe_allow_html=True)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="kpi-container">
                <p class="kpi-value">{len(filtered_df)}</p>
                <p class="kpi-label">Total Tickets</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            high_priority_count = len(filtered_df[filtered_df['priority'].isin(['High', 'P1'])]) if not filtered_df.empty else 0
            st.markdown(f"""
            <div class="kpi-container">
                <p class="kpi-value">{high_priority_count}</p>
                <p class="kpi-label">High Priority</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            negative_sentiment_count = len(filtered_df[filtered_df['sentiment'] == 'Frustrated']) if not filtered_df.empty else 0
            st.markdown(f"""
            <div class="kpi-container">
                <p class="kpi-value">{negative_sentiment_count}</p>
                <p class="kpi-label">Frustrated Sentiment</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            unique_topics = filtered_df['topic'].nunique() if not filtered_df.empty else 0
            st.markdown(f"""
            <div class="kpi-container">
                <p class="kpi-value">{unique_topics}</p>
                <p class="kpi-label">Unique Topics</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Tickets display
        if not filtered_df.empty:
            st.markdown("### Ticket Details")
            
            # Display tickets
            for _, row in filtered_df.iterrows():
                # Create badges for priority and sentiment
                priority_class = f"badge-{str(row['priority']).lower()}"
                sentiment_class = f"badge-{str(row['sentiment']).lower()}"
                
                with st.expander(f"#{row['display_id']} - {row['subject']}", expanded=False):
                    col_left, col_right = st.columns([3, 1])
                    
                    with col_left:
                        st.markdown(f"**Query:** {row['user_query']}")
                        st.markdown(f"**Created:** {pd.to_datetime(row['created_at']).strftime('%Y-%m-%d %H:%M')}")
                    
                    with col_right:
                        st.markdown(f"""
                        <div style="text-align: right;">
                            <span class="badge {priority_class}">Priority: {row['priority']}</span><br>
                            <span class="badge {sentiment_class}">Sentiment: {row['sentiment']}</span><br>
                            <span class="badge" style="background-color: #eff6ff; color: #2563eb;">Topic: {row['topic']}</span>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Download section
            st.markdown('<div class="download-section">', unsafe_allow_html=True)
            st.markdown("### Export Data")
            col_download = st.columns([1, 2, 1])[1]
            with col_download:
                st.download_button(
                    "Download Filtered Tickets as CSV",
                    filtered_df.to_csv(index=False),
                    "filtered_tickets.csv",
                    "text/csv",
                    use_container_width=True
                )
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No tickets match the current filters. Try adjusting your search criteria.")

    # --- Tab 2: Analytics ---
    with tab2:
        st.markdown('<div class="section-header">Analytics Dashboard</div>', unsafe_allow_html=True)
        
        if not filtered_df.empty:
            # KPI Cards
            total_tickets = len(filtered_df)
            top_topic = filtered_df['topic'].value_counts().idxmax() if not filtered_df.empty else "N/A"
            top_priority = filtered_df['priority'].value_counts().idxmax() if not filtered_df.empty else "N/A"
            avg_sentiment_score = filtered_df['sentiment'].value_counts()
            
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            
            with kpi1:
                st.markdown(f"""
                <div class="kpi-container">
                    <p class="kpi-value">{total_tickets}</p>
                    <p class="kpi-label">Total Tickets</p>
                </div>
                """, unsafe_allow_html=True)
            
            with kpi2:
                st.markdown(f"""
                <div class="kpi-container">
                    <p class="kpi-value">{top_topic}</p>
                    <p class="kpi-label">Top Topic</p>
                </div>
                """, unsafe_allow_html=True)
            
            with kpi3:
                st.markdown(f"""
                <div class="kpi-container">
                    <p class="kpi-value">{top_priority}</p>
                    <p class="kpi-label">Top Priority</p>
                </div>
                """, unsafe_allow_html=True)
            
            with kpi4:
                resolution_rate = round((len(filtered_df) / len(tickets_df)) * 100, 1) if len(tickets_df) > 0 else 0
                st.markdown(f"""
                <div class="kpi-container">
                    <p class="kpi-value">{resolution_rate}%</p>
                    <p class="kpi-label">Filter Coverage</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Analytics Grid
            st.markdown("### Distribution Analysis")
            col1, col2, col3 = st.columns(3)
            
            # Priority Distribution
            with col1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                fig_priority = px.pie(
                    filtered_df, 
                    names='priority', 
                    title="Priority Distribution",
                    color_discrete_map={
                        'P1': '#dc2626', 'High': '#dc2626',
                        'P2': '#d97706', 'Medium': '#d97706', 
                        'P3': '#16a34a', 'Low': '#16a34a'
                    },
                    template="plotly_white"
                )
                fig_priority.update_layout(
                    font=dict(size=11),
                    title_font_size=14,
                    margin=dict(t=40, b=20, l=20, r=20),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2)
                )
                st.plotly_chart(fig_priority, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Sentiment Distribution
            with col2:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                fig_sentiment = px.pie(
                    filtered_df, 
                    names='sentiment', 
                    title="Sentiment Analysis",
                    template="plotly_white",
                    color_discrete_map={
                        'Positive': '#16a34a',
                        'Negative': '#dc2626',
                        'Neutral': '#64748b'
                    }
                )
                fig_sentiment.update_layout(
                    font=dict(size=11),
                    title_font_size=14,
                    margin=dict(t=40, b=20, l=20, r=20),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2)
                )
                st.plotly_chart(fig_sentiment, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Topic Distribution - FIXED VERSION
            with col3:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                fig_topic = px.pie(
                    filtered_df, 
                    names='topic', 
                    title="Topic Breakdown",
                    template="plotly_white",
                    color_discrete_sequence=['#FFB6C1', '#87CEEB', '#DDA0DD', '#F0E68C', '#98FB98', '#F4A460', '#DEB887', '#E6E6FA', '#FFDAB9', '#B0E0E6']
                )
                fig_topic.update_layout(
                    font=dict(size=11),
                    title_font_size=14,
                    margin=dict(t=40, b=20, l=20, r=20),
                    showlegend=True,
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", 
                        y=-0.3,
                        xanchor="center",
                        x=0.5
                    ),
                    height=500
                )
                fig_topic.update_traces(
                    textposition='inside', 
                    textinfo='percent',
                    textfont_size=10
                )
                st.plotly_chart(fig_topic, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Advanced Analytics
            st.markdown("### Advanced Analytics")
            
            col_heat, col_bar = st.columns(2)
            
            # Heatmap: Topic vs Sentiment
            with col_heat:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                heatmap_data = filtered_df.groupby(['topic', 'sentiment']).size().reset_index(name='count')
                if not heatmap_data.empty:
                    heatmap_pivot = heatmap_data.pivot(index='topic', columns='sentiment', values='count').fillna(0)
                    fig_heatmap = go.Figure(data=go.Heatmap(
                        z=heatmap_pivot.values,
                        x=heatmap_pivot.columns,
                        y=heatmap_pivot.index,
                        colorscale='Viridis',
                        hoverongaps=False
                    ))
                    fig_heatmap.update_layout(
                        title="Topic vs Sentiment Correlation",
                        template="plotly_white",
                        xaxis_title="Sentiment",
                        yaxis_title="Topic",
                        font=dict(size=11),
                        title_font_size=14,
                        margin=dict(t=40, b=40, l=60, r=20)
                    )
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                else:
                    st.info("Insufficient data for heatmap visualization")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Bar Chart: Topics by Priority
            with col_bar:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                bar_data = filtered_df.groupby(['topic', 'priority']).size().reset_index(name='count')
                if not bar_data.empty:
                    fig_bar = px.bar(
                        bar_data, 
                        x='topic', 
                        y='count', 
                        color='priority', 
                        barmode='stack',
                        title="Topics by Priority Level", 
                        template="plotly_white",
                        color_discrete_map={
                            'P1': '#dc2626', 'High': '#dc2626',
                            'P2': '#d97706', 'Medium': '#d97706',
                            'P3': '#16a34a', 'Low': '#16a34a'
                        }
                    )
                    fig_bar.update_layout(
                        font=dict(size=11),
                        title_font_size=14,
                        margin=dict(t=40, b=60, l=40, r=20),
                        xaxis_title="Topic",
                        yaxis_title="Ticket Count",
                        legend_title="Priority"
                    )
                    fig_bar.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("Insufficient data for bar chart visualization")
                st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            st.info("No data available for analytics. Please adjust your filters to view charts and insights.")