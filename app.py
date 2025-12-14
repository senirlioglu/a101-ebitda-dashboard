import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import json
from pathlib import Path

st.set_page_config(
    page_title="EBITDA Karar Motoru",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Minimal karar odaklı tema
st.markdown("""
<style>
    .stApp { background: #0f172a; }
    
    .main-title { color: #f59e0b; font-size: 1.8rem; font-weight: 700; }
    .sub-title { color: #64748b; font-size: 0.9rem; }
    
    /* KPI Kartları */
    .kpi-row { display: flex; gap: 16px; margin-bottom: 24px; }
    .kpi-box {
        flex: 1;
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .kpi-box-alert {
        flex: 1;
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
        border: 1px solid #dc2626;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s;
    }
    .kpi-box-alert:hover { transform: scale(1.02); }
    .kpi-box-warning {
        flex: 1;
        background: linear-gradient(135deg, #78350f 0%, #92400e 100%);
        border: 1px solid #f59e0b;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s;
    }
    .kpi-box-warning:hover { transform: scale(1.02); }
    
    .kpi-label { color: #94a3b8; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { color: #ffffff; font-size: 1.8rem; font-weight: 700; margin: 4px 0; }
    .kpi-delta { font-size: 0.85rem; }
    
    /* Zaman Serisi Tablosu */
    .time-table { width: 100%; border-collapse: collapse; margin: 16px 0; }
    .time-table th {
        background: #0f172a;
        color: #64748b;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 12px 8px;
        text-align: right;
        border-bottom: 1px solid #334155;
    }
    .time-table th:first-child { text-align: left; }
    .time-table td {
        padding: 12px 8px;
        border-bottom: 1px solid #1e293b;
        color: #e2e8f0;
        font-size: 0.9rem;
        text-align: right;
    }
    .time-table td:first-child { text-align: left; font-weight: 600; }
    .time-table tr:hover { background: #1e293b; }
    
    /* SM Grup Kartları */
    .sm-group {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        margin: 16px 0;
        overflow: hidden;
    }
    .sm-group-header {
        background: #0f172a;
        padding: 12px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
        border-bottom: 1px solid #334155;
    }
    .sm-group-header:hover { background: #1a2744; }
    .sm-group-title { color: #f59e0b; font-weight: 600; font-size: 1rem; }
    .sm-group-badge { 
        background: #334155; 
        color: #94a3b8; 
        padding: 4px 12px; 
        border-radius: 20px; 
        font-size: 0.8rem; 
    }
    
    /* Mağaza Kartı */
    .magaza-card {
        border-left: 3px solid #475569;
        background: #0f172a;
        padding: 16px;
        margin: 8px 16px;
        border-radius: 0 8px 8px 0;
    }
    .magaza-card-alert { border-left-color: #ef4444; }
    .magaza-card-warning { border-left-color: #f97316; }
    
    .magaza-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .magaza-kod { color: #ffffff; font-weight: 700; font-size: 1rem; }
    .magaza-isim { color: #94a3b8; font-size: 0.85rem; margin-left: 8px; }
    
    /* Zaman Serisi Satırı */
    .time-series {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 8px;
        background: #1e293b;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    .time-item { text-align: center; }
    .time-item-label { color: #64748b; font-size: 0.65rem; text-transform: uppercase; }
    .time-item-value { color: #e2e8f0; font-size: 0.95rem; font-weight: 600; }
    .time-item-delta { font-size: 0.8rem; }
    
    /* Sebep Analizi */
    .sebep-box {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        margin-top: 12px;
    }
    .sebep-title { color: #f59e0b; font-size: 0.85rem; font-weight: 600; margin-bottom: 12px; }
    .sebep-item {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 8px 0;
        border-bottom: 1px solid #1e293b;
        font-size: 0.85rem;
        color: #cbd5e1;
    }
    .sebep-item:last-child { border-bottom: none; }
    .sebep-icon { width: 20px; text-align: center; }
    .sebep-detail { flex: 1; }
    .sebep-numbers { color: #94a3b8; font-size: 0.8rem; margin-top: 4px; }
    
    .negative { color: #f87171; }
    .positive { color: #4ade80; }
    .neutral { color: #94a3b8; }
    
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #334155, transparent);
        margin: 24px 0;
    }
    
    .section-title {
        color: #e2e8f0;
        font-size: 1.1rem;
        font-weight: 600;
        margin: 24px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #334155;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# === YARDIMCI FONKSİYONLAR ===

def extract_code(magaza):
    if pd.isna(magaza):
        return None
    return str(magaza).split()[0]

def format_currency(value):
    if pd.isna(value) or value == 0:
        return "-"
    if abs(value) >= 1000000:
        return f"{value/1000000:.2f}M"
    elif abs(value) >= 1000:
        return f"{value/1000:.0f}K"
    return f"{value:,.0f}"

def format_pct(value, show_sign=True):
    if pd.isna(value):
        return "-"
    if show_sign:
        return f"{value:+.1f}%" if value != 0 else "0%"
    return f"{value:.1f}%"

def safe_div(a, b, default=0):
    if b == 0 or pd.isna(b) or pd.isna(a):
        return default
    return a / b * 100

# === VERİ İŞLEME ===

@st.cache_data
def load_and_process(uploaded_file):
    """Veriyi yükle ve 3 aylık karşılaştırma yap"""
    
    df = pd.read_excel(uploaded_file, sheet_name='EBITDA', header=1)
    df = df[df['Kar / Zarar'] != 'GENEL'].copy()
    
    # Dönemleri sırala
    ay_map = {'Ocak': 1, 'Şubat': 2, 'Mart': 3, 'Nisan': 4, 'Mayıs': 5, 'Haziran': 6,
              'Temmuz': 7, 'Ağustos': 8, 'Eylül': 9, 'Ekim': 10, 'Kasım': 11, 'Aralık': 12}
    
    donemler = df['Mali yıl/dönem - Orta uzunl.metin'].dropna().unique()
    donemler = sorted(donemler, key=lambda d: ay_map.get(d.split()[0], 0))[-3:]  # Son 3 ay
    
    if len(donemler) < 2:
        return None, None, "En az 2 dönem verisi gerekli"
    
    # Dönem verilerini ayır
    donem_data = {}
    for d in donemler:
        temp = df[df['Mali yıl/dönem - Orta uzunl.metin'] == d].copy()
        temp['Kod'] = temp['Mağaza'].apply(extract_code)
        donem_data[d] = temp.set_index('Kod')
    
    # Son dönemde Net Satış > 0 olanlar
    son_donem = donemler[-1]
    son_df = donem_data[son_donem]
    son_df['_NetSatis'] = pd.to_numeric(son_df['Net Satış (KDV Hariç)'], errors='coerce').fillna(0)
    valid_codes = set(son_df[son_df['_NetSatis'] > 0].index)
    
    # Tüm dönemlerde ortak
    for d in donemler[:-1]:
        valid_codes = valid_codes & set(donem_data[d].index)
    
    # Analiz için sütunlar
    metric_cols = {
        'NetSatis': 'Net Satış (KDV Hariç)',
        'SMM': 'SMM',
        'Iade': 'Satış İade ve İskontoları',
        'Envanter': 'Envanter Kaybı Mağaza',
        'NetMarj': 'Net Marj',
        'Personel': 'Personel Giderleri',
        'Kira': 'Mağaza Kira Giderleri',
        'Elektrik': 'Su\\Elektrik\\Telefon Giderleri ',
        'ToplamGider': 'Toplam Mağaza Giderleri',
        'EBITDA': 'Mağaza Kar/Zararı'
    }
    
    results = []
    
    for kod in valid_codes:
        row = {'Kod': kod}
        
        # Son dönemden sabit bilgiler
        son = son_df.loc[kod]
        if isinstance(son, pd.DataFrame):
            son = son.iloc[0]
        
        row['Magaza'] = str(son['Mağaza'])
        row['SM'] = str(son['Satış Müdürü - Metin']) if pd.notna(son['Satış Müdürü - Metin']) else ''
        row['BS'] = str(son['Bölge Sorumlusu - Metin']) if pd.notna(son['Bölge Sorumlusu - Metin']) else ''
        
        # Her dönem için metrikleri al
        for i, d in enumerate(donemler):
            prefix = f'D{i+1}_'
            data = donem_data[d]
            
            if kod in data.index:
                r = data.loc[kod]
                if isinstance(r, pd.DataFrame):
                    r = r.iloc[0]
                
                for key, col in metric_cols.items():
                    val = pd.to_numeric(r.get(col, 0), errors='coerce') or 0
                    row[f'{prefix}{key}'] = val
                
                # Oranları hesapla
                net_satis = row[f'{prefix}NetSatis']
                if net_satis > 0:
                    row[f'{prefix}EBITDA_Oran'] = row[f'{prefix}EBITDA'] / net_satis * 100
                    row[f'{prefix}SMM_Oran'] = abs(row[f'{prefix}SMM']) / net_satis * 100
                    row[f'{prefix}Iade_Oran'] = abs(row[f'{prefix}Iade']) / net_satis * 100
                    row[f'{prefix}Envanter_Oran'] = abs(row[f'{prefix}Envanter']) / net_satis * 100
                    row[f'{prefix}Personel_Oran'] = row[f'{prefix}Personel'] / net_satis * 100
                    row[f'{prefix}Kira_Oran'] = row[f'{prefix}Kira'] / net_satis * 100
                    row[f'{prefix}Elektrik_Oran'] = row[f'{prefix}Elektrik'] / net_satis * 100
                    row[f'{prefix}ToplamGider_Oran'] = row[f'{prefix}ToplamGider'] / net_satis * 100
                else:
                    for suffix in ['EBITDA_Oran', 'SMM_Oran', 'Iade_Oran', 'Envanter_Oran', 
                                   'Personel_Oran', 'Kira_Oran', 'Elektrik_Oran', 'ToplamGider_Oran']:
                        row[f'{prefix}{suffix}'] = 0
        
        results.append(row)
    
    result_df = pd.DataFrame(results)
    n = len(donemler)
    
    # Değişimleri hesapla
    if n >= 2:
        result_df['D1_D2_NetSatis_Pct'] = ((result_df['D2_NetSatis'] - result_df['D1_NetSatis']) / result_df['D1_NetSatis'].replace(0, np.nan) * 100).fillna(0)
        result_df['D1_D2_EBITDA_Pct'] = ((result_df['D2_EBITDA'] - result_df['D1_EBITDA']) / result_df['D1_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
        result_df['D1_D2_Oran_Degisim'] = result_df['D2_EBITDA_Oran'] - result_df['D1_EBITDA_Oran']
    
    if n >= 3:
        result_df['D2_D3_NetSatis_Pct'] = ((result_df['D3_NetSatis'] - result_df['D2_NetSatis']) / result_df['D2_NetSatis'].replace(0, np.nan) * 100).fillna(0)
        result_df['D2_D3_EBITDA_Pct'] = ((result_df['D3_EBITDA'] - result_df['D2_EBITDA']) / result_df['D2_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
        result_df['D2_D3_Oran_Degisim'] = result_df['D3_EBITDA_Oran'] - result_df['D2_EBITDA_Oran']
    
    # Acil ve Yangın tanımları
    if n >= 3:
        result_df['Yangin'] = (result_df['D2_EBITDA'] < 0) & (result_df['D3_EBITDA'] < 0)
        result_df['Acil'] = (result_df['D3_EBITDA'] < 0) & (
            (result_df['D2_D3_EBITDA_Pct'] < 0) | (result_df['D1_D2_EBITDA_Pct'] < 0)
        )
    else:
        result_df['Yangin'] = (result_df['D1_EBITDA'] < 0) & (result_df['D2_EBITDA'] < 0)
        result_df['Acil'] = (result_df['D2_EBITDA'] < 0) & (result_df['D1_D2_EBITDA_Pct'] < 0)
    
    return result_df, {'donemler': donemler, 'n': n}, None


def generate_detailed_sebep(row, donem_info):
    """Detaylı sebep analizi üret - prompt'a uygun"""
    
    n = donem_info['n']
    donemler = donem_info['donemler']
    
    sebepler = []
    
    if n >= 3:
        d1, d2 = 'D2_', 'D3_'
        d1_name, d2_name = donemler[1], donemler[2]
    else:
        d1, d2 = 'D1_', 'D2_'
        d1_name, d2_name = donemler[0], donemler[1]
    
    # === EBITDA ORAN DEĞİŞİMİ (EN ÖNEMLİ) ===
    oran1 = row.get(f'{d1}EBITDA_Oran', 0)
    oran2 = row.get(f'{d2}EBITDA_Oran', 0)
    oran_degisim = oran2 - oran1
    
    if oran_degisim < -2:
        sebepler.append({
            'icon': '📊',
            'type': 'critical',
            'title': 'EBITDA Oranı DÜŞTÜ',
            'detail': f'%{oran1:.1f} → %{oran2:.1f} ({oran_degisim:+.1f} puan)',
            'numbers': f'{d1_name}: %{oran1:.1f} | {d2_name}: %{oran2:.1f}'
        })
    
    # === CİRO DEĞİŞİMİ ===
    ciro1 = row.get(f'{d1}NetSatis', 0)
    ciro2 = row.get(f'{d2}NetSatis', 0)
    ciro_pct = ((ciro2 - ciro1) / ciro1 * 100) if ciro1 > 0 else 0
    
    if ciro_pct < -10:
        sebepler.append({
            'icon': '📉',
            'type': 'warning',
            'title': 'Net Satış DÜŞTÜ',
            'detail': f'{format_currency(ciro1)}₺ → {format_currency(ciro2)}₺ ({ciro_pct:+.1f}%)',
            'numbers': f'Düşüş: {format_currency(ciro1 - ciro2)}₺'
        })
    
    # === SMM DEĞİŞİMİ ===
    smm_oran1 = row.get(f'{d1}SMM_Oran', 0)
    smm_oran2 = row.get(f'{d2}SMM_Oran', 0)
    smm_degisim = smm_oran2 - smm_oran1
    
    if smm_degisim > 1:
        sebepler.append({
            'icon': '🏭',
            'type': 'warning',
            'title': 'SMM Oranı ARTTI',
            'detail': f'%{smm_oran1:.1f} → %{smm_oran2:.1f} ({smm_degisim:+.1f} puan)',
            'numbers': f'Maliyet oranı yükseldi'
        })
    
    # === İADE DEĞİŞİMİ ===
    iade_oran1 = row.get(f'{d1}Iade_Oran', 0)
    iade_oran2 = row.get(f'{d2}Iade_Oran', 0)
    iade_degisim = iade_oran2 - iade_oran1
    
    if iade_degisim > 0.5:
        sebepler.append({
            'icon': '↩️',
            'type': 'warning',
            'title': 'İade Oranı ARTTI',
            'detail': f'%{iade_oran1:.2f} → %{iade_oran2:.2f} ({iade_degisim:+.2f} puan)',
            'numbers': ''
        })
    
    # === ENVANTER KAYBI ===
    env_oran1 = row.get(f'{d1}Envanter_Oran', 0)
    env_oran2 = row.get(f'{d2}Envanter_Oran', 0)
    env_degisim = env_oran2 - env_oran1
    
    if env_degisim > 0.3:
        sebepler.append({
            'icon': '📦',
            'type': 'warning',
            'title': 'Envanter Kaybı ARTTI',
            'detail': f'%{env_oran1:.2f} → %{env_oran2:.2f} ({env_degisim:+.2f} puan)',
            'numbers': ''
        })
    
    # === GİDER KALEMLERİ ===
    gider_kalemleri = [
        ('Personel', 'Personel Gideri'),
        ('Kira', 'Kira Gideri'),
        ('Elektrik', 'Su/Elektrik/Tel')
    ]
    
    for key, name in gider_kalemleri:
        tl1 = row.get(f'{d1}{key}', 0)
        tl2 = row.get(f'{d2}{key}', 0)
        oran1 = row.get(f'{d1}{key}_Oran', 0)
        oran2 = row.get(f'{d2}{key}_Oran', 0)
        
        tl_degisim = tl2 - tl1
        oran_degisim = oran2 - oran1
        
        if oran_degisim > 1:  # Oran 1 puandan fazla arttıysa
            if tl_degisim > 5000:  # TL de arttı
                sebepler.append({
                    'icon': '⚠️',
                    'type': 'warning',
                    'title': f'{name}: TL ARTTI',
                    'detail': f'{format_currency(tl1)}₺ → {format_currency(tl2)}₺ (TL arttı)',
                    'numbers': f'Oran: %{oran1:.1f} → %{oran2:.1f} ({oran_degisim:+.1f} puan)'
                })
            elif abs(tl_degisim) < 5000:  # TL sabit, ciro düştü
                sebepler.append({
                    'icon': '⚠️',
                    'type': 'info',
                    'title': f'{name}: CİRO DÜŞÜNCE ORAN ARTTI',
                    'detail': f'TL sabit ({format_currency(tl2)}₺), ciro düşünce oran yükseldi',
                    'numbers': f'Oran: %{oran1:.1f} → %{oran2:.1f} ({oran_degisim:+.1f} puan)'
                })
    
    if not sebepler:
        sebepler.append({
            'icon': '✓',
            'type': 'neutral',
            'title': 'Belirgin bozulma tespit edilemedi',
            'detail': '',
            'numbers': ''
        })
    
    return sebepler


# === ANA UYGULAMA ===

def main():
    # Başlık
    st.markdown('<p class="main-title">🎯 EBITDA Karar Motoru</p>', unsafe_allow_html=True)
    
    # Session state - dosya kalıcılığı
    if 'data' not in st.session_state:
        st.session_state.data = None
        st.session_state.donem_info = None
    
    # Dosya yükleme (sadece ilk seferde veya yenileme için)
    col1, col2 = st.columns([4, 1])
    with col2:
        uploaded_file = st.file_uploader("", type=['xlsx'], label_visibility="collapsed", key="file_uploader")
    
    # Yeni dosya yüklendiyse işle
    if uploaded_file is not None:
        with st.spinner("Veri işleniyor..."):
            result_df, donem_info, error = load_and_process(uploaded_file)
        
        if error:
            st.error(error)
            return
        
        st.session_state.data = result_df
        st.session_state.donem_info = donem_info
        st.success(f"✓ {len(result_df)} mağaza yüklendi")
    
    # Veri yoksa uyarı göster
    if st.session_state.data is None:
        st.markdown("""
        <div style="background:#1e293b;border-left:3px solid #f59e0b;padding:20px;border-radius:0 8px 8px 0;margin-top:20px">
            <strong style="color:#f59e0b;font-size:1.1rem">📁 EBITDA dosyasını yükleyin</strong><br><br>
            <span style="color:#94a3b8">
            • Dosya bir kez yüklenir, oturumda kalır<br>
            • Her ay yeni rapor geldiğinde güncelleyin<br>
            • En az 2 dönem verisi gerekli
            </span>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Veriyi al
    df = st.session_state.data
    donem_info = st.session_state.donem_info
    donemler = donem_info['donemler']
    n = donem_info['n']
    
    st.markdown(f'<p class="sub-title">{" → ".join(donemler)} | {len(df)} mağaza</p>', unsafe_allow_html=True)
    
    # === GENEL METRİKLER ===
    son = f'D{n}_'
    onceki = f'D{n-1}_' if n > 1 else son
    
    toplam_ebitda = df[f'{son}EBITDA'].sum()
    toplam_satis = df[f'{son}NetSatis'].sum()
    genel_oran = (toplam_ebitda / toplam_satis * 100) if toplam_satis > 0 else 0
    
    onceki_ebitda = df[f'{onceki}EBITDA'].sum()
    onceki_satis = df[f'{onceki}NetSatis'].sum()
    onceki_oran = (onceki_ebitda / onceki_satis * 100) if onceki_satis > 0 else 0
    
    oran_degisim = genel_oran - onceki_oran
    ebitda_degisim = toplam_ebitda - onceki_ebitda
    
    acil_count = df['Acil'].sum()
    yangin_count = df['Yangin'].sum()
    
    # KPI Kartları
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-box">
            <p class="kpi-label">💰 {donemler[-1]} EBITDA</p>
            <p class="kpi-value">{format_currency(toplam_ebitda)}₺</p>
            <p class="kpi-delta {'negative' if ebitda_degisim < 0 else 'positive'}">{format_currency(ebitda_degisim)}₺</p>
        </div>
        <div class="kpi-box">
            <p class="kpi-label">📊 EBITDA Oranı</p>
            <p class="kpi-value">%{genel_oran:.2f}</p>
            <p class="kpi-delta {'negative' if oran_degisim < 0 else 'positive'}">{oran_degisim:+.2f} puan</p>
        </div>
        <div class="kpi-box-alert" onclick="document.getElementById('acil_section').scrollIntoView()">
            <p class="kpi-label">🚨 Acil Müdahale</p>
            <p class="kpi-value">{int(acil_count)}</p>
            <p class="kpi-delta neutral">tıkla → liste</p>
        </div>
        <div class="kpi-box-warning">
            <p class="kpi-label">🔥 Yangın</p>
            <p class="kpi-value">{int(yangin_count)}</p>
            <p class="kpi-delta neutral">üst üste negatif</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # === SM PERFORMANS TABLOSU ===
    st.markdown('<p class="section-title">👥 SM Performans (Zaman Serisi)</p>', unsafe_allow_html=True)
    
    # SM grupla
    sm_agg = {f'D{i}_EBITDA': 'sum' for i in range(1, n+1)}
    sm_agg.update({f'D{i}_NetSatis': 'sum' for i in range(1, n+1)})
    sm_agg['Kod'] = 'count'
    sm_agg['Acil'] = 'sum'
    sm_agg['Yangin'] = 'sum'
    
    sm_df = df.groupby('SM').agg(sm_agg).reset_index()
    sm_df = sm_df[sm_df['Kod'] > 2]
    
    # Oranları hesapla
    for i in range(1, n+1):
        sm_df[f'D{i}_Oran'] = (sm_df[f'D{i}_EBITDA'] / sm_df[f'D{i}_NetSatis'] * 100).fillna(0)
    
    # Değişimleri hesapla
    if n >= 2:
        sm_df['D1_D2_Pct'] = ((sm_df['D2_EBITDA'] - sm_df['D1_EBITDA']) / sm_df['D1_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
    if n >= 3:
        sm_df['D2_D3_Pct'] = ((sm_df['D3_EBITDA'] - sm_df['D2_EBITDA']) / sm_df['D2_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
    
    sm_df = sm_df.sort_values(f'D{n}_EBITDA', ascending=False)
    
    # Tablo HTML
    if n == 3:
        table_html = f"""
        <table class="time-table">
            <thead>
                <tr>
                    <th style="text-align:left">SM</th>
                    <th>{donemler[0]}</th>
                    <th>{donemler[1]}</th>
                    <th>Δ%</th>
                    <th>{donemler[2]}</th>
                    <th>Δ%</th>
                    <th>Durum</th>
                </tr>
            </thead>
            <tbody>
        """
        for _, r in sm_df.iterrows():
            sm_name = r['SM'].split()[0] if pd.notna(r['SM']) else 'N/A'
            d1_d2_class = 'negative' if r.get('D1_D2_Pct', 0) < 0 else 'positive'
            d2_d3_class = 'negative' if r.get('D2_D3_Pct', 0) < 0 else 'positive'
            
            durum = ''
            if r['Acil'] > 0:
                durum += f'<span style="background:#7f1d1d;color:#fca5a5;padding:2px 8px;border-radius:10px;font-size:0.75rem">{int(r["Acil"])} acil</span> '
            if r['Yangin'] > 0:
                durum += f'<span style="background:#78350f;color:#fcd34d;padding:2px 8px;border-radius:10px;font-size:0.75rem">{int(r["Yangin"])} 🔥</span>'
            
            table_html += f"""
                <tr>
                    <td><strong>{sm_name}</strong> <span style="color:#64748b;font-size:0.8rem">({int(r['Kod'])})</span></td>
                    <td>{format_currency(r['D1_EBITDA'])}₺<br><span style="color:#64748b;font-size:0.75rem">%{r['D1_Oran']:.1f}</span></td>
                    <td>{format_currency(r['D2_EBITDA'])}₺<br><span style="color:#64748b;font-size:0.75rem">%{r['D2_Oran']:.1f}</span></td>
                    <td class="{d1_d2_class}">{r.get('D1_D2_Pct', 0):+.1f}%</td>
                    <td>{format_currency(r['D3_EBITDA'])}₺<br><span style="color:#64748b;font-size:0.75rem">%{r['D3_Oran']:.1f}</span></td>
                    <td class="{d2_d3_class}">{r.get('D2_D3_Pct', 0):+.1f}%</td>
                    <td>{durum}</td>
                </tr>
            """
        table_html += "</tbody></table>"
    else:
        table_html = f"""
        <table class="time-table">
            <thead>
                <tr>
                    <th style="text-align:left">SM</th>
                    <th>{donemler[0]}</th>
                    <th>{donemler[1]}</th>
                    <th>Δ%</th>
                    <th>Durum</th>
                </tr>
            </thead>
            <tbody>
        """
        for _, r in sm_df.iterrows():
            sm_name = r['SM'].split()[0] if pd.notna(r['SM']) else 'N/A'
            d1_d2_class = 'negative' if r.get('D1_D2_Pct', 0) < 0 else 'positive'
            
            durum = ''
            if r['Acil'] > 0:
                durum += f'<span style="background:#7f1d1d;color:#fca5a5;padding:2px 8px;border-radius:10px;font-size:0.75rem">{int(r["Acil"])} acil</span> '
            
            table_html += f"""
                <tr>
                    <td><strong>{sm_name}</strong> <span style="color:#64748b;font-size:0.8rem">({int(r['Kod'])})</span></td>
                    <td>{format_currency(r['D1_EBITDA'])}₺<br><span style="color:#64748b;font-size:0.75rem">%{r['D1_Oran']:.1f}</span></td>
                    <td>{format_currency(r['D2_EBITDA'])}₺<br><span style="color:#64748b;font-size:0.75rem">%{r['D2_Oran']:.1f}</span></td>
                    <td class="{d1_d2_class}">{r.get('D1_D2_Pct', 0):+.1f}%</td>
                    <td>{durum}</td>
                </tr>
            """
        table_html += "</tbody></table>"
    
    st.markdown(table_html, unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # === ACİL VE YANGIN SEKMELERI ===
    
    tab1, tab2 = st.tabs([f"🚨 Acil Müdahale ({int(acil_count)})", f"🔥 Yangın ({int(yangin_count)})"])
    
    with tab1:
        st.markdown('<p id="acil_section"></p>', unsafe_allow_html=True)
        
        if acil_count > 0:
            acil_df = df[df['Acil']].sort_values(f'D{n}_EBITDA')
            
            # SM bazında grupla
            for sm in acil_df['SM'].unique():
                sm_name = sm.split()[0] if pd.notna(sm) else 'N/A'
                sm_magazalar = acil_df[acil_df['SM'] == sm]
                
                with st.expander(f"📁 {sm_name} ({len(sm_magazalar)} mağaza)", expanded=True):
                    for _, row in sm_magazalar.iterrows():
                        # Zaman serisi
                        if n == 3:
                            ts_html = f"""
                            <div class="time-series">
                                <div class="time-item">
                                    <div class="time-item-label">{donemler[0]}</div>
                                    <div class="time-item-value">{format_currency(row['D1_EBITDA'])}₺</div>
                                    <div class="time-item-delta neutral">%{row['D1_EBITDA_Oran']:.1f}</div>
                                </div>
                                <div class="time-item">
                                    <div class="time-item-label">→</div>
                                    <div class="time-item-value {'negative' if row.get('D1_D2_EBITDA_Pct', 0) < 0 else 'positive'}">{row.get('D1_D2_EBITDA_Pct', 0):+.1f}%</div>
                                </div>
                                <div class="time-item">
                                    <div class="time-item-label">{donemler[1]}</div>
                                    <div class="time-item-value">{format_currency(row['D2_EBITDA'])}₺</div>
                                    <div class="time-item-delta neutral">%{row['D2_EBITDA_Oran']:.1f}</div>
                                </div>
                                <div class="time-item">
                                    <div class="time-item-label">→</div>
                                    <div class="time-item-value {'negative' if row.get('D2_D3_EBITDA_Pct', 0) < 0 else 'positive'}">{row.get('D2_D3_EBITDA_Pct', 0):+.1f}%</div>
                                </div>
                                <div class="time-item">
                                    <div class="time-item-label">{donemler[2]}</div>
                                    <div class="time-item-value negative">{format_currency(row['D3_EBITDA'])}₺</div>
                                    <div class="time-item-delta negative">%{row['D3_EBITDA_Oran']:.1f}</div>
                                </div>
                            </div>
                            """
                        else:
                            ts_html = f"""
                            <div class="time-series" style="grid-template-columns: repeat(3, 1fr);">
                                <div class="time-item">
                                    <div class="time-item-label">{donemler[0]}</div>
                                    <div class="time-item-value">{format_currency(row['D1_EBITDA'])}₺</div>
                                    <div class="time-item-delta neutral">%{row['D1_EBITDA_Oran']:.1f}</div>
                                </div>
                                <div class="time-item">
                                    <div class="time-item-label">→</div>
                                    <div class="time-item-value {'negative' if row.get('D1_D2_EBITDA_Pct', 0) < 0 else 'positive'}">{row.get('D1_D2_EBITDA_Pct', 0):+.1f}%</div>
                                </div>
                                <div class="time-item">
                                    <div class="time-item-label">{donemler[1]}</div>
                                    <div class="time-item-value negative">{format_currency(row['D2_EBITDA'])}₺</div>
                                    <div class="time-item-delta negative">%{row['D2_EBITDA_Oran']:.1f}</div>
                                </div>
                            </div>
                            """
                        
                        # Sebep analizi
                        sebepler = generate_detailed_sebep(row, donem_info)
                        sebep_html = '<div class="sebep-box"><div class="sebep-title">📋 NEDEN?</div>'
                        for s in sebepler:
                            sebep_html += f"""
                            <div class="sebep-item">
                                <div class="sebep-icon">{s['icon']}</div>
                                <div class="sebep-detail">
                                    <strong>{s['title']}</strong><br>
                                    {s['detail']}
                                    {'<div class="sebep-numbers">' + s['numbers'] + '</div>' if s['numbers'] else ''}
                                </div>
                            </div>
                            """
                        sebep_html += '</div>'
                        
                        st.markdown(f"""
                        <div class="magaza-card magaza-card-alert">
                            <div class="magaza-header">
                                <div>
                                    <span class="magaza-kod">{row['Kod']}</span>
                                    <span class="magaza-isim">{row['Magaza'][:40]}</span>
                                </div>
                            </div>
                            {ts_html}
                            {sebep_html}
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.success("✅ Acil müdahale gerektiren mağaza yok")
    
    with tab2:
        if yangin_count > 0:
            st.markdown("""
            <div style="background:#7f1d1d;border:1px solid #dc2626;border-radius:8px;padding:12px;margin-bottom:16px">
                <strong style="color:#fca5a5">⚠️ Bu mağazalara ÖNCE gidilmeli - Üst üste 2 ay negatif EBITDA</strong>
            </div>
            """, unsafe_allow_html=True)
            
            yangin_df = df[df['Yangin']].sort_values(f'D{n}_EBITDA')
            
            for sm in yangin_df['SM'].unique():
                sm_name = sm.split()[0] if pd.notna(sm) else 'N/A'
                sm_magazalar = yangin_df[yangin_df['SM'] == sm]
                
                with st.expander(f"🔥 {sm_name} ({len(sm_magazalar)} mağaza)", expanded=True):
                    for _, row in sm_magazalar.iterrows():
                        # Basit zaman serisi
                        if n == 3:
                            ts_str = f"{donemler[0]}: {format_currency(row['D1_EBITDA'])}₺ → {donemler[1]}: {format_currency(row['D2_EBITDA'])}₺ → {donemler[2]}: {format_currency(row['D3_EBITDA'])}₺"
                        else:
                            ts_str = f"{donemler[0]}: {format_currency(row['D1_EBITDA'])}₺ → {donemler[1]}: {format_currency(row['D2_EBITDA'])}₺"
                        
                        sebepler = generate_detailed_sebep(row, donem_info)
                        sebep_html = '<div class="sebep-box"><div class="sebep-title">📋 NEDEN?</div>'
                        for s in sebepler:
                            sebep_html += f"""
                            <div class="sebep-item">
                                <div class="sebep-icon">{s['icon']}</div>
                                <div class="sebep-detail">
                                    <strong>{s['title']}</strong><br>
                                    {s['detail']}
                                </div>
                            </div>
                            """
                        sebep_html += '</div>'
                        
                        st.markdown(f"""
                        <div class="magaza-card magaza-card-warning">
                            <div class="magaza-header">
                                <div>
                                    <span style="color:#f97316;margin-right:8px">🔥</span>
                                    <span class="magaza-kod">{row['Kod']}</span>
                                    <span class="magaza-isim">{row['Magaza'][:40]}</span>
                                </div>
                            </div>
                            <div style="color:#94a3b8;font-size:0.9rem;margin:12px 0">{ts_str}</div>
                            {sebep_html}
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.success("✅ Yangın durumunda mağaza yok")
    
    # === EXPORT ===
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='TÜM VERİ', index=False)
            if acil_count > 0:
                df[df['Acil']].to_excel(writer, sheet_name='ACİL', index=False)
            if yangin_count > 0:
                df[df['Yangin']].to_excel(writer, sheet_name='YANGIN', index=False)
            sm_df.to_excel(writer, sheet_name='SM ÖZET', index=False)
        
        st.download_button(
            "📥 Excel İndir",
            data=output.getvalue(),
            file_name=f"EBITDA_Karar_{donemler[-1].replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # Footer
    st.markdown(f"""
    <div style="text-align:center;margin-top:32px;color:#475569;font-size:0.8rem">
        🎯 EBITDA Karar Motoru | {' → '.join(donemler)} | A101 Antalya Bölgesi
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
