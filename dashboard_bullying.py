# dashboard_final_with_map.py
# Sistem Deteksi Bullying - Dashboard Final dengan Peta
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
import random

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

# Koordinat kota di Indonesia
CITY_COORDINATES = {
    "Jakarta": {"lat": -6.2088, "lon": 106.8456},
    "Surabaya": {"lat": -7.2575, "lon": 112.7521},
    "Bandung": {"lat": -6.9175, "lon": 107.6191},
    "Medan": {"lat": 3.5952, "lon": 98.6722},
    "Semarang": {"lat": -6.9667, "lon": 110.4167},
    "Makassar": {"lat": -5.1477, "lon": 119.4327},
    "Palembang": {"lat": -2.9911, "lon": 104.7567},
    "Depok": {"lat": -6.4025, "lon": 106.7942},
    "Tangerang": {"lat": -6.1781, "lon": 106.6300},
    "Bekasi": {"lat": -6.2349, "lon": 106.9920},
    "Mataram": {"lat": -8.5833, "lon": 116.1167},
    "Denpasar": {"lat": -8.6500, "lon": 115.2167},
    "Yogyakarta": {"lat": -7.8014, "lon": 110.3644},
    "Malang": {"lat": -7.9833, "lon": 112.6333},
    "Surakarta": {"lat": -7.5667, "lon": 110.8167}
}

# ========== SETUP PAGE ==========
st.set_page_config(
    page_title="🚨 Sistem Deteksi Bullying - Dashboard Final",
    page_icon="🚨",
    layout="wide"
)

# ========== CSS CUSTOM ==========
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
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        margin-bottom: 1rem;
        transition: transform 0.3s;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2D3748;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #4F46E5;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        font-weight: 600;
        border-radius: 10px 10px 0 0;
    }
</style>
""", unsafe_allow_html=True)

# ========== FUNGSI KONEKSI MONGODB ==========
@st.cache_resource
def init_connection():
    """Connect ke MongoDB Atlas - FIX error"""
    try:
        client = MongoClient(MONGODB_ATLAS_URI, server_api=ServerApi('1'))
        db = client[DB_NAME]
        # Test koneksi
        client.admin.command('ping')
        return db
    except Exception as e:
        st.sidebar.error(f"❌ MongoDB Error: {str(e)[:100]}")
        return None

# ========== FUNGSI LOAD DATA ==========
@st.cache_data(ttl=30)
def load_mongodb_data():
    """Load data dari MongoDB - FIX error"""
    db = init_connection()
    
    # FIX: Pakai 'is None' bukan 'if not db'
    if db is None:
        st.warning("⚠️ Menggunakan data dummy karena tidak bisa konek ke MongoDB")
        return create_dummy_data(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        # AMBIL DATA seperti di notebook
        tweets = list(db[COLLECTION_TWEETS].find({"processed": True}).limit(2000))
        cctv = list(db[COLLECTION_CCTV].find().limit(1000))
        alerts = list(db[COLLECTION_ALERTS].find().limit(500))
        schools = list(db[COLLECTION_SCHOOLS].find().limit(100))
        
        return tweets, cctv, alerts, schools
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return create_dummy_data(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def create_dummy_data():
    """Buat data dummy jika MongoDB error"""
    print("⚠️ Membuat data dummy...")
    
    cities = list(CITY_COORDINATES.keys())[:10]  # Ambil 10 kota pertama
    sentiments = ['positif', 'netral', 'negatif']
    risk_levels = ['merah', 'kuning', 'hijau', 'aman']
    
    data = []
    for i in range(1000):
        city = random.choice(cities)
        sentiment = random.choices(sentiments, weights=[0.2, 0.3, 0.5])[0]
        risk_level = random.choices(risk_levels, weights=[0.3, 0.4, 0.2, 0.1])[0]
        
        data.append({
            'tweet_id': f'dummy_{i}',
            'text': f'Sample tweet tentang bullying di sekolah {i}',
            'city': city,
            'sentiment': sentiment,
            'risk_level': risk_level,
            'risk_score': random.randint(1, 20),
            'bullying_detected': risk_level in ['merah', 'kuning'],
            'created_at': datetime.now() - timedelta(days=random.randint(0, 30)),
            'school': f'SMP Negeri {random.randint(1, 5)} {city}',
            'category': random.choice(['korban', 'pelaku', 'saksi', 'unknown']),
            'processed': True
        })
    
    return data

# ========== FUNGSI UNTUK PETA ==========
def create_indonesia_heatmap(tweets_df, cctv_df):
    """Buat heatmap peta Indonesia seperti di notebook"""
    if tweets_df.empty and cctv_df.empty:
        return None
    
    heat_data = []
    
    # 1. Hitung tweet risiko tinggi per kota
    if not tweets_df.empty and 'city' in tweets_df.columns and 'risk_level' in tweets_df.columns:
        high_risk_tweets = tweets_df[tweets_df['risk_level'].isin(['merah', 'kuning'])]
        if not high_risk_tweets.empty:
            tweet_counts = high_risk_tweets['city'].value_counts()
            for city, count in tweet_counts.items():
                if city in CITY_COORDINATES:
                    heat_data.append({
                        'city': city,
                        'lat': CITY_COORDINATES[city]['lat'],
                        'lon': CITY_COORDINATES[city]['lon'],
                        'count': count,
                        'type': 'tweet',
                        'label': f'Tweet: {count} risiko tinggi'
                    })
    
    # 2. Hitung anomali CCTV per kota
    if not cctv_df.empty and 'city' in cctv_df.columns and 'is_anomaly' in cctv_df.columns:
        anomaly_df = cctv_df[cctv_df['is_anomaly'] == True]
        if not anomaly_df.empty:
            cctv_counts = anomaly_df['city'].value_counts()
            for city, count in cctv_counts.items():
                if city in CITY_COORDINATES:
                    # Cek apakah kota sudah ada di data
                    found = False
                    for item in heat_data:
                        if item['city'] == city:
                            item['count'] += count * 2  # CCTV lebih berat
                            item['label'] = f"{item['label']} + CCTV: {count}"
                            found = True
                            break
                    if not found:
                        heat_data.append({
                            'city': city,
                            'lat': CITY_COORDINATES[city]['lat'],
                            'lon': CITY_COORDINATES[city]['lon'],
                            'count': count * 2,
                            'type': 'cctv',
                            'label': f'CCTV: {count} anomali'
                        })
    
    if not heat_data:
        return None
    
    heat_df = pd.DataFrame(heat_data)
    
    # Buat scatter map
    fig = px.scatter_geo(
        heat_df,
        lat='lat',
        lon='lon',
        size='count',
        color='count',
        hover_name='city',
        hover_data={'count': True, 'label': True, 'lat': False, 'lon': False},
        size_max=40,
        projection='natural earth',
        title='🗺️ Heatmap Risiko Bullying & Anomali CCTV di Indonesia',
        color_continuous_scale='RdYlGn_r',
        color_continuous_midpoint=heat_df['count'].median(),
        scope='asia',
        center={'lat': -2.5, 'lon': 118},
        template='plotly_white'
    )
    
    # Update geos settings
    fig.update_geos(
        resolution=50,
        showcoastlines=True,
        coastlinecolor="Black",
        showland=True,
        landcolor="lightgray",
        showocean=True,
        oceancolor="lightblue",
        showcountries=True,
        countrycolor="black",
        showlakes=True,
        lakecolor="lightblue"
    )
    
    # Update layout
    fig.update_layout(
        height=550,
        margin={"r": 0, "t": 60, "l": 0, "b": 0},
        title_x=0.5,
        title_font_size=18,
        geo=dict(
            projection_scale=5,
            center=dict(lat=-2.5, lon=118)
        )
    )
    
    return fig

# ========== FUNGSI VISUALISASI ==========
def create_matching_sentiment_chart(tweets_df):
    """Buat chart sentimen SAMA dengan notebook"""
    if tweets_df.empty or 'sentiment' not in tweets_df.columns:
        return None
    
    sentiment_counts = tweets_df['sentiment'].value_counts()
    
    fig = px.pie(
        values=sentiment_counts.values,
        names=sentiment_counts.index,
        title='Distribusi Sentimen Tweet',
        color=sentiment_counts.index,
        color_discrete_map={'positif': 'green', 'netral': 'blue', 'negatif': 'red'},
        hole=0.3
    )
    
    fig.update_layout(
        title_x=0.5,
        height=400,
        showlegend=True
    )
    
    return fig

def create_matching_risk_chart(tweets_df):
    """Buat chart risk level SAMA dengan notebook"""
    if tweets_df.empty or 'risk_level' not in tweets_df.columns:
        return None
    
    risk_counts = tweets_df['risk_level'].value_counts()
    
    fig = px.bar(
        x=risk_counts.index,
        y=risk_counts.values,
        title='Distribusi Level Risiko',
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
    """Buat dashboard lengkap SAMA dengan notebook"""
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
        # Ambil top 8 kota
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
        title_text="Dashboard Monitoring Bullying - Konsisten dengan Notebook",
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
    # Header
    st.markdown('<h1 class="main-header">🚨 Sistem Deteksi Bullying - Dashboard Final</h1>', unsafe_allow_html=True)
    st.markdown("**Dashboard dengan Peta Heatmap Indonesia**")
    
    # Load data
    tweets_data, cctv_data, alerts_data, schools_data = load_mongodb_data()
    
    # Convert to DataFrame
    tweets_df = pd.DataFrame(tweets_data) if tweets_data else pd.DataFrame()
    cctv_df = pd.DataFrame(cctv_data) if cctv_data else pd.DataFrame()
    alerts_df = pd.DataFrame(alerts_data) if alerts_data else pd.DataFrame()
    
    # ========== SIDEBAR ==========
    st.sidebar.title("⚙️ Kontrol Dashboard")
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.title("📊 Statistik Data")
    
    st.sidebar.write(f"**Total Tweet:** {len(tweets_df)}")
    
    if not tweets_df.empty:
        if 'sentiment' in tweets_df.columns:
            neg_count = len(tweets_df[tweets_df['sentiment'] == 'negatif'])
            st.sidebar.write(f"**Sentimen Negatif:** {neg_count}")
        
        if 'risk_level' in tweets_df.columns:
            high_risk = len(tweets_df[tweets_df['risk_level'].isin(['merah', 'kuning'])])
            st.sidebar.write(f"**High Risk:** {high_risk}")
    
    if not cctv_df.empty:
        anomalies = len(cctv_df[cctv_df['is_anomaly'] == True])
        st.sidebar.write(f"**Anomali CCTV:** {anomalies}")
    
    st.sidebar.markdown("---")
    st.sidebar.caption(f"🕒 Terakhir update: {datetime.now().strftime('%H:%M:%S')}")
    
    # ========== METRICS ==========
    st.markdown('<div class="sub-header">📊 Metrics Real-time</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("📝 Total Tweet", len(tweets_df))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if not tweets_df.empty and 'sentiment' in tweets_df.columns:
            neg_count = len(tweets_df[tweets_df['sentiment'] == 'negatif'])
            st.metric("😔 Sentimen Negatif", neg_count)
        else:
            st.metric("😔 Sentimen Negatif", 0)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if not tweets_df.empty and 'risk_level' in tweets_df.columns:
            high_risk = len(tweets_df[tweets_df['risk_level'].isin(['merah', 'kuning'])])
            st.metric("🚨 High Risk", high_risk)
        else:
            st.metric("🚨 High Risk", 0)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if not cctv_df.empty:
            anomalies = len(cctv_df[cctv_df['is_anomaly'] == True])
            st.metric("📹 Anomali CCTV", anomalies)
        else:
            st.metric("📹 Anomali CCTV", 0)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== TABS ==========
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Peta Heatmap", 
        "📊 Visualisasi", 
        "📈 Dashboard Lengkap",
        "📋 Data Detail"
    ])
    
    with tab1:
        st.markdown('<div class="sub-header">🗺️ Peta Heatmap Indonesia</div>', unsafe_allow_html=True)
        
        # Buat peta heatmap
        heatmap_fig = create_indonesia_heatmap(tweets_df, cctv_df)
        
        if heatmap_fig:
            st.plotly_chart(heatmap_fig, use_container_width=True)
            
            # Stats di bawah peta
            col1, col2, col3 = st.columns(3)
            with col1:
                if not tweets_df.empty and 'risk_level' in tweets_df.columns:
                    red_tweets = len(tweets_df[tweets_df['risk_level'] == 'merah'])
                    st.metric("🔴 Tweet Merah", red_tweets)
            
            with col2:
                if not tweets_df.empty and 'risk_level' in tweets_df.columns:
                    yellow_tweets = len(tweets_df[tweets_df['risk_level'] == 'kuning'])
                    st.metric("🟡 Tweet Kuning", yellow_tweets)
            
            with col3:
                if not cctv_df.empty:
                    total_anomalies = len(cctv_df[cctv_df['is_anomaly'] == True])
                    st.metric("📹 Total Anomali", total_anomalies)
        else:
            st.info("Data tidak cukup untuk membuat peta heatmap")
            
            # Fallback: bar chart per kota
            if not tweets_df.empty and 'city' in tweets_df.columns:
                st.subheader("Distribusi per Kota")
                city_counts = tweets_df['city'].value_counts().head(10).reset_index()
                city_counts.columns = ['city', 'count']
                
                fig_bar = px.bar(
                    city_counts,
                    x='city',
                    y='count',
                    title='Jumlah Tweet per Kota',
                    color='count',
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig_bar, use_container_width=True)
    
    with tab2:
        st.markdown('<div class="sub-header">📈 Diagram Individual</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = create_matching_sentiment_chart(tweets_df)
            if fig1:
                st.plotly_chart(fig1, use_container_width=True)
                st.caption("**Distribusi Sentimen Tweet**")
            else:
                st.info("Data sentimen tidak tersedia")
        
        with col2:
            fig2 = create_matching_risk_chart(tweets_df)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)
                st.caption("**Distribusi Level Risiko**")
            else:
                st.info("Data risk level tidak tersedia")
        
        # Tambahan: Trend waktu
        if not tweets_df.empty and 'created_at' in tweets_df.columns:
            st.subheader("📅 Trend Harian")
            
            try:
                tweets_df['date'] = pd.to_datetime(tweets_df['created_at']).dt.date
                daily_counts = tweets_df.groupby('date').size().reset_index(name='count')
                
                fig_trend = px.line(
                    daily_counts,
                    x='date',
                    y='count',
                    title='Jumlah Tweet per Hari',
                    markers=True
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            except:
                pass
    
    with tab3:
        st.markdown('<div class="sub-header">📊 Dashboard Lengkap (2x2 Subplots)</div>', unsafe_allow_html=True)
        
        fig3 = create_matching_complete_dashboard(tweets_df, cctv_df, alerts_df)
        if fig3:
            st.plotly_chart(fig3, use_container_width=True)
            st.caption("**Dashboard lengkap dengan 4 visualisasi**")
        else:
            st.info("Data tidak cukup untuk membuat dashboard lengkap")
            
            # Fallback: simple dashboard
            if not tweets_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    fig_fallback1 = create_matching_sentiment_chart(tweets_df)
                    if fig_fallback1:
                        st.plotly_chart(fig_fallback1, use_container_width=True)
                
                with col2:
                    fig_fallback2 = create_matching_risk_chart(tweets_df)
                    if fig_fallback2:
                        st.plotly_chart(fig_fallback2, use_container_width=True)
    
    with tab4:
        st.markdown('<div class="sub-header">📋 Data Detail dari MongoDB</div>', unsafe_allow_html=True)
        
        if not tweets_df.empty:
            # Tampilkan distribusi
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**📊 Distribusi Sentimen:**")
                if 'sentiment' in tweets_df.columns:
                    for sent, count in tweets_df['sentiment'].value_counts().items():
                        st.write(f"- {sent}: {count}")
                else:
                    st.write("Tidak ada data")
            
            with col2:
                st.write("**⚠️ Distribusi Risk Level:**")
                if 'risk_level' in tweets_df.columns:
                    for risk, count in tweets_df['risk_level'].value_counts().items():
                        st.write(f"- {risk}: {count}")
                else:
                    st.write("Tidak ada data")
            
            with col3:
                st.write("**📍 Top 5 Kota:**")
                if 'city' in tweets_df.columns:
                    for city, count in tweets_df['city'].value_counts().head(5).items():
                        st.write(f"- {city}: {count}")
                else:
                    st.write("Tidak ada data")
            
            # Tampilkan sample data
            st.subheader("Sample Data Tweet (10 terbaru)")
            
            # Sort by date jika ada
            if 'created_at' in tweets_df.columns:
                tweets_df_sorted = tweets_df.sort_values('created_at', ascending=False)
            else:
                tweets_df_sorted = tweets_df
            
            # Pilih kolom untuk ditampilkan
            show_cols = ['city', 'sentiment', 'risk_level', 'risk_score', 'bullying_detected', 'created_at']
            available_cols = [col for col in show_cols if col in tweets_df_sorted.columns]
            
            if available_cols:
                sample_df = tweets_df_sorted[available_cols].head(10).copy()
                
                # Format tanggal
                if 'created_at' in sample_df.columns:
                    sample_df['created_at'] = pd.to_datetime(sample_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                
                # Format risk score
                if 'risk_score' in sample_df.columns:
                    sample_df['risk_score'] = sample_df['risk_score'].apply(lambda x: f"{x}/20")
                
                st.dataframe(sample_df, use_container_width=True)
                
                # Download button
                csv = sample_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Sample Data (CSV)",
                    data=csv,
                    file_name=f"sample_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Kolom data tidak tersedia")
        else:
            st.info("Tidak ada data tweet")
    
    # ========== FOOTER ==========
    st.markdown("---")
    st.markdown("**Sistem Deteksi Bullying** • Teknik Informatika UNRAM • © 2025")
    st.caption(f"Dashboard terakhir di-load: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()