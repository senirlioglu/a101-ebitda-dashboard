import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(
    page_title="EBITDA Karar Motoru",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Minimal dark theme - karar odaklı
st.markdown("""
<style>
    .stApp { background: #0f172a; }
    
    .main-title {
        color: #f59e0b;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0;
    }
    
    .sub-title {
        color: #64748b;
        font-size: 0.9rem;
    }
    
    .kpi-box {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    
    .kpi-box-alert {
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
        border: 1px solid #dc2626;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        cursor: pointer;
    }
    
    .kpi-box-warning {
        background: linear-gradient(135deg, #78350f 0%, #92400e 100%);
        border: 1px solid #f59e0b;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        cursor: pointer;
    }
    
    .kpi-label {
        color: #94a3b8;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .kpi-value {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        margin: 4px 0;
    }
    
    .kpi-delta {
        font-size: 0.85rem;
    }
    
    .negative { color: #f87171; }
    .positive { color: #4ade80; }
    .neutral { color: #94a3b8; }
    
    .section-title {
        color: #e2e8f0;
        font-size: 1.1rem;
        font-weight: 600;
        margin: 24px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #334155;
    }
    
    .sm-row {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    
    .magaza-card {
        background: #1e293b;
        border-left: 3px solid #f59e0b;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 8px 0;
    }
    
    .magaza-card-alert {
        background: #1e293b;
        border-left: 3px solid #ef4444;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 8px 0;
    }
    
    .sebep-box {
        background: #0f172a;
        border: 1px solid #475569;
        border-radius: 8px;
        padding: 12px;
        margin-top: 8px;
        font-size: 0.85rem;
        color: #cbd5e1;
    }
    
    .time-header {
        display: grid;
        grid-template-columns: 2fr 1fr 1fr 0.5fr 1fr 0.5fr;
        gap: 8px;
        padding: 8px 12px;
        background: #0f172a;
        border-radius: 8px;
        font-size: 0.7rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    
    .time-row {
        display: grid;
        grid-template-columns: 2fr 1fr 1fr 0.5fr 1fr 0.5fr;
        gap: 8px;
        padding: 10px 12px;
        background: #1e293b;
        border-radius: 8px;
        margin-bottom: 4px;
        font-size: 0.9rem;
        color: #e2e8f0;
    }
    
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #334155, transparent);
        margin: 24px 0;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# === VERİ İŞLEME FONKSİYONLARI ===

def extract_code(magaza):
    if pd.isna(magaza):
        return None
    return str(magaza).split()[0]

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name='EBITDA', header=1)
    df = df[df['Kar / Zarar'] != 'GENEL'].copy()
    return df

def process_data(df):
    """3 aylık veriyi işle ve karar motoru için hazırla"""
    
    # Dönemleri sırala
    ay_map = {'Ocak': 1, 'Şubat': 2, 'Mart': 3, 'Nisan': 4, 'Mayıs': 5, 'Haziran': 6,
              'Temmuz': 7, 'Ağustos': 8, 'Eylül': 9, 'Ekim': 10, 'Kasım': 11, 'Aralık': 12}
    
    donemler = df['Mali yıl/dönem - Orta uzunl.metin'].dropna().unique()
    
    def parse_donem(d):
        try:
            parts = d.split()
            return ay_map.get(parts[0], 0)
        except:
            return 0
    
    donemler = sorted(donemler, key=parse_donem)
    
    if len(donemler) < 2:
        return None, None, "En az 2 dönem verisi gerekli"
    
    # Son 3 ayı al (veya mevcut kadarını)
    donemler = donemler[-3:] if len(donemler) >= 3 else donemler
    
    # Her dönem için veri ayır
    donem_data = {}
    for d in donemler:
        temp = df[df['Mali yıl/dönem - Orta uzunl.metin'] == d].copy()
        temp['Kod'] = temp['Mağaza'].apply(extract_code)
        donem_data[d] = temp.set_index('Kod')
    
    # Ortak mağazalar (son ayda satışı olanlar)
    son_donem = donemler[-1]
    son_df = donem_data[son_donem]
    
    # Son ay Net Satış'ı olmayanları çıkar
    son_df = son_df[pd.to_numeric(son_df['Net Satış (KDV Hariç)'], errors='coerce').fillna(0) > 0]
    valid_codes = set(son_df.index)
    
    # Tüm dönemlerde ortak olanlar
    for d in donemler[:-1]:
        valid_codes = valid_codes & set(donem_data[d].index)
    
    # Sonuç DataFrame oluştur
    results = []
    
    gider_kalemleri = {
        'Personel': 'Personel Giderleri',
        'Kira': 'Mağaza Kira Giderleri',
        'Elektrik_Su_Tel': 'Su\\Elektrik\\Telefon Giderleri ',
        'Diger': 'Diğer Giderler'
    }
    
    for kod in valid_codes:
        row = {'Kod': kod}
        
        # Son dönemden sabit bilgiler
        son = son_df.loc[kod]
        if isinstance(son, pd.DataFrame):
            son = son.iloc[0]
        
        row['Mağaza'] = str(son['Mağaza'])
        row['SM'] = str(son['Satış Müdürü - Metin']) if pd.notna(son['Satış Müdürü - Metin']) else ''
        row['BS'] = str(son['Bölge Sorumlusu - Metin']) if pd.notna(son['Bölge Sorumlusu - Metin']) else ''
        
        # Her dönem için metrikleri al
        for i, d in enumerate(donemler):
            prefix = f"D{i+1}_"  # D1_, D2_, D3_
            
            data = donem_data[d]
            if kod in data.index:
                r = data.loc[kod]
                if isinstance(r, pd.DataFrame):
                    r = r.iloc[0]
                
                net_satis = pd.to_numeric(r['Net Satış (KDV Hariç)'], errors='coerce') or 0
                toplam_gider = pd.to_numeric(r['Toplam Mağaza Giderleri'], errors='coerce') or 0
                ebitda = pd.to_numeric(r['Mağaza Kar/Zararı'], errors='coerce') or 0
                
                row[f'{prefix}NetSatis'] = net_satis
                row[f'{prefix}ToplamGider'] = toplam_gider
                row[f'{prefix}EBITDA'] = ebitda
                row[f'{prefix}EBITDA_Oran'] = (ebitda / net_satis * 100) if net_satis > 0 else 0
                
                # Gider kalemleri
                for key, col in gider_kalemleri.items():
                    if col in r.index:
                        val = pd.to_numeric(r[col], errors='coerce') or 0
                        row[f'{prefix}{key}_TL'] = val
                        row[f'{prefix}{key}_Oran'] = (val / net_satis * 100) if net_satis > 0 else 0
            else:
                row[f'{prefix}NetSatis'] = 0
                row[f'{prefix}ToplamGider'] = 0
                row[f'{prefix}EBITDA'] = 0
                row[f'{prefix}EBITDA_Oran'] = 0
        
        results.append(row)
    
    result_df = pd.DataFrame(results)
    
    # Değişim hesapla
    n = len(donemler)
    
    if n >= 2:
        # D1 → D2 değişim
        result_df['D1_D2_EBITDA_Degisim'] = result_df['D2_EBITDA'] - result_df['D1_EBITDA']
        result_df['D1_D2_Oran_Degisim'] = result_df['D2_EBITDA_Oran'] - result_df['D1_EBITDA_Oran']
        result_df['D1_D2_Satis_Degisim_Pct'] = ((result_df['D2_NetSatis'] - result_df['D1_NetSatis']) / result_df['D1_NetSatis'].replace(0, np.nan) * 100).fillna(0)
    
    if n >= 3:
        # D2 → D3 değişim
        result_df['D2_D3_EBITDA_Degisim'] = result_df['D3_EBITDA'] - result_df['D2_EBITDA']
        result_df['D2_D3_Oran_Degisim'] = result_df['D3_EBITDA_Oran'] - result_df['D2_EBITDA_Oran']
        result_df['D2_D3_Satis_Degisim_Pct'] = ((result_df['D3_NetSatis'] - result_df['D2_NetSatis']) / result_df['D2_NetSatis'].replace(0, np.nan) * 100).fillna(0)
    
    # Acil ve Yangın tanımları
    son_ebitda_col = f'D{n}_EBITDA'
    son_oran_col = f'D{n}_EBITDA_Oran'
    
    if n >= 3:
        # Yangın: Üst üste 2 ay negatif
        result_df['Yangin'] = (result_df['D2_EBITDA'] < 0) & (result_df['D3_EBITDA'] < 0)
        
        # Acil: Son ay negatif VE trend kötüleşiyor
        result_df['Acil'] = (
            (result_df['D3_EBITDA'] < 0) & 
            ((result_df['D2_D3_EBITDA_Degisim'] < 0) | (result_df['D1_D2_EBITDA_Degisim'] < 0))
        )
    elif n >= 2:
        result_df['Yangin'] = (result_df['D1_EBITDA'] < 0) & (result_df['D2_EBITDA'] < 0)
        result_df['Acil'] = (result_df['D2_EBITDA'] < 0) & (result_df['D1_D2_EBITDA_Degisim'] < 0)
    
    donem_info = {
        'donemler': donemler,
        'n': n
    }
    
    return result_df, donem_info, None


def generate_sebep_analizi(row, donem_info):
    """Mağaza için detaylı sebep analizi üret"""
    
    n = donem_info['n']
    donemler = donem_info['donemler']
    
    sebepler = []
    
    if n < 2:
        return "Yeterli veri yok"
    
    # Son iki dönem karşılaştır
    if n >= 3:
        onceki_prefix = 'D2_'
        son_prefix = 'D3_'
        onceki_donem = donemler[1]
        son_donem = donemler[2]
    else:
        onceki_prefix = 'D1_'
        son_prefix = 'D2_'
        onceki_donem = donemler[0]
        son_donem = donemler[1]
    
    # Satış değişimi
    onceki_satis = row[f'{onceki_prefix}NetSatis']
    son_satis = row[f'{son_prefix}NetSatis']
    satis_degisim_pct = ((son_satis - onceki_satis) / onceki_satis * 100) if onceki_satis > 0 else 0
    
    if satis_degisim_pct < -10:
        sebepler.append(f"📉 Net Satış %{abs(satis_degisim_pct):.1f} düştü ({onceki_donem}: {onceki_satis:,.0f}₺ → {son_donem}: {son_satis:,.0f}₺)")
    
    # Gider kalemleri analizi
    gider_kalemleri = ['Personel', 'Kira', 'Elektrik_Su_Tel', 'Diger']
    gider_isimleri = {'Personel': 'Personel', 'Kira': 'Kira', 'Elektrik_Su_Tel': 'Su/Elektrik/Tel', 'Diger': 'Diğer'}
    
    for gider in gider_kalemleri:
        onceki_tl = row.get(f'{onceki_prefix}{gider}_TL', 0) or 0
        son_tl = row.get(f'{son_prefix}{gider}_TL', 0) or 0
        onceki_oran = row.get(f'{onceki_prefix}{gider}_Oran', 0) or 0
        son_oran = row.get(f'{son_prefix}{gider}_Oran', 0) or 0
        
        tl_degisim = son_tl - onceki_tl
        oran_degisim = son_oran - onceki_oran
        
        # Oran değişimi kritik mi?
        if oran_degisim > 1:  # 1 puan üzeri artış
            gider_ismi = gider_isimleri[gider]
            
            if tl_degisim > 5000:  # TL de arttı
                sebepler.append(
                    f"⚠️ {gider_ismi}: TL arttı ({onceki_tl:,.0f}→{son_tl:,.0f}) + Oran %{onceki_oran:.1f}→%{son_oran:.1f}"
                )
            elif abs(tl_degisim) < 3000:  # TL sabit, ciro düştü
                sebepler.append(
                    f"⚠️ {gider_ismi}: TL sabit ({son_tl:,.0f}₺), ciro düşünce oran %{onceki_oran:.1f}→%{son_oran:.1f} çıktı"
                )
    
    # EBITDA oran değişimi
    onceki_ebitda_oran = row[f'{onceki_prefix}EBITDA_Oran']
    son_ebitda_oran = row[f'{son_prefix}EBITDA_Oran']
    oran_degisim = son_ebitda_oran - onceki_ebitda_oran
    
    if oran_degisim < -2:
        sebepler.append(f"📊 EBITDA Oranı %{onceki_ebitda_oran:.1f} → %{son_ebitda_oran:.1f} ({oran_degisim:+.1f} puan)")
    
    if not sebepler:
        return "Belirgin bozulma tespit edilemedi"
    
    return "\n".join(sebepler)


def format_currency(value):
    if pd.isna(value) or value == 0:
        return "-"
    if abs(value) >= 1000000:
        return f"{value/1000000:.2f}M"
    elif abs(value) >= 1000:
        return f"{value/1000:.0f}K"
    return f"{value:.0f}"


# === ANA UYGULAMA ===

def main():
    # Header
    st.markdown('<p class="main-title">🎯 EBITDA Karar Motoru</p>', unsafe_allow_html=True)
    
    # File upload
    col1, col2 = st.columns([3, 1])
    with col2:
        uploaded_file = st.file_uploader("", type=['xlsx'], label_visibility="collapsed")
    
    if not uploaded_file:
        st.markdown("""
        <div style="background:#1e293b;border-left:3px solid #f59e0b;padding:16px;border-radius:0 8px 8px 0;margin-top:20px">
            <strong style="color:#f59e0b">📁 EBITDA dosyasını yükleyin</strong><br>
            <span style="color:#94a3b8;font-size:0.9rem">MIS_BW_03_Mağaza_Bazında_EBITDA formatında, en az 2 dönem</span>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Veri yükle
    with st.spinner("Veri işleniyor..."):
        df = load_data(uploaded_file)
        result_df, donem_info, error = process_data(df)
    
    if error:
        st.error(error)
        return
    
    donemler = donem_info['donemler']
    n = donem_info['n']
    
    st.markdown(f'<p class="sub-title">{" → ".join(donemler)} | {len(result_df)} mağaza</p>', unsafe_allow_html=True)
    
    # === KPI KARTLARI ===
    
    # Hesaplamalar
    son_prefix = f'D{n}_'
    toplam_ebitda = result_df[f'{son_prefix}EBITDA'].sum()
    toplam_satis = result_df[f'{son_prefix}NetSatis'].sum()
    genel_oran = (toplam_ebitda / toplam_satis * 100) if toplam_satis > 0 else 0
    
    acil_sayi = result_df['Acil'].sum() if 'Acil' in result_df.columns else 0
    yangin_sayi = result_df['Yangin'].sum() if 'Yangin' in result_df.columns else 0
    
    # Önceki dönemle karşılaştır
    if n >= 2:
        onceki_prefix = f'D{n-1}_'
        onceki_toplam = result_df[f'{onceki_prefix}EBITDA'].sum()
        onceki_satis = result_df[f'{onceki_prefix}NetSatis'].sum()
        onceki_oran = (onceki_toplam / onceki_satis * 100) if onceki_satis > 0 else 0
        ebitda_degisim = toplam_ebitda - onceki_toplam
        oran_degisim = genel_oran - onceki_oran
    else:
        ebitda_degisim = 0
        oran_degisim = 0
    
    # KPI gösterimi
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta_class = "negative" if ebitda_degisim < 0 else "positive"
        st.markdown(f"""
        <div class="kpi-box">
            <p class="kpi-label">💰 {donemler[-1]} EBITDA</p>
            <p class="kpi-value">{format_currency(toplam_ebitda)}₺</p>
            <p class="kpi-delta {delta_class}">{ebitda_degisim:+,.0f}₺</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        delta_class = "negative" if oran_degisim < 0 else "positive"
        st.markdown(f"""
        <div class="kpi-box">
            <p class="kpi-label">📊 EBITDA Oranı</p>
            <p class="kpi-value">%{genel_oran:.2f}</p>
            <p class="kpi-delta {delta_class}">{oran_degisim:+.2f} puan</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="kpi-box-alert">
            <p class="kpi-label">🚨 Acil Müdahale</p>
            <p class="kpi-value">{int(acil_sayi)}</p>
            <p class="kpi-delta neutral">mağaza</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="kpi-box-warning">
            <p class="kpi-label">🔥 Yangın</p>
            <p class="kpi-value">{int(yangin_sayi)}</p>
            <p class="kpi-delta neutral">üst üste negatif</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # === SM PERFORMANS TABLOSU ===
    
    st.markdown('<p class="section-title">👥 SM Performans (Zaman Serisi)</p>', unsafe_allow_html=True)
    
    # SM bazında grupla
    sm_cols = ['SM']
    for i in range(1, n+1):
        sm_cols.extend([f'D{i}_EBITDA', f'D{i}_EBITDA_Oran', f'D{i}_NetSatis'])
    
    sm_df = result_df.groupby('SM').agg({
        **{f'D{i}_EBITDA': 'sum' for i in range(1, n+1)},
        **{f'D{i}_NetSatis': 'sum' for i in range(1, n+1)},
        'Kod': 'count',
        'Acil': 'sum' if 'Acil' in result_df.columns else lambda x: 0,
        'Yangin': 'sum' if 'Yangin' in result_df.columns else lambda x: 0
    }).reset_index()
    
    # Oranları hesapla
    for i in range(1, n+1):
        sm_df[f'D{i}_Oran'] = (sm_df[f'D{i}_EBITDA'] / sm_df[f'D{i}_NetSatis'] * 100).fillna(0)
    
    # Değişimleri hesapla
    if n >= 2:
        sm_df['D1_D2_Pct'] = ((sm_df['D2_EBITDA'] - sm_df['D1_EBITDA']) / sm_df['D1_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
    if n >= 3:
        sm_df['D2_D3_Pct'] = ((sm_df['D3_EBITDA'] - sm_df['D2_EBITDA']) / sm_df['D2_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
    
    sm_df = sm_df[sm_df['Kod'] > 2].sort_values(f'D{n}_EBITDA', ascending=False)
    
    # Tablo header
    if n == 3:
        header_html = f"""
        <div class="time-header">
            <div>SM</div>
            <div style="text-align:right">{donemler[0]}</div>
            <div style="text-align:right">{donemler[1]}</div>
            <div style="text-align:center">%Δ</div>
            <div style="text-align:right">{donemler[2]}</div>
            <div style="text-align:center">%Δ</div>
        </div>
        """
    else:
        header_html = f"""
        <div class="time-header" style="grid-template-columns: 2fr 1fr 1fr 0.5fr;">
            <div>SM</div>
            <div style="text-align:right">{donemler[0]}</div>
            <div style="text-align:right">{donemler[1]}</div>
            <div style="text-align:center">%Δ</div>
        </div>
        """
    
    st.markdown(header_html, unsafe_allow_html=True)
    
    for _, sm_row in sm_df.iterrows():
        sm_name = sm_row['SM'].split()[0] if pd.notna(sm_row['SM']) else 'N/A'
        
        if n == 3:
            d1_d2_class = "negative" if sm_row.get('D1_D2_Pct', 0) < 0 else "positive"
            d2_d3_class = "negative" if sm_row.get('D2_D3_Pct', 0) < 0 else "positive"
            
            row_html = f"""
            <div class="time-row">
                <div><strong>{sm_name}</strong> <span style="color:#64748b;font-size:0.8rem">({int(sm_row['Kod'])} mğz)</span></div>
                <div style="text-align:right">{format_currency(sm_row['D1_EBITDA'])}₺<br><span style="color:#64748b;font-size:0.75rem">%{sm_row['D1_Oran']:.1f}</span></div>
                <div style="text-align:right">{format_currency(sm_row['D2_EBITDA'])}₺<br><span style="color:#64748b;font-size:0.75rem">%{sm_row['D2_Oran']:.1f}</span></div>
                <div style="text-align:center" class="{d1_d2_class}">{sm_row.get('D1_D2_Pct', 0):+.1f}%</div>
                <div style="text-align:right">{format_currency(sm_row['D3_EBITDA'])}₺<br><span style="color:#64748b;font-size:0.75rem">%{sm_row['D3_Oran']:.1f}</span></div>
                <div style="text-align:center" class="{d2_d3_class}">{sm_row.get('D2_D3_Pct', 0):+.1f}%</div>
            </div>
            """
        else:
            d1_d2_class = "negative" if sm_row.get('D1_D2_Pct', 0) < 0 else "positive"
            
            row_html = f"""
            <div class="time-row" style="grid-template-columns: 2fr 1fr 1fr 0.5fr;">
                <div><strong>{sm_name}</strong> <span style="color:#64748b;font-size:0.8rem">({int(sm_row['Kod'])} mğz)</span></div>
                <div style="text-align:right">{format_currency(sm_row['D1_EBITDA'])}₺<br><span style="color:#64748b;font-size:0.75rem">%{sm_row['D1_Oran']:.1f}</span></div>
                <div style="text-align:right">{format_currency(sm_row['D2_EBITDA'])}₺<br><span style="color:#64748b;font-size:0.75rem">%{sm_row['D2_Oran']:.1f}</span></div>
                <div style="text-align:center" class="{d1_d2_class}">{sm_row.get('D1_D2_Pct', 0):+.1f}%</div>
            </div>
            """
        
        st.markdown(row_html, unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # === ACİL VE YANGIN LİSTELERİ ===
    
    tab1, tab2 = st.tabs([f"🚨 Acil Müdahale ({int(acil_sayi)})", f"🔥 Yangın ({int(yangin_sayi)})"])
    
    with tab1:
        if acil_sayi > 0:
            acil_df = result_df[result_df['Acil']].sort_values(f'D{n}_EBITDA')
            
            # SM bazında grupla
            for sm in acil_df['SM'].unique():
                sm_name = sm.split()[0] if pd.notna(sm) else 'N/A'
                sm_magazalar = acil_df[acil_df['SM'] == sm]
                
                st.markdown(f"<p style='color:#f59e0b;font-weight:600;margin:16px 0 8px 0'>📁 {sm_name} ({len(sm_magazalar)} mağaza)</p>", unsafe_allow_html=True)
                
                for _, row in sm_magazalar.iterrows():
                    # Zaman serisi göster
                    if n == 3:
                        zaman_str = f"{donemler[0]}: {format_currency(row['D1_EBITDA'])}₺ (%{row['D1_EBITDA_Oran']:.1f}) → {donemler[1]}: {format_currency(row['D2_EBITDA'])}₺ (%{row['D2_EBITDA_Oran']:.1f}) → {donemler[2]}: {format_currency(row['D3_EBITDA'])}₺ (%{row['D3_EBITDA_Oran']:.1f})"
                    else:
                        zaman_str = f"{donemler[0]}: {format_currency(row['D1_EBITDA'])}₺ (%{row['D1_EBITDA_Oran']:.1f}) → {donemler[1]}: {format_currency(row['D2_EBITDA'])}₺ (%{row['D2_EBITDA_Oran']:.1f})"
                    
                    sebep = generate_sebep_analizi(row, donem_info)
                    
                    st.markdown(f"""
                    <div class="magaza-card-alert">
                        <div style="display:flex;justify-content:space-between;align-items:center">
                            <strong style="color:#ffffff">{row['Kod']} - {row['Mağaza'][:30]}</strong>
                        </div>
                        <div style="color:#94a3b8;font-size:0.85rem;margin-top:8px">{zaman_str}</div>
                        <div class="sebep-box">{sebep.replace(chr(10), '<br>')}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.success("✅ Acil müdahale gerektiren mağaza yok")
    
    with tab2:
        if yangin_sayi > 0:
            yangin_df = result_df[result_df['Yangin']].sort_values(f'D{n}_EBITDA')
            
            st.markdown("""
            <div style="background:#7f1d1d;border:1px solid #dc2626;border-radius:8px;padding:12px;margin-bottom:16px">
                <strong style="color:#fca5a5">⚠️ Bu mağazalara ÖNCE gidilmeli - Üst üste 2 ay negatif EBITDA</strong>
            </div>
            """, unsafe_allow_html=True)
            
            for sm in yangin_df['SM'].unique():
                sm_name = sm.split()[0] if pd.notna(sm) else 'N/A'
                sm_magazalar = yangin_df[yangin_df['SM'] == sm]
                
                st.markdown(f"<p style='color:#fb923c;font-weight:600;margin:16px 0 8px 0'>📁 {sm_name} ({len(sm_magazalar)} mağaza)</p>", unsafe_allow_html=True)
                
                for _, row in sm_magazalar.iterrows():
                    if n == 3:
                        zaman_str = f"{donemler[0]}: {format_currency(row['D1_EBITDA'])}₺ → {donemler[1]}: {format_currency(row['D2_EBITDA'])}₺ → {donemler[2]}: {format_currency(row['D3_EBITDA'])}₺"
                    else:
                        zaman_str = f"{donemler[0]}: {format_currency(row['D1_EBITDA'])}₺ → {donemler[1]}: {format_currency(row['D2_EBITDA'])}₺"
                    
                    sebep = generate_sebep_analizi(row, donem_info)
                    
                    st.markdown(f"""
                    <div class="magaza-card" style="border-left-color:#f97316">
                        <div style="display:flex;justify-content:space-between;align-items:center">
                            <strong style="color:#ffffff">🔥 {row['Kod']} - {row['Mağaza'][:30]}</strong>
                        </div>
                        <div style="color:#94a3b8;font-size:0.85rem;margin-top:8px">{zaman_str}</div>
                        <div class="sebep-box">{sebep.replace(chr(10), '<br>')}</div>
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
            result_df.to_excel(writer, sheet_name='TÜM VERİ', index=False)
            if acil_sayi > 0:
                result_df[result_df['Acil']].to_excel(writer, sheet_name='ACİL', index=False)
            if yangin_sayi > 0:
                result_df[result_df['Yangin']].to_excel(writer, sheet_name='YANGIN', index=False)
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
