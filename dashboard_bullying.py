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
    .data-container {
        max-height: 600px;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin-top: 10px;
        background-color: #f9f9f9;
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
    """Load data dari MongoDB - FIX error dengan debug info"""
    db = init_connection()
    
    if db is None:
        st.warning("⚠️ Menggunakan data dummy karena tidak bisa konek ke MongoDB")
        return create_dummy_data(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        # AMBIL DATA dengan debug print
        print("🔍 Loading data from MongoDB...")
        
        # Tweets
        tweets = list(db[COLLECTION_TWEETS].find({"processed": True}))
        print(f"   • Tweets loaded: {len(tweets)}")
        if tweets:
            print(f"   • Tweet fields: {list(tweets[0].keys())[:10]}...")
        
        # CCTV - ambil semua, tidak ada filter
        cctv = list(db[COLLECTION_CCTV].find())
        print(f"   • CCTV logs loaded: {len(cctv)}")
        if cctv:
            print(f"   • CCTV fields: {list(cctv[0].keys())}")
        
        # Alerts
        alerts = list(db[COLLECTION_ALERTS].find())
        print(f"   • Alerts loaded: {len(alerts)}")
        
        # Schools
        schools = list(db[COLLECTION_SCHOOLS].find())
        print(f"   • Schools loaded: {len(schools)}")
        
        return tweets, cctv, alerts, schools
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        import traceback
        traceback.print_exc()
        return create_dummy_data(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def create_dummy_data():
    """Buat data dummy jika MongoDB error"""
    print("⚠️ Membuat data dummy...")
    
    cities = list(CITY_COORDINATES.keys())[:10]
    sentiments = ['positif', 'netral', 'negatif']
    risk_levels = ['merah', 'kuning', 'hijau', 'aman']
    categories = ['korban_direct', 'pelaku', 'saksi', 'support', 'report', 'positif_umum']
    locations = ['gerbang', 'lorong', 'kantin', 'lapangan', 'parkir', 'toilet', 'kelas']
    
    # Buat dummy tweets
    tweets_data = []
    for i in range(500):
        city = random.choice(cities)
        sentiment = random.choices(sentiments, weights=[0.2, 0.3, 0.5])[0]
        risk_level = random.choices(risk_levels, weights=[0.3, 0.4, 0.2, 0.1])[0]
        category = random.choice(categories)
        
        tweets_data.append({
            'tweet_id': f'dummy_tweet_{i}',
            'text': f'Contoh tweet tentang bullying di sekolah {i} di kota {city}',
            'city': city,
            'sentiment': sentiment,
            'risk_level': risk_level,
            'risk_score': random.randint(1, 20),
            'bullying_detected': risk_level in ['merah', 'kuning'],
            'created_at': datetime.now() - timedelta(days=random.randint(0, 30)),
            'school': f'SMP Negeri {random.randint(1, 5)} {city}',
            'category': category,
            'processed': True
        })
    
    # Buat dummy CCTV logs
    cctv_data = []
    for i in range(100):
        city = random.choice(cities)
        location = random.choice(locations)
        
        cctv_data.append({
            'log_id': f'cctv_log_{i}',
            'cctv_id': f'cctv_{random.randint(1, 20)}',
            'school': f'SMP Negeri {random.randint(1, 5)} {city}',
            'city': city,
            'location': location,
            'timestamp': datetime.now() - timedelta(hours=random.randint(0, 72)),
            'crowd_level': random.randint(1, 100),
            'noise_level': random.randint(30, 90),
            'is_anomaly': random.choice([True, False, False, False]),  # 25% anomaly
            'warning_level': random.choice(['merah', 'kuning', 'hijau']),
            'processed': False
        })
    
    return tweets_data, cctv_data, [], []

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
    schools_df = pd.DataFrame(schools_data) if schools_data else pd.DataFrame()
    
    # Debug info di sidebar
    with st.sidebar.expander("🔍 Debug Info", expanded=False):
        st.write(f"**Data Loaded:**")
        st.write(f"• Tweets: {len(tweets_df)} rows")
        st.write(f"• CCTV Logs: {len(cctv_df)} rows")
        st.write(f"• Alerts: {len(alerts_df)} rows")
        
        if not tweets_df.empty:
            st.write(f"**Tweet Columns:** {list(tweets_df.columns)[:10]}")
        
        if not cctv_df.empty:
            st.write(f"**CCTV Columns:** {list(cctv_df.columns)}")
    
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️ Peta Heatmap", 
        "📊 Visualisasi", 
        "📈 Dashboard Lengkap",
        "📝 Tweet & CCTV Log",
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
    
    # Tab 4: Tweet & CCTV Log - FIXED VERSION
    with tab4:
        st.markdown('<div class="sub-header">📝 Data Tweet & CCTV Log Lengkap</div>', unsafe_allow_html=True)
        
        # Sub-tabs untuk tweet dan CCTV
        sub_tab1, sub_tab2 = st.tabs(["📨 Semua Tweet", "📹 CCTV Log"])
        
        with sub_tab1:
            if tweets_df.empty:
                st.info("📭 Tidak ada data tweet yang tersedia")
                st.write("Jalankan pipeline di notebook untuk generate data tweet")
            else:
                st.markdown("**🔍 Filter Data Tweet:**")
                
                # Dapatkan unique values untuk filter
                unique_cities = ["Semua"]
                if 'city' in tweets_df.columns:
                    city_list = sorted([str(c) for c in tweets_df['city'].dropna().unique()])
                    unique_cities += city_list[:15]  # Batasi ke 15 kota pertama
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    selected_city = st.selectbox(
                        "Pilih Kota:",
                        unique_cities,
                        key="city_filter_tab4"
                    )
                
                with col2:
                    selected_risk = st.selectbox(
                        "Pilih Risk Level:",
                        ["Semua", "merah", "kuning", "hijau", "aman"],
                        key="risk_filter_tab4"
                    )
                
                with col3:
                    selected_sentiment = st.selectbox(
                        "Pilih Sentimen:",
                        ["Semua", "positif", "netral", "negatif"],
                        key="sentiment_filter_tab4"
                    )
                
                # Filter data
                filtered_tweets = tweets_df.copy()
                
                if selected_city != "Semua" and 'city' in filtered_tweets.columns:
                    filtered_tweets = filtered_tweets[filtered_tweets['city'] == selected_city]
                
                if selected_risk != "Semua" and 'risk_level' in filtered_tweets.columns:
                    filtered_tweets = filtered_tweets[filtered_tweets['risk_level'] == selected_risk]
                
                if selected_sentiment != "Semua" and 'sentiment' in filtered_tweets.columns:
                    filtered_tweets = filtered_tweets[filtered_tweets['sentiment'] == selected_sentiment]
                
                # Tampilkan jumlah hasil
                st.markdown(f"**📊 Menampilkan {len(filtered_tweets)} dari {len(tweets_df)} tweet**")
                
                if not filtered_tweets.empty:
                    # Pagination
                    items_per_page = st.selectbox(
                        "Items per page:",
                        [10, 25, 50, 100],
                        index=1,
                        key="tweet_pagination_tab4"
                    )
                    
                    total_pages = max(1, (len(filtered_tweets) + items_per_page - 1) // items_per_page)
                    page_number = st.number_input(
                        "Page:",
                        min_value=1,
                        max_value=total_pages,
                        value=1,
                        step=1,
                        key="tweet_page_tab4"
                    )
                    
                    start_idx = (page_number - 1) * items_per_page
                    end_idx = min(start_idx + items_per_page, len(filtered_tweets))
                    
                    st.write(f"**Halaman {page_number}/{total_pages}** (Item {start_idx+1}-{end_idx})")
                    
                    # Container dengan scroll
                    st.markdown('<div class="data-container">', unsafe_allow_html=True)
                    
                    for idx in range(start_idx, end_idx):
                        tweet = filtered_tweets.iloc[idx]
                        
                        # Format date jika ada
                        created_at = tweet.get('created_at', 'N/A')
                        if isinstance(created_at, (datetime, pd.Timestamp)):
                            created_at_str = created_at.strftime('%Y-%m-%d %H:%M')
                        else:
                            created_at_str = str(created_at)
                        
                        # Format city
                        city = str(tweet.get('city', 'N/A'))
                        
                        # Risk color mapping
                        risk_level = tweet.get('risk_level', 'aman')
                        risk_color = {
                            'merah': '🔴',
                            'kuning': '🟡', 
                            'hijau': '🟢',
                            'aman': '🔵'
                        }.get(risk_level, '⚪')
                        
                        # Buat expander
                        with st.expander(f"Tweet dari {city} - {created_at_str}", expanded=False):
                            col_a, col_b = st.columns([3, 1])
                            
                            with col_a:
                                # Text (potong jika terlalu panjang)
                                text = str(tweet.get('text', 'N/A'))
                                if len(text) > 300:
                                    text = text[:300] + "..."
                                st.write(f"**💬 Text:** {text}")
                                
                                # School
                                school = str(tweet.get('school', 'N/A'))
                                st.write(f"**🏫 Sekolah:** {school}")
                            
                            with col_b:
                                st.write(f"{risk_color} **Risk:** {risk_level}")
                                
                                # Sentiment dengan emoji
                                sentiment = tweet.get('sentiment', 'N/A')
                                sentiment_emoji = {
                                    'positif': '😊',
                                    'netral': '😐', 
                                    'negatif': '😔'
                                }.get(sentiment, '❓')
                                st.write(f"{sentiment_emoji} **Sentimen:** {sentiment}")
                                
                                # Risk score
                                risk_score = tweet.get('risk_score', 'N/A')
                                st.write(f"📊 **Score:** {risk_score}/20")
                            
                            # Footer info
                            st.caption(f"ID: {tweet.get('tweet_id', 'N/A')} • Category: {tweet.get('category', 'N/A')}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Download button
                    if 'text' in filtered_tweets.columns:
                        download_cols = ['text', 'city', 'school', 'sentiment', 'risk_level', 'risk_score', 'created_at']
                        available_cols = [col for col in download_cols if col in filtered_tweets.columns]
                        
                        if available_cols:
                            csv_tweets = filtered_tweets[available_cols].to_csv(index=False)
                            st.download_button(
                                label="📥 Download Data Tweet (CSV)",
                                data=csv_tweets,
                                file_name=f"tweet_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                mime="text/csv",
                                key="download_tweets_tab4"
                            )
                else:
                    st.info("Tidak ada tweet yang sesuai dengan filter")
        
        with sub_tab2:
            if cctv_df.empty:
                st.info("📭 Tidak ada data CCTV yang tersedia")
                st.write("Jalankan fungsi `generate_cctv_data()` di notebook untuk membuat data CCTV")
            else:
                st.markdown("**🔍 Filter CCTV Log:**")
                
                # Dapatkan unique values untuk filter
                cctv_cities = ["Semua"]
                if 'city' in cctv_df.columns:
                    city_list = sorted([str(c) for c in cctv_df['city'].dropna().unique()])
                    cctv_cities += city_list[:10]  # Batasi ke 10 kota pertama
                
                cctv_locations = ["Semua"]
                if 'location' in cctv_df.columns:
                    location_list = sorted([str(l) for l in cctv_df['location'].dropna().unique()])
                    cctv_locations += location_list
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    cctv_city_filter = st.selectbox(
                        "Pilih Kota CCTV:",
                        cctv_cities,
                        key="cctv_city_filter_tab4"
                    )
                
                with col2:
                    cctv_location_filter = st.selectbox(
                        "Pilih Lokasi:",
                        cctv_locations,
                        key="cctv_location_filter_tab4"
                    )
                
                with col3:
                    cctv_anomaly_filter = st.selectbox(
                        "Status Anomali:",
                        ["Semua", "Anomali", "Normal"],
                        key="cctv_anomaly_filter_tab4"
                    )
                
                # Filter CCTV data
                filtered_cctv = cctv_df.copy()
                
                if cctv_city_filter != "Semua" and 'city' in filtered_cctv.columns:
                    filtered_cctv = filtered_cctv[filtered_cctv['city'] == cctv_city_filter]
                
                if cctv_location_filter != "Semua" and 'location' in filtered_cctv.columns:
                    filtered_cctv = filtered_cctv[filtered_cctv['location'] == cctv_location_filter]
                
                if cctv_anomaly_filter != "Semua":
                    if cctv_anomaly_filter == "Anomali":
                        filtered_cctv = filtered_cctv[filtered_cctv['is_anomaly'] == True]
                    else:
                        filtered_cctv = filtered_cctv[filtered_cctv['is_anomaly'] == False]
                
                # Tampilkan jumlah hasil
                st.markdown(f"**📊 Menampilkan {len(filtered_cctv)} dari {len(cctv_df)} log CCTV**")
                
                if not filtered_cctv.empty:
                    # Pagination untuk CCTV
                    cctv_items_per_page = st.selectbox(
                        "Items per page CCTV:",
                        [10, 25, 50, 100],
                        index=1,
                        key="cctv_items_tab4"
                    )
                    
                    cctv_total_pages = max(1, (len(filtered_cctv) + cctv_items_per_page - 1) // cctv_items_per_page)
                    cctv_page_number = st.number_input(
                        "Page CCTV:",
                        min_value=1,
                        max_value=cctv_total_pages,
                        value=1,
                        step=1,
                        key="cctv_page_tab4"
                    )
                    
                    cctv_start_idx = (cctv_page_number - 1) * cctv_items_per_page
                    cctv_end_idx = min(cctv_start_idx + cctv_items_per_page, len(filtered_cctv))
                    
                    st.write(f"**Halaman {cctv_page_number}/{cctv_total_pages}** (Item {cctv_start_idx+1}-{cctv_end_idx})")
                    
                    # Container dengan scroll
                    st.markdown('<div class="data-container">', unsafe_allow_html=True)
                    
                    for idx in range(cctv_start_idx, cctv_end_idx):
                        log = filtered_cctv.iloc[idx]
                        
                        # Format timestamp
                        timestamp = log.get('timestamp', 'N/A')
                        if isinstance(timestamp, (datetime, pd.Timestamp)):
                            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M')
                        else:
                            timestamp_str = str(timestamp)
                        
                        # Anomaly status
                        is_anomaly = log.get('is_anomaly', False)
                        anomaly_status = "🔴 ANOMALI" if is_anomaly else "🟢 NORMAL"
                        anomaly_color = "🔴" if is_anomaly else "🟢"
                        
                        # CCTV ID - coba beberapa kemungkinan field
                        cctv_id = log.get('cctv_id', 'N/A')
                        if cctv_id == 'N/A':
                            cctv_id = log.get('log_id', 'N/A')  # Coba field alternatif
                        
                        # Buat expander
                        with st.expander(f"{anomaly_color} CCTV {cctv_id} - {timestamp_str}", expanded=False):
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                # School
                                school = str(log.get('school', 'N/A'))
                                st.write(f"**🏫 Sekolah:** {school}")
                                
                                # Location
                                location = str(log.get('location', 'N/A'))
                                st.write(f"**📍 Lokasi:** {location}")
                                
                                # City
                                city = str(log.get('city', 'N/A'))
                                st.write(f"**🌆 Kota:** {city}")
                            
                            with col_b:
                                # Status
                                st.write(f"**📊 Status:** {anomaly_status}")
                                
                                # Warning level
                                warning_level = log.get('warning_level', 'N/A')
                                warning_emoji = {
                                    'merah': '🔴',
                                    'kuning': '🟡',
                                    'hijau': '🟢'
                                }.get(warning_level, '⚪')
                                st.write(f"{warning_emoji} **Warning:** {warning_level}")
                                
                                # Metrics
                                crowd_level = log.get('crowd_level', 'N/A')
                                noise_level = log.get('noise_level', 'N/A')
                                st.write(f"**👥 Keramaian:** {crowd_level} orang")
                                st.write(f"**🔊 Kebisingan:** {noise_level} dB")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Download button untuk CCTV
                    available_cctv_cols = []
                    possible_cols = ['timestamp', 'cctv_id', 'log_id', 'school', 'city', 'location', 
                                   'crowd_level', 'noise_level', 'is_anomaly', 'warning_level']
                    
                    for col in possible_cols:
                        if col in filtered_cctv.columns:
                            available_cctv_cols.append(col)
                    
                    if available_cctv_cols:
                        # Buat copy untuk download
                        download_cctv = filtered_cctv[available_cctv_cols].copy()
                        
                        # Format timestamp untuk CSV
                        if 'timestamp' in download_cctv.columns:
                            download_cctv['timestamp'] = download_cctv['timestamp'].apply(
                                lambda x: x.strftime('%Y-%m-%d %H:%M') if isinstance(x, (datetime, pd.Timestamp)) else str(x)
                            )
                        
                        csv_cctv = download_cctv.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Data CCTV (CSV)",
                            data=csv_cctv,
                            file_name=f"cctv_logs_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv",
                            key="download_cctv_tab4"
                        )
                else:
                    st.info("Tidak ada log CCTV yang sesuai dengan filter")
    
    # Tab 5: Data Detail - FIXED VERSION
    with tab5:
        st.markdown('<div class="sub-header">📋 Data Detail dari MongoDB</div>', unsafe_allow_html=True)
        
        if not tweets_df.empty:
            # Tampilkan distribusi
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**📊 Distribusi Sentimen:**")
                if 'sentiment' in tweets_df.columns:
                    sentiment_counts = tweets_df['sentiment'].value_counts()
                    for sent, count in sentiment_counts.items():
                        percentage = (count / len(tweets_df)) * 100
                        st.write(f"- {sent}: {count} ({percentage:.1f}%)")
                else:
                    st.write("Kolom 'sentiment' tidak ditemukan")
            
            with col2:
                st.write("**⚠️ Distribusi Risk Level:**")
                if 'risk_level' in tweets_df.columns:
                    risk_counts = tweets_df['risk_level'].value_counts()
                    for risk, count in risk_counts.items():
                        percentage = (count / len(tweets_df)) * 100
                        st.write(f"- {risk}: {count} ({percentage:.1f}%)")
                else:
                    st.write("Kolom 'risk_level' tidak ditemukan")
            
            with col3:
                st.write("**📍 Top 5 Kota:**")
                if 'city' in tweets_df.columns:
                    city_counts = tweets_df['city'].value_counts().head(5)
                    for city, count in city_counts.items():
                        percentage = (count / len(tweets_df)) * 100
                        st.write(f"- {city}: {count} ({percentage:.1f}%)")
                else:
                    st.write("Kolom 'city' tidak ditemukan")
            
            # Tampilkan sample data
            st.subheader("📊 Sample Data Tweet (10 terbaru)")
            
            # Sort by date jika ada
            if 'created_at' in tweets_df.columns:
                tweets_df_sorted = tweets_df.sort_values('created_at', ascending=False)
            else:
                tweets_df_sorted = tweets_df
            
            # Pilih kolom untuk ditampilkan
            show_cols = ['text', 'city', 'school', 'sentiment', 'risk_level', 'risk_score', 'category', 'created_at']
            available_cols = [col for col in show_cols if col in tweets_df_sorted.columns]
            
            if available_cols:
                sample_df = tweets_df_sorted[available_cols].head(10).copy()
                
                # Format tanggal
                if 'created_at' in sample_df.columns:
                    sample_df['created_at'] = pd.to_datetime(sample_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                
                # Format text (potong jika terlalu panjang)
                if 'text' in sample_df.columns:
                    sample_df['text'] = sample_df['text'].apply(lambda x: x[:100] + '...' if len(str(x)) > 100 else str(x))
                
                # Tampilkan dataframe
                st.dataframe(sample_df, use_container_width=True, height=400)
                
                # Download button
                csv = sample_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Sample Data (CSV)",
                    data=csv,
                    file_name=f"sample_tweets_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="download_sample_tab5"
                )
            else:
                st.info("Kolom data tidak tersedia")
        else:
            st.info("Tidak ada data tweet yang tersedia")
        
        # CCTV Data Section
        st.subheader("📹 Data CCTV Log")
        
        if not cctv_df.empty:
            # Tampilkan distribusi CCTV
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**📍 Lokasi CCTV:**")
                if 'location' in cctv_df.columns:
                    location_counts = cctv_df['location'].value_counts()
                    for loc, count in location_counts.items():
                        percentage = (count / len(cctv_df)) * 100
                        st.write(f"- {loc}: {count} ({percentage:.1f}%)")
            
            with col2:
                st.write("**⚠️ Status Anomali:**")
                if 'is_anomaly' in cctv_df.columns:
                    anomaly_counts = cctv_df['is_anomaly'].value_counts()
                    total = len(cctv_df)
                    for status, count in anomaly_counts.items():
                        status_text = "Anomali" if status else "Normal"
                        percentage = (count / total) * 100
                        st.write(f"- {status_text}: {count} ({percentage:.1f}%)")
            
            # Tampilkan sample CCTV data
            st.write("**Sample CCTV Logs (10 terbaru):**")
            
            # Sort by timestamp jika ada
            if 'timestamp' in cctv_df.columns:
                cctv_df_sorted = cctv_df.sort_values('timestamp', ascending=False)
            else:
                cctv_df_sorted = cctv_df
            
            # Pilih kolom CCTV untuk ditampilkan
            cctv_show_cols = ['cctv_id', 'log_id', 'school', 'city', 'location', 'crowd_level', 'noise_level', 'is_anomaly', 'timestamp']
            cctv_available_cols = [col for col in cctv_show_cols if col in cctv_df_sorted.columns]
            
            if cctv_available_cols:
                cctv_sample = cctv_df_sorted[cctv_available_cols].head(10).copy()
                
                # Format timestamp
                if 'timestamp' in cctv_sample.columns:
                    cctv_sample['timestamp'] = pd.to_datetime(cctv_sample['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                
                # Format boolean untuk anomaly
                if 'is_anomaly' in cctv_sample.columns:
                    cctv_sample['is_anomaly'] = cctv_sample['is_anomaly'].apply(lambda x: '✅ YA' if x else '❌ TIDAK')
                
                st.dataframe(cctv_sample, use_container_width=True, height=300)
                
                # Download button untuk CCTV
                csv_cctv = cctv_sample.to_csv(index=False)
                st.download_button(
                    label="📥 Download Sample CCTV (CSV)",
                    data=csv_cctv,
                    file_name=f"sample_cctv_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="download_cctv_tab5"
                )
            else:
                st.info("Kolom data CCTV tidak tersedia")
        else:
            st.info("Tidak ada data CCTV yang tersedia")
    
    # ========== FOOTER ==========
    st.markdown("---")
    st.markdown("**Sistem Deteksi Bullying** • Teknik Informatika UNRAM • © 2025")
    st.caption(f"Dashboard terakhir di-load: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()