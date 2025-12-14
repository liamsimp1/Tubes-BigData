def create_streamlit_dashboard():
    """Buat kode untuk dashboard Streamlit yang KONSISTEN dengan notebook"""
    dashboard_code = '''# dashboard_bullying_consistent.py
# Sistem Deteksi Bullying - Dashboard KONSISTEN dengan Notebook
# Universitas Mataram - Teknik Informatika 2025/2026

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import time
import urllib.parse
import warnings
warnings.filterwarnings('ignore')
from plotly.subplots import make_subplots

# ========== KONFIGURASI MONGODB ATLAS ==========
MONGODB_USERNAME = ""
MONGODB_PASSWORD = ""
MONGODB_CLUSTER = ""

# Encode username dan password
encoded_username = urllib.parse.quote_plus(MONGODB_USERNAME)
encoded_password = urllib.parse.quote_plus(MONGODB_PASSWORD)

# Connection string
MONGODB_ATLAS_URI = f"mongodb+srv://{encoded_username}:{encoded_password}@{MONGODB_CLUSTER}.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

DB_NAME = "bullying_detection"
COLLECTION_TWEETS = "tweets"
COLLECTION_CCTV = "cctv_logs"
COLLECTION_ALERTS = "alerts"
COLLECTION_SCHOOLS = "schools"

# ========== SETUP PAGE ==========
st.set_page_config(
    page_title="🚨 Sistem Deteksi Bullying - Konsisten dengan Notebook",
    page_icon="🚨",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        padding: 1rem;
        background: linear-gradient(90deg, #1E3A8A, #3B82F6);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ========== FUNGSI KONEKSI MONGODB ==========
@st.cache_resource
def init_connection():
    """Connect ke MongoDB Atlas"""
    try:
        client = MongoClient(MONGODB_ATLAS_URI, server_api=ServerApi('1'))
        db = client[DB_NAME]
        return db
    except Exception as e:
        st.error(f"❌ Gagal terhubung ke MongoDB: {e}")
        return None

# ========== FUNGSI LOAD DATA ==========
@st.cache_data(ttl=10)
def load_mongodb_data():
    """Load data dari MongoDB - SAMA dengan notebook"""
    try:
        db = init_connection()
        if db is None:
            return None, None, None, None
        
        # AMBIL SEMUA DATA seperti di notebook
        tweets = list(db[COLLECTION_TWEETS].find({"processed": True}))
        cctv = list(db[COLLECTION_CCTV].find())
        alerts = list(db[COLLECTION_ALERTS].find())
        schools = list(db[COLLECTION_SCHOOLS].find())
        
        return tweets, cctv, alerts, schools
    except Exception as e:
        st.error(f"Error: {e}")
        return None, None, None, None

# ========== FUNGSI VISUALISASI YANG SAMA DENGAN NOTEBOOK ==========
def create_matching_sentiment_chart(tweets_df):
    """Buat chart sentimen yang SAMA dengan notebook"""
    if tweets_df.empty or 'sentiment' not in tweets_df.columns:
        return None
    
    # SAMA dengan notebook
    sentiment_counts = tweets_df['sentiment'].value_counts()
    
    fig = px.pie(
        values=sentiment_counts.values,
        names=sentiment_counts.index,
        title='Distribusi Sentimen Tweet (Konsisten dengan Notebook)',
        color=sentiment_counts.index,
        color_discrete_map={'positif': 'green', 'netral': 'blue', 'negatif': 'red'}
    )
    
    fig.update_layout(
        title_x=0.5,
        height=400,
        showlegend=True
    )
    
    return fig

def create_matching_risk_chart(tweets_df):
    """Buat chart risk level yang SAMA dengan notebook"""
    if tweets_df.empty or 'risk_level' not in tweets_df.columns:
        return None
    
    # SAMA dengan notebook
    risk_counts = tweets_df['risk_level'].value_counts()
    
    fig = px.bar(
        x=risk_counts.index,
        y=risk_counts.values,
        title='Distribusi Level Risiko (Konsisten dengan Notebook)',
        labels={'x': 'Level Risiko', 'y': 'Jumlah Tweet'},
        color=risk_counts.index,
        color_discrete_map={'merah': 'red', 'kuning': 'yellow', 'hijau': 'green', 'aman': 'blue'},
        text=risk_counts.values
    )
    
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(
        title_x=0.5,
        height=400,
        showlegend=False
    )
    
    return fig

def create_matching_complete_dashboard(tweets_df, cctv_df, alerts_df):
    """Buat dashboard lengkap yang SAMA dengan notebook"""
    if tweets_df.empty:
        return None
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Distribusi Sentimen', 'Level Risiko per Kota',
                       'Trend Alert 7 Hari Terakhir', 'Anomali CCTV per Lokasi'),
        specs=[[{'type': 'pie'}, {'type': 'bar'}],
               [{'type': 'scatter'}, {'type': 'bar'}]],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # 1. Pie chart sentimen
    if 'sentiment' in tweets_df.columns:
        sentiment_counts = tweets_df['sentiment'].value_counts()
        fig.add_trace(
            go.Pie(labels=sentiment_counts.index, values=sentiment_counts.values,
                   name="Sentimen", marker_colors=['green', 'blue', 'red']),
            row=1, col=1
        )
    
    # 2. Risk level per kota
    if 'city' in tweets_df.columns and 'risk_level' in tweets_df.columns:
        # Top 8 kota seperti di notebook
        top_cities = tweets_df['city'].value_counts().head(8).index
        tweets_top = tweets_df[tweets_df['city'].isin(top_cities)]
        risk_by_city = tweets_top.groupby(['city', 'risk_level']).size().unstack(fill_value=0)
        
        colors = {'merah': 'red', 'kuning': 'yellow', 'hijau': 'green', 'aman': 'blue'}
        
        for risk_level in ['merah', 'kuning', 'hijau', 'aman']:
            if risk_level in risk_by_city.columns:
                fig.add_trace(
                    go.Bar(x=risk_by_city.index, y=risk_by_city[risk_level],
                           name=f'Risiko {risk_level}', marker_color=colors[risk_level]),
                    row=1, col=2
                )
    
    # 3. Trend 7 hari terakhir
    if not alerts_df.empty and 'created_at' in alerts_df.columns:
        alerts_df['created_at'] = pd.to_datetime(alerts_df['created_at'])
        last_7_days = datetime.now() - timedelta(days=7)
        recent_alerts = alerts_df[alerts_df['created_at'] >= last_7_days]
        
        if not recent_alerts.empty:
            recent_alerts['date'] = recent_alerts['created_at'].dt.date
            daily_recent = recent_alerts.groupby('date').size().reset_index(name='alert_count')
            
            fig.add_trace(
                go.Scatter(x=daily_recent['date'], y=daily_recent['alert_count'],
                          mode='lines+markers', name='Alert Harian',
                          line=dict(color='red', width=2)),
                row=2, col=1
            )
    
    # 4. CCTV anomalies by location
    if not cctv_df.empty and 'is_anomaly' in cctv_df.columns:
        anomaly_locations = cctv_df[cctv_df['is_anomaly'] == True]
        
        if not anomaly_locations.empty and 'location' in anomaly_locations.columns:
            location_counts = anomaly_locations['location'].value_counts()
            
            fig.add_trace(
                go.Bar(x=location_counts.index, y=location_counts.values,
                       name='Anomali per Lokasi', marker_color='orange'),
                row=2, col=2
            )
    
    fig.update_layout(
        height=800,
        title_text="Dashboard Monitoring Bullying - KONSISTEN dengan Notebook",
        showlegend=True,
        template='plotly_white'
    )
    
    fig.update_xaxes(title_text="Kota", row=1, col=2)
    fig.update_yaxes(title_text="Jumlah Tweet", row=1, col=2)
    
    fig.update_xaxes(title_text="Tanggal", row=2, col=1)
    fig.update_yaxes(title_text="Jumlah Alert", row=2, col=1)
    
    fig.update_xaxes(title_text="Lokasi", row=2, col=2)
    fig.update_yaxes(title_text="Jumlah Anomali", row=2, col=2)
    
    return fig

# ========== FUNGSI UTAMA DASHBOARD ==========
def main():
    st.markdown('<h1 class="main-header">🚨 Sistem Deteksi Bullying - KONSISTEN dengan Notebook</h1>', unsafe_allow_html=True)
    st.markdown("**Data diambil dari MongoDB yang sama dengan notebook**")
    
    # Load data
    tweets_data, cctv_data, alerts_data, schools_data = load_mongodb_data()
    
    if tweets_data is None:
        st.error("Tidak dapat terhubung ke database. Pastikan pipeline sudah dijalankan.")
        return
    
    # Convert to DataFrame
    tweets_df = pd.DataFrame(tweets_data) if tweets_data else pd.DataFrame()
    cctv_df = pd.DataFrame(cctv_data) if cctv_data else pd.DataFrame()
    alerts_df = pd.DataFrame(alerts_data) if alerts_data else pd.DataFrame()
    
    # Tampilkan statistik
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📝 Total Tweet", len(tweets_df))
    with col2:
        if not tweets_df.empty and 'sentiment' in tweets_df.columns:
            neg_count = len(tweets_df[tweets_df['sentiment'] == 'negatif'])
            st.metric("😔 Sentimen Negatif", neg_count)
    with col3:
        if not tweets_df.empty and 'risk_level' in tweets_df.columns:
            high_risk = len(tweets_df[tweets_df['risk_level'].isin(['merah', 'kuning'])])
            st.metric("🚨 High Risk", high_risk)
    with col4:
        if not cctv_df.empty:
            anomalies = len(cctv_df[cctv_df['is_anomaly'] == True])
            st.metric("📹 Anomali CCTV", anomalies)
    
    # Tab untuk visualisasi
    tab1, tab2, tab3 = st.tabs(["📊 Visualisasi Individual", "📈 Dashboard Lengkap", "📋 Data Detail"])
    
    with tab1:
        st.subheader("Visualisasi Individual")
        
        col1, col2 = st.columns(2)
        with col1:
            fig1 = create_matching_sentiment_chart(tweets_df)
            if fig1:
                st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = create_matching_risk_chart(tweets_df)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        st.subheader("Dashboard Lengkap (Sama dengan Notebook)")
        
        fig3 = create_matching_complete_dashboard(tweets_df, cctv_df, alerts_df)
        if fig3:
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Data tidak cukup untuk membuat dashboard")
    
    with tab3:
        st.subheader("Data Detail dari MongoDB")
        
        if not tweets_df.empty:
            # Tampilkan distribusi yang sama dengan notebook
            st.write("### Distribusi Sentimen (Sama dengan Notebook):")
            if 'sentiment' in tweets_df.columns:
                sentiment_dist = tweets_df['sentiment'].value_counts()
                for sentiment, count in sentiment_dist.items():
                    st.write(f"- {sentiment}: {count}")
            
            st.write("### Distribusi Risk Level (Sama dengan Notebook):")
            if 'risk_level' in tweets_df.columns:
                risk_dist = tweets_df['risk_level'].value_counts()
                for risk, count in risk_dist.items():
                    st.write(f"- {risk}: {count}")
            
            # Tampilkan sample data
            st.write("### Sample Data Tweet:")
            if 'text' in tweets_df.columns and 'sentiment' in tweets_df.columns:
                sample_df = tweets_df[['text', 'sentiment', 'risk_level', 'city']].head(10)
                st.dataframe(sample_df)
    
    # Info tentang data
    st.sidebar.title("ℹ️ Info Data")
    st.sidebar.write(f"Total Tweet: {len(tweets_df)}")
    st.sidebar.write(f"Data diambil: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not tweets_df.empty and 'created_at' in tweets_df.columns:
        latest_date = pd.to_datetime(tweets_df['created_at']).max()
        st.sidebar.write(f"Data terbaru: {latest_date.strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    main()'''
    
    # Simpan kode dashboard
    with open('dashboard_consistent.py', 'w', encoding='utf-8') as f:
        f.write(dashboard_code)
    
    print("✅ Dashboard KONSISTEN berhasil dibuat: dashboard_consistent.py")
    print("🎯 Jalankan dengan: streamlit run dashboard_consistent.py")
    
    return dashboard_code