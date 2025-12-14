import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(
    page_title="EBITDA Performans Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern Dark Theme CSS - React tarzı
st.markdown("""
<style>
    /* Ana tema */
    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0a0a0f 100%);
    }
    
    /* Header */
    .main-header {
        background: linear-gradient(90deg, #f59e0b 0%, #ea580c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0;
        letter-spacing: -0.5px;
    }
    
    .sub-header {
        color: #64748b;
        font-size: 0.95rem;
        margin-top: 0;
    }
    
    /* Metric Kartları */
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.4);
    }
    
    .metric-card-alert {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.2rem;
        box-shadow: 0 8px 32px rgba(220,38,38,0.3);
        position: relative;
        overflow: hidden;
    }
    .metric-card-alert::before {
        content: '';
        position: absolute;
        top: 8px;
        right: 8px;
        width: 10px;
        height: 10px;
        background: #fca5a5;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
    }
    
    .metric-card-warning {
        background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.2rem;
        box-shadow: 0 8px 32px rgba(234,88,12,0.3);
    }
    
    .metric-card-success {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.2rem;
        box-shadow: 0 8px 32px rgba(5,150,105,0.3);
    }
    
    .metric-card-purple {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.2rem;
        box-shadow: 0 8px 32px rgba(124,58,237,0.3);
    }
    
    .metric-title {
        color: rgba(255,255,255,0.7);
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    
    .metric-value {
        color: #ffffff;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
    }
    
    .metric-delta {
        font-size: 0.8rem;
        font-weight: 500;
        margin-top: 4px;
    }
    .metric-delta-negative { color: #fca5a5; }
    .metric-delta-positive { color: #86efac; }
    .metric-delta-neutral { color: rgba(255,255,255,0.6); }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.2); }
    }
    
    /* SM Kartları */
    .sm-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1rem;
        transition: border-color 0.2s;
    }
    .sm-card:hover {
        border-color: rgba(245,158,11,0.5);
    }
    
    .sm-name {
        color: #ffffff;
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    .sm-stat {
        display: flex;
        justify-content: space-between;
        margin-bottom: 4px;
    }
    
    .sm-label {
        color: #64748b;
        font-size: 0.75rem;
    }
    
    .sm-value {
        color: #ffffff;
        font-size: 0.9rem;
        font-weight: 600;
    }
    
    .sm-value-negative { color: #f87171; }
    .sm-value-positive { color: #4ade80; }
    
    /* Badge'ler */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    
    .badge-red {
        background: rgba(239,68,68,0.2);
        color: #f87171;
        border: 1px solid rgba(239,68,68,0.3);
    }
    
    .badge-orange {
        background: rgba(249,115,22,0.2);
        color: #fb923c;
        border: 1px solid rgba(249,115,22,0.3);
    }
    
    .badge-green {
        background: rgba(34,197,94,0.2);
        color: #4ade80;
        border: 1px solid rgba(34,197,94,0.3);
    }
    
    .badge-purple {
        background: rgba(168,85,247,0.2);
        color: #c084fc;
        border: 1px solid rgba(168,85,247,0.3);
    }
    
    .badge-gray {
        background: rgba(100,116,139,0.2);
        color: #94a3b8;
        border: 1px solid rgba(100,116,139,0.3);
    }
    
    /* Tab stilleri */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(30, 41, 59, 0.4);
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(245,158,11,0.2) !important;
        color: #f59e0b !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background: rgba(30, 41, 59, 0.4);
        border: 2px dashed rgba(245,158,11,0.3);
        border-radius: 12px;
        padding: 1rem;
    }
    
    /* Section divider */
    .section-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        margin: 2rem 0;
    }
    
    /* Info box */
    .info-box {
        background: rgba(30, 41, 59, 0.6);
        border-left: 4px solid #f59e0b;
        border-radius: 0 8px 8px 0;
        padding: 1rem;
        color: #e2e8f0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #1e293b;
    }
    ::-webkit-scrollbar-thumb {
        background: #475569;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #64748b;
    }
</style>
""", unsafe_allow_html=True)


def extract_code(magaza):
    if pd.isna(magaza):
        return None
    return str(magaza).split()[0]


def analyze_reason(row):
    sebepler = []
    if row['Ciro_Degisim'] < -50000:
        sebepler.append('CİRO')
    if row['Gider_Degisim'] > 30000:
        sebepler.append('GİDER')
    if row['Marj_Degisim'] < -50000:
        sebepler.append('MARJ')
    
    if not sebepler:
        return 'KARMA' if row['EBITDA_Degisim'] < 0 else 'POZİTİF'
    return '+'.join(sebepler)


@st.cache_data
def load_and_process_data(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name='EBITDA', header=1)
    df = df[df['Kar / Zarar'] != 'GENEL'].copy()
    
    donemler = df['Mali yıl/dönem - Orta uzunl.metin'].dropna().unique()
    
    ay_map = {'Ocak': 1, 'Şubat': 2, 'Mart': 3, 'Nisan': 4, 'Mayıs': 5, 'Haziran': 6,
              'Temmuz': 7, 'Ağustos': 8, 'Eylül': 9, 'Ekim': 10, 'Kasım': 11, 'Aralık': 12}
    
    def parse_donem(d):
        try:
            parts = d.split()
            ay = ay_map.get(parts[0], 0)
            yil = int(parts[1])
            return yil * 100 + ay
        except:
            return 0
    
    donemler = sorted(donemler, key=parse_donem)
    
    if len(donemler) < 2:
        return None, None, "En az 2 dönem verisi gerekli"
    
    onceki_donem = donemler[0]
    guncel_donem = donemler[1]
    
    onceki = df[df['Mali yıl/dönem - Orta uzunl.metin'] == onceki_donem].copy()
    guncel = df[df['Mali yıl/dönem - Orta uzunl.metin'] == guncel_donem].copy()
    
    onceki['Kod'] = onceki['Mağaza'].apply(extract_code)
    guncel['Kod'] = guncel['Mağaza'].apply(extract_code)
    
    common = set(onceki['Kod'].dropna()) & set(guncel['Kod'].dropna())
    
    onceki_c = onceki[onceki['Kod'].isin(common)].set_index('Kod')
    guncel_c = guncel[guncel['Kod'].isin(common)].set_index('Kod')
    
    comparison = pd.DataFrame({
        'Kod': list(common),
        'Mağaza': [guncel_c.loc[k, 'Mağaza'] if k in guncel_c.index else '' for k in common],
        'BS': [guncel_c.loc[k, 'Bölge Sorumlusu - Metin'] if k in guncel_c.index else '' for k in common],
        'SM': [guncel_c.loc[k, 'Satış Müdürü - Metin'] if k in guncel_c.index else '' for k in common],
        'm2': [guncel_c.loc[k, 'Net Metrekare'] if k in guncel_c.index else 0 for k in common],
        'Onceki_Ciro': [onceki_c.loc[k, 'Net Satış (KDV Hariç)'] if k in onceki_c.index else 0 for k in common],
        'Guncel_Ciro': [guncel_c.loc[k, 'Net Satış (KDV Hariç)'] if k in guncel_c.index else 0 for k in common],
        'Onceki_Gider': [onceki_c.loc[k, 'Toplam Mağaza Giderleri'] if k in onceki_c.index else 0 for k in common],
        'Guncel_Gider': [guncel_c.loc[k, 'Toplam Mağaza Giderleri'] if k in guncel_c.index else 0 for k in common],
        'Onceki_Marj': [onceki_c.loc[k, 'Net Marj'] if k in onceki_c.index else 0 for k in common],
        'Guncel_Marj': [guncel_c.loc[k, 'Net Marj'] if k in guncel_c.index else 0 for k in common],
        'Onceki_EBITDA': [onceki_c.loc[k, 'Mağaza Kar/Zararı'] if k in onceki_c.index else 0 for k in common],
        'Guncel_EBITDA': [guncel_c.loc[k, 'Mağaza Kar/Zararı'] if k in guncel_c.index else 0 for k in common],
    })
    
    numeric_cols = ['Onceki_Ciro', 'Guncel_Ciro', 'Onceki_Gider', 'Guncel_Gider', 
                    'Onceki_Marj', 'Guncel_Marj', 'Onceki_EBITDA', 'Guncel_EBITDA', 'm2']
    for col in numeric_cols:
        comparison[col] = pd.to_numeric(comparison[col], errors='coerce').fillna(0)
    
    comparison['EBITDA_Degisim'] = comparison['Guncel_EBITDA'] - comparison['Onceki_EBITDA']
    comparison['Ciro_Degisim'] = comparison['Guncel_Ciro'] - comparison['Onceki_Ciro']
    comparison['Gider_Degisim'] = comparison['Guncel_Gider'] - comparison['Onceki_Gider']
    comparison['Marj_Degisim'] = comparison['Guncel_Marj'] - comparison['Onceki_Marj']
    
    comparison['Gider_Ciro_Oran'] = np.where(
        comparison['Guncel_Ciro'] > 0,
        (comparison['Guncel_Gider'] / comparison['Guncel_Ciro']) * 100,
        0
    )
    
    comparison['Sebep'] = comparison.apply(analyze_reason, axis=1)
    comparison['Acil'] = (comparison['Guncel_EBITDA'] < 0) | (comparison['EBITDA_Degisim'] < -100000)
    comparison['Ust_Uste_Negatif'] = (comparison['Onceki_EBITDA'] < 0) & (comparison['Guncel_EBITDA'] < 0)
    
    valid_ratios = comparison[(comparison['Gider_Ciro_Oran'] > 0) & (comparison['Gider_Ciro_Oran'] < 100)]['Gider_Ciro_Oran']
    benchmark = valid_ratios.median() if len(valid_ratios) > 0 else 14.43
    
    comparison['Tasarruf_Potansiyeli'] = np.where(
        (comparison['Guncel_Ciro'] > 0) & (comparison['Gider_Ciro_Oran'] > benchmark),
        comparison['Guncel_Gider'] - (comparison['Guncel_Ciro'] * benchmark / 100),
        0
    )
    comparison['Tasarruf_Potansiyeli'] = comparison['Tasarruf_Potansiyeli'].clip(lower=0)
    
    donem_info = {'onceki': onceki_donem, 'guncel': guncel_donem, 'benchmark': benchmark}
    
    return comparison, donem_info, None


def format_currency(value):
    if pd.isna(value):
        return "-"
    if abs(value) >= 1000000:
        return f"{value/1000000:.2f}M"
    elif abs(value) >= 1000:
        return f"{value/1000:.0f}K"
    return f"{value:.0f}"


def render_metric_card(title, value, delta=None, delta_type="neutral", card_type="default"):
    card_class = {
        "default": "metric-card",
        "alert": "metric-card-alert",
        "warning": "metric-card-warning",
        "success": "metric-card-success",
        "purple": "metric-card-purple"
    }.get(card_type, "metric-card")
    
    delta_class = {
        "negative": "metric-delta-negative",
        "positive": "metric-delta-positive",
        "neutral": "metric-delta-neutral"
    }.get(delta_type, "metric-delta-neutral")
    
    delta_html = f'<p class="metric-delta {delta_class}">{delta}</p>' if delta else ''
    
    return f"""
    <div class="{card_class}">
        <p class="metric-title">{title}</p>
        <p class="metric-value">{value}</p>
        {delta_html}
    </div>
    """


def render_sm_card(sm_name, magaza_sayisi, guncel_ebitda, degisim, degisim_pct, acil_sayisi):
    value_class = "sm-value-negative" if degisim < 0 else "sm-value-positive"
    degisim_str = f"{format_currency(degisim)}₺"
    if degisim > 0:
        degisim_str = f"+{degisim_str}"
    
    acil_html = f'<span class="badge badge-red" style="margin-left:8px">{acil_sayisi} acil</span>' if acil_sayisi > 0 else ''
    
    return f"""
    <div class="sm-card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <span class="sm-name">{sm_name}</span>
            <span class="badge badge-gray">{magaza_sayisi}</span>
        </div>
        <div class="sm-stat">
            <span class="sm-label">Güncel EBITDA</span>
            <span class="sm-value">{format_currency(guncel_ebitda)}₺</span>
        </div>
        <div class="sm-stat">
            <span class="sm-label">Değişim</span>
            <span class="sm-value {value_class}">{degisim_str} ({degisim_pct:.1f}%)</span>
        </div>
        <div style="margin-top:8px">{acil_html}</div>
    </div>
    """


def main():
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
            <div style="background:linear-gradient(135deg,#f59e0b,#ea580c);padding:10px;border-radius:12px">
                <span style="font-size:1.5rem">📊</span>
            </div>
            <div>
                <p class="main-header">EBITDA Performans Dashboard</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        uploaded_file = st.file_uploader("", type=['xlsx', 'xls'], label_visibility="collapsed")
    
    if not uploaded_file:
        st.markdown("""
        <div class="info-box">
            <strong>📁 EBITDA Excel dosyasını yükleyin</strong><br>
            <span style="color:#94a3b8;font-size:0.9rem">MIS_BW_03_Mağaza_Bazında_EBITDA formatında, en az 2 dönem verisi içeren dosya</span>
        </div>
        """, unsafe_allow_html=True)
        return
    
    with st.spinner("Veri işleniyor..."):
        df, donem_info, error = load_and_process_data(uploaded_file)
    
    if error:
        st.error(f"❌ {error}")
        return
    
    if df is None or len(df) == 0:
        st.error("Veri işlenemedi")
        return
    
    # Dönem bilgisi
    st.markdown(f'<p class="sub-header">{donem_info["onceki"]} → {donem_info["guncel"]} Karşılaştırması</p>', unsafe_allow_html=True)
    
    # Metrikler
    toplam_onceki = df['Onceki_EBITDA'].sum()
    toplam_guncel = df['Guncel_EBITDA'].sum()
    toplam_degisim = toplam_guncel - toplam_onceki
    degisim_pct = (toplam_degisim / abs(toplam_onceki) * 100) if toplam_onceki != 0 else 0
    acil_sayi = len(df[df['Acil']])
    yangin_sayi = len(df[df['Ust_Uste_Negatif']])
    tasarruf = df['Tasarruf_Potansiyeli'].sum()
    
    # KPI Kartları
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    
    cols = st.columns(6)
    
    with cols[0]:
        st.markdown(render_metric_card(
            f"💰 {donem_info['guncel']} EBITDA",
            f"{format_currency(toplam_guncel)}₺",
            f"↓ {degisim_pct:.1f}% ({format_currency(toplam_degisim)}₺)",
            "negative" if toplam_degisim < 0 else "positive",
            "default"
        ), unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown(render_metric_card(
            "🏪 Mağaza Sayısı",
            str(len(df)),
            f"{len(df[df['Guncel_EBITDA'] < 0])} negatif",
            "neutral",
            "default"
        ), unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown(render_metric_card(
            "🚨 Acil Müdahale",
            str(acil_sayi),
            "mağaza",
            "negative",
            "alert"
        ), unsafe_allow_html=True)
    
    with cols[3]:
        st.markdown(render_metric_card(
            "🔥 Yangın",
            str(yangin_sayi),
            "üst üste negatif",
            "negative",
            "warning"
        ), unsafe_allow_html=True)
    
    with cols[4]:
        st.markdown(render_metric_card(
            "📐 Benchmark G/C",
            f"%{donem_info['benchmark']:.1f}",
            "medyan oran",
            "neutral",
            "purple"
        ), unsafe_allow_html=True)
    
    with cols[5]:
        st.markdown(render_metric_card(
            "💎 Tasarruf Potansiyeli",
            f"{format_currency(tasarruf)}₺",
            "normalize edilirse",
            "positive",
            "success"
        ), unsafe_allow_html=True)
    
    # Divider
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # SM Performans
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px">
        <span style="font-size:1.2rem">👥</span>
        <span style="color:#ffffff;font-size:1.1rem;font-weight:600">SM Bazında Performans</span>
    </div>
    """, unsafe_allow_html=True)
    
    sm_df = df.groupby('SM').agg({
        'Onceki_EBITDA': 'sum',
        'Guncel_EBITDA': 'sum',
        'EBITDA_Degisim': 'sum',
        'Kod': 'count',
        'Acil': 'sum'
    }).reset_index()
    sm_df.columns = ['SM', 'Onceki', 'Guncel', 'Degisim', 'Magaza', 'Acil']
    sm_df['Degisim_Pct'] = (sm_df['Degisim'] / sm_df['Onceki'].abs() * 100)
    sm_df = sm_df[sm_df['Magaza'] > 2].sort_values('Degisim')
    
    sm_cols = st.columns(len(sm_df))
    for i, (_, row) in enumerate(sm_df.iterrows()):
        with sm_cols[i]:
            st.markdown(render_sm_card(
                row['SM'].split()[0] if pd.notna(row['SM']) else 'N/A',
                int(row['Magaza']),
                row['Guncel'],
                row['Degisim'],
                row['Degisim_Pct'],
                int(row['Acil'])
            ), unsafe_allow_html=True)
    
    # Divider
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        f"🚨 Acil Müdahale ({acil_sayi})",
        f"🔥 Yangın ({yangin_sayi})",
        f"📉 Düşenler ({len(df[df['EBITDA_Degisim'] < 0])})",
        f"📈 Gelişenler ({len(df[df['EBITDA_Degisim'] > 0])})",
        f"📊 Tümü ({len(df)})"
    ])
    
    display_cols = ['Kod', 'Mağaza', 'SM', 'Guncel_EBITDA', 'EBITDA_Degisim', 'Sebep', 'Gider_Ciro_Oran', 'Tasarruf_Potansiyeli']
    col_names = ['Kod', 'Mağaza', 'SM', 'EBITDA', 'Değişim', 'Sebep', 'G/C %', 'Tasarruf']
    
    def style_dataframe(df_display):
        return df_display.style.format({
            'EBITDA': '{:,.0f}',
            'Değişim': '{:+,.0f}',
            'G/C %': '{:.1f}%',
            'Tasarruf': '{:,.0f}'
        })
    
    with tab1:
        acil_df = df[df['Acil']].sort_values('EBITDA_Degisim')[display_cols].copy()
        acil_df.columns = col_names
        acil_df['SM'] = acil_df['SM'].apply(lambda x: x.split()[0] if pd.notna(x) else '')
        acil_df['Mağaza'] = acil_df['Mağaza'].apply(lambda x: x[:35] if pd.notna(x) else '')
        st.dataframe(style_dataframe(acil_df), height=450, use_container_width=True)
    
    with tab2:
        if yangin_sayi > 0:
            st.markdown("""
            <div style="background:rgba(249,115,22,0.1);border:1px solid rgba(249,115,22,0.3);border-radius:8px;padding:12px;margin-bottom:16px">
                <strong style="color:#fb923c">⚠️ Bu mağazalara ÖNCE gidilmeli!</strong>
                <span style="color:#94a3b8;font-size:0.9rem;margin-left:8px">Üst üste 2 ay negatif EBITDA</span>
            </div>
            """, unsafe_allow_html=True)
            
            yangin_df = df[df['Ust_Uste_Negatif']].sort_values('Guncel_EBITDA')[display_cols].copy()
            yangin_df.columns = col_names
            yangin_df['SM'] = yangin_df['SM'].apply(lambda x: x.split()[0] if pd.notna(x) else '')
            yangin_df['Mağaza'] = yangin_df['Mağaza'].apply(lambda x: x[:35] if pd.notna(x) else '')
            st.dataframe(style_dataframe(yangin_df), height=400, use_container_width=True)
        else:
            st.success("✅ Üst üste negatif mağaza yok!")
    
    with tab3:
        col1, col2 = st.columns([1, 2])
        with col1:
            sebep_counts = df[df['EBITDA_Degisim'] < 0]['Sebep'].value_counts()
            fig = px.pie(
                values=sebep_counts.values, 
                names=sebep_counts.index,
                color_discrete_sequence=['#ef4444', '#f97316', '#a855f7', '#64748b']
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#94a3b8',
                showlegend=True,
                legend=dict(font=dict(size=11)),
                margin=dict(t=20, b=20, l=20, r=20),
                height=280
            )
            fig.update_traces(textinfo='percent+label', textfont_size=11)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            dusen_df = df[df['EBITDA_Degisim'] < 0].sort_values('EBITDA_Degisim')[display_cols].copy()
            dusen_df.columns = col_names
            dusen_df['SM'] = dusen_df['SM'].apply(lambda x: x.split()[0] if pd.notna(x) else '')
            dusen_df['Mağaza'] = dusen_df['Mağaza'].apply(lambda x: x[:35] if pd.notna(x) else '')
            st.dataframe(style_dataframe(dusen_df), height=280, use_container_width=True)
    
    with tab4:
        gelisen_df = df[df['EBITDA_Degisim'] > 0].sort_values('EBITDA_Degisim', ascending=False)[display_cols].copy()
        gelisen_df.columns = col_names
        gelisen_df['SM'] = gelisen_df['SM'].apply(lambda x: x.split()[0] if pd.notna(x) else '')
        gelisen_df['Mağaza'] = gelisen_df['Mağaza'].apply(lambda x: x[:35] if pd.notna(x) else '')
        st.dataframe(style_dataframe(gelisen_df), height=450, use_container_width=True)
    
    with tab5:
        col1, col2, col3 = st.columns(3)
        with col1:
            sm_filter = st.multiselect("SM", options=df['SM'].dropna().unique(), key="sm_filter")
        with col2:
            sebep_filter = st.multiselect("Sebep", options=df['Sebep'].unique(), key="sebep_filter")
        with col3:
            sort_by = st.selectbox("Sırala", ['EBITDA_Degisim', 'Guncel_EBITDA', 'Gider_Ciro_Oran'], key="sort")
        
        filtered = df.copy()
        if sm_filter:
            filtered = filtered[filtered['SM'].isin(sm_filter)]
        if sebep_filter:
            filtered = filtered[filtered['Sebep'].isin(sebep_filter)]
        filtered = filtered.sort_values(sort_by)
        
        all_display = filtered[display_cols].copy()
        all_display.columns = col_names
        all_display['SM'] = all_display['SM'].apply(lambda x: x.split()[0] if pd.notna(x) else '')
        all_display['Mağaza'] = all_display['Mağaza'].apply(lambda x: x[:35] if pd.notna(x) else '')
        st.dataframe(style_dataframe(all_display), height=400, use_container_width=True)
    
    # Divider
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # Gider Analizi
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px">
        <span style="font-size:1.2rem">💸</span>
        <span style="color:#ffffff;font-size:1.1rem;font-weight:600">Gider Analizi - En Yüksek Gider/Ciro</span>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        gider_top = df[df['Gider_Ciro_Oran'] > 0].nlargest(15, 'Gider_Ciro_Oran')
        
        fig = go.Figure()
        colors = ['#ef4444' if x > donem_info['benchmark'] * 2 else '#f97316' if x > donem_info['benchmark'] else '#22c55e' 
                  for x in gider_top['Gider_Ciro_Oran']]
        fig.add_trace(go.Bar(
            x=gider_top['Kod'],
            y=gider_top['Gider_Ciro_Oran'],
            marker_color=colors,
            text=[f"{x:.1f}%" for x in gider_top['Gider_Ciro_Oran']],
            textposition='outside'
        ))
        fig.add_hline(
            y=donem_info['benchmark'], 
            line_dash="dash", 
            line_color="#22c55e",
            annotation_text=f"Benchmark: %{donem_info['benchmark']:.1f}",
            annotation_font_color="#22c55e"
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#94a3b8',
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title='Gider/Ciro %'),
            margin=dict(t=40, b=40),
            height=320
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        gider_df = df[df['Gider_Ciro_Oran'] > 0].nlargest(10, 'Gider_Ciro_Oran')[
            ['Kod', 'Gider_Ciro_Oran', 'Tasarruf_Potansiyeli']
        ].copy()
        gider_df.columns = ['Kod', 'G/C %', 'Tasarruf']
        gider_df['Fark'] = gider_df['G/C %'] - donem_info['benchmark']
        
        st.dataframe(
            gider_df.style.format({
                'G/C %': '{:.1f}%',
                'Tasarruf': '{:,.0f}',
                'Fark': '{:+.1f}%'
            }),
            height=320,
            use_container_width=True
        )
    
    # Export
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df[df['Acil']].to_excel(writer, sheet_name='ACİL', index=False)
            df[df['Ust_Uste_Negatif']].to_excel(writer, sheet_name='YANGIN', index=False)
            df.to_excel(writer, sheet_name='TÜM VERİ', index=False)
            sm_df.to_excel(writer, sheet_name='SM ÖZET', index=False)
        
        st.download_button(
            "📥 Excel İndir",
            data=output.getvalue(),
            file_name=f"EBITDA_{donem_info['guncel'].replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col2:
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📄 CSV İndir",
            data=csv,
            file_name=f"EBITDA_{donem_info['guncel'].replace(' ', '_')}.csv",
            mime="text/csv"
        )
    
    # Footer
    st.markdown("""
    <div style="text-align:center;margin-top:32px;padding:16px;color:#475569;font-size:0.8rem">
        📊 A101 EBITDA Performans Dashboard | Antalya Bölgesi
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
