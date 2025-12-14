import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="EBITDA Karar Sistemi", page_icon="🎯", layout="wide")

# Light Tema
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .main-header h1 { margin: 0; font-size: 1.8rem; }
    .main-header p { margin: 4px 0 0 0; opacity: 0.9; font-size: 0.9rem; }
    
    /* Karar Kutusu */
    .karar-box {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 4px solid #f59e0b;
        padding: 16px 20px;
        border-radius: 0 12px 12px 0;
        margin-bottom: 24px;
        color: #92400e;
        font-size: 1rem;
    }
    
    /* Metrik Kartları */
    .metric-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .metric-label { color: #64748b; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { color: #1e293b; font-size: 1.6rem; font-weight: 700; margin: 8px 0; }
    .metric-delta { font-size: 0.85rem; }
    .metric-delta.positive { color: #059669; }
    .metric-delta.negative { color: #dc2626; }
    
    /* Kategori Butonları */
    .kat-container { display: flex; gap: 12px; margin: 20px 0; }
    .kat-btn {
        flex: 1;
        padding: 16px;
        border-radius: 12px;
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        border: 2px solid transparent;
    }
    .kat-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    .kat-btn .sayi { font-size: 2rem; font-weight: 700; }
    .kat-btn .label { font-size: 0.8rem; margin-top: 4px; }
    
    .kat-basarili { background: #d1fae5; color: #065f46; border-color: #10b981; }
    .kat-dikkat { background: #fef3c7; color: #92400e; border-color: #f59e0b; }
    .kat-kritik { background: #fee2e2; color: #991b1b; border-color: #ef4444; }
    .kat-acil { background: #fecaca; color: #7f1d1d; border-color: #dc2626; }
    .kat-yangin { background: #7f1d1d; color: #fef2f2; border-color: #450a0a; }
    
    /* Tablo */
    .data-table {
        width: 100%;
        border-collapse: collapse;
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .data-table th {
        background: #f1f5f9;
        color: #475569;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 12px 16px;
        text-align: left;
        border-bottom: 2px solid #e2e8f0;
    }
    .data-table td {
        padding: 12px 16px;
        border-bottom: 1px solid #f1f5f9;
        color: #334155;
        font-size: 0.9rem;
    }
    .data-table tr:hover { background: #f8fafc; }
    
    /* Problem Kartları */
    .problem-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .problem-card.yapisal { border-left: 4px solid #6366f1; }
    .problem-card.akut { border-left: 4px solid #ef4444; }
    .problem-card.dalgali { border-left: 4px solid #f59e0b; }
    
    .problem-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .problem-title { font-weight: 600; color: #1e293b; font-size: 1rem; }
    .problem-badge { padding: 4px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 600; }
    .badge-yapisal { background: #e0e7ff; color: #4338ca; }
    .badge-akut { background: #fee2e2; color: #dc2626; }
    .badge-dalgali { background: #fef3c7; color: #d97706; }
    
    .problem-stats { color: #64748b; font-size: 0.85rem; margin-bottom: 8px; }
    .problem-desc { color: #475569; font-size: 0.85rem; font-style: italic; margin-bottom: 8px; }
    .problem-magazalar { color: #64748b; font-size: 0.8rem; }
    
    /* Mağaza Kartı */
    .magaza-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .magaza-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .magaza-isim { font-weight: 600; color: #1e293b; }
    .magaza-meta { color: #64748b; font-size: 0.8rem; }
    
    .trend-row { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
    .trend-item { text-align: center; padding: 8px 12px; background: #f8fafc; border-radius: 8px; }
    .trend-label { font-size: 0.65rem; color: #64748b; text-transform: uppercase; }
    .trend-value { font-size: 0.95rem; font-weight: 600; color: #1e293b; }
    .trend-oran { font-size: 0.75rem; color: #64748b; }
    .trend-arrow { font-size: 0.85rem; font-weight: 600; }
    .trend-arrow.up { color: #059669; }
    .trend-arrow.down { color: #dc2626; }
    
    .neden-box { background: #f8fafc; border-radius: 8px; padding: 12px; }
    .neden-title { font-size: 0.75rem; color: #64748b; text-transform: uppercase; margin-bottom: 8px; }
    .neden-item { font-size: 0.85rem; color: #475569; padding: 4px 0; }
    
    /* Band etiketi */
    .band-normal { background: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; }
    .band-dusuk { background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; }
    .band-cok-dusuk { background: #fed7aa; color: #c2410c; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; }
    .band-kritik { background: #fecaca; color: #991b1b; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; }
</style>
""", unsafe_allow_html=True)

# === YARDIMCI FONKSİYONLAR ===

def extract_code(magaza):
    if pd.isna(magaza):
        return None
    return str(magaza).split()[0]

def get_magaza_isim(magaza_full):
    if pd.isna(magaza_full):
        return ""
    parts = str(magaza_full).split(' ', 1)
    return parts[1][:35] if len(parts) > 1 else str(magaza_full)[:35]

def format_currency(value):
    if pd.isna(value) or value == 0:
        return "-"
    if abs(value) >= 1000000:
        return f"{value/1000000:.2f}M₺"
    elif abs(value) >= 1000:
        return f"{value/1000:.0f}K₺"
    return f"{value:,.0f}₺"

def get_ebitda_band(seviye_sapma):
    if seviye_sapma >= -0.5:
        return 'NORMAL', 'band-normal'
    elif seviye_sapma >= -1.5:
        return 'DÜŞÜK', 'band-dusuk'
    elif seviye_sapma >= -3.0:
        return 'ÇOK DÜŞÜK', 'band-cok-dusuk'
    else:
        return 'KRİTİK', 'band-kritik'

def get_yapisal_akut(d1_yuksek, d2_yuksek, d3_yuksek):
    """3 aya bakarak yapısal mı akut mu belirle"""
    yuksek_sayisi = sum([d1_yuksek, d2_yuksek, d3_yuksek])
    
    if yuksek_sayisi >= 2:
        return '📌 YAPISAL', 'yapisal', 'badge-yapisal', '3 aydır yüksek, yapısal sorun'
    elif d3_yuksek and not d2_yuksek:
        return '⚡ AKUT', 'akut', 'badge-akut', 'Son ay ani artış, acil müdahale'
    elif yuksek_sayisi == 1:
        return '🔄 DALGALI', 'dalgali', 'badge-dalgali', 'İstikrarsız, takip et'
    else:
        return '✓ NORMAL', 'normal', '', ''

# === VERİ İŞLEME ===

@st.cache_data
def load_and_process(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name='EBITDA', header=1)
    df = df[df['Kar / Zarar'] != 'GENEL'].copy()
    
    ay_map = {'Ocak': 1, 'Şubat': 2, 'Mart': 3, 'Nisan': 4, 'Mayıs': 5, 'Haziran': 6,
              'Temmuz': 7, 'Ağustos': 8, 'Eylül': 9, 'Ekim': 10, 'Kasım': 11, 'Aralık': 12}
    
    donemler = df['Mali yıl/dönem - Orta uzunl.metin'].dropna().unique()
    donemler = sorted(donemler, key=lambda d: ay_map.get(d.split()[0], 0))[-3:]
    
    if len(donemler) < 2:
        return None, None, "En az 2 dönem gerekli"
    
    donem_data = {}
    for d in donemler:
        temp = df[df['Mali yıl/dönem - Orta uzunl.metin'] == d].copy()
        temp['Kod'] = temp['Mağaza'].apply(extract_code)
        donem_data[d] = temp.set_index('Kod')
    
    son_donem = donemler[-1]
    son_df = donem_data[son_donem]
    son_df['_NetSatis'] = pd.to_numeric(son_df['Net Satış (KDV Hariç)'], errors='coerce').fillna(0)
    valid_codes = set(son_df[son_df['_NetSatis'] > 0].index)
    
    for d in donemler[:-1]:
        valid_codes = valid_codes & set(donem_data[d].index)
    
    results = []
    
    for kod in valid_codes:
        row = {'Kod': kod}
        
        son = son_df.loc[kod]
        if isinstance(son, pd.DataFrame):
            son = son.iloc[0]
        
        row['Magaza'] = str(son['Mağaza'])
        row['Magaza_Isim'] = get_magaza_isim(son['Mağaza'])
        row['SM'] = str(son['Satış Müdürü - Metin']).split()[0] if pd.notna(son['Satış Müdürü - Metin']) else ''
        row['BS'] = str(son['Bölge Sorumlusu - Metin']).split()[0] if pd.notna(son['Bölge Sorumlusu - Metin']) else ''
        
        for i, d in enumerate(donemler):
            prefix = f'D{i+1}_'
            data = donem_data[d]
            
            if kod in data.index:
                r = data.loc[kod]
                if isinstance(r, pd.DataFrame):
                    r = r.iloc[0]
                
                ns = pd.to_numeric(r.get('Net Satış (KDV Hariç)', 0), errors='coerce') or 0
                ebitda = pd.to_numeric(r.get('Mağaza Kar/Zararı', 0), errors='coerce') or 0
                smm = pd.to_numeric(r.get('SMM', 0), errors='coerce') or 0
                iade = pd.to_numeric(r.get('Satış İade ve İskontoları', 0), errors='coerce') or 0
                env = pd.to_numeric(r.get('Envanter Kaybı Mağaza', 0), errors='coerce') or 0
                personel = pd.to_numeric(r.get('Personel Giderleri', 0), errors='coerce') or 0
                kira = pd.to_numeric(r.get('Mağaza Kira Giderleri', 0), errors='coerce') or 0
                elektrik = pd.to_numeric(r.get('Su\\Elektrik\\Telefon Giderleri ', 0), errors='coerce') or 0
                
                row[f'{prefix}NetSatis'] = ns
                row[f'{prefix}EBITDA'] = ebitda
                row[f'{prefix}EBITDA_Oran'] = (ebitda / ns * 100) if ns > 0 else 0
                row[f'{prefix}SMM_Oran'] = (abs(smm) / ns * 100) if ns > 0 else 0
                row[f'{prefix}Iade_Oran'] = (abs(iade) / ns * 100) if ns > 0 else 0
                row[f'{prefix}Env_Oran'] = (abs(env) / ns * 100) if ns > 0 else 0
                row[f'{prefix}Personel'] = personel
                row[f'{prefix}Personel_Oran'] = (personel / ns * 100) if ns > 0 else 0
                row[f'{prefix}Kira'] = kira
                row[f'{prefix}Kira_Oran'] = (kira / ns * 100) if ns > 0 else 0
                row[f'{prefix}Elektrik'] = elektrik
                row[f'{prefix}Elektrik_Oran'] = (elektrik / ns * 100) if ns > 0 else 0
        
        results.append(row)
    
    result_df = pd.DataFrame(results)
    n = len(donemler)
    
    # Değişimler
    if n >= 2:
        result_df['D1_D2_EBITDA_Pct'] = ((result_df['D2_EBITDA'] - result_df['D1_EBITDA']) / result_df['D1_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
    if n >= 3:
        result_df['D2_D3_EBITDA_Pct'] = ((result_df['D3_EBITDA'] - result_df['D2_EBITDA']) / result_df['D2_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
    
    # Bölge medyanı
    son_oran_col = f'D{n}_EBITDA_Oran'
    bolge_medyan = result_df[son_oran_col].median()
    
    # Hibrit Skor
    result_df['Seviye_Sapma'] = result_df[son_oran_col] - bolge_medyan
    
    if n >= 3:
        result_df['Trend_Degisim'] = result_df['D3_EBITDA_Oran'] - result_df['D2_EBITDA_Oran']
    else:
        result_df['Trend_Degisim'] = result_df['D2_EBITDA_Oran'] - result_df['D1_EBITDA_Oran']
    
    result_df['Hibrit_Skor'] = result_df['Seviye_Sapma'] + (result_df['Trend_Degisim'] * 1.5)
    
    # EBITDA Bandı
    result_df['EBITDA_Band'] = result_df['Seviye_Sapma'].apply(lambda x: get_ebitda_band(x)[0])
    
    # Kategori
    def kategorize(row):
        skor = row['Hibrit_Skor']
        if n >= 3:
            if row['D2_EBITDA'] < 0 and row['D3_EBITDA'] < 0:
                return '🔥 Yangın'
        else:
            if row['D1_EBITDA'] < 0 and row['D2_EBITDA'] < 0:
                return '🔥 Yangın'
        
        if skor >= 0:
            return '🟩 Başarılı'
        elif skor >= -1:
            return '🟧 Dikkat'
        elif skor >= -2.5:
            return '🟥 Kritik'
        else:
            return '🚨 Acil'
    
    result_df['Kategori'] = result_df.apply(kategorize, axis=1)
    
    return result_df, {'donemler': donemler, 'n': n, 'bolge_medyan': bolge_medyan}, None


def generate_neden(row, donem_info):
    n = donem_info['n']
    donemler = donem_info['donemler']
    nedenler = []
    
    if n >= 3:
        d1, d2 = 'D2_', 'D3_'
    else:
        d1, d2 = 'D1_', 'D2_'
    
    # EBITDA Oran
    oran1, oran2 = row.get(f'{d1}EBITDA_Oran', 0), row.get(f'{d2}EBITDA_Oran', 0)
    if oran2 - oran1 < -2:
        nedenler.append(f"📊 EBITDA Oranı: %{oran1:.1f} → %{oran2:.1f} ({oran2-oran1:+.1f}p)")
    
    # Ciro
    ciro1, ciro2 = row.get(f'{d1}NetSatis', 0), row.get(f'{d2}NetSatis', 0)
    ciro_pct = ((ciro2 - ciro1) / ciro1 * 100) if ciro1 > 0 else 0
    if ciro_pct < -10:
        nedenler.append(f"📉 Ciro: {format_currency(ciro1)} → {format_currency(ciro2)} ({ciro_pct:+.0f}%)")
    
    # SMM
    smm1, smm2 = row.get(f'{d1}SMM_Oran', 0), row.get(f'{d2}SMM_Oran', 0)
    if smm2 - smm1 > 1:
        nedenler.append(f"🏭 SMM: %{smm1:.1f} → %{smm2:.1f} ({smm2-smm1:+.1f}p)")
    
    # Envanter
    env1, env2 = row.get(f'{d1}Env_Oran', 0), row.get(f'{d2}Env_Oran', 0)
    if env2 - env1 > 0.5:
        nedenler.append(f"📦 Envanter: %{env1:.1f} → %{env2:.1f} ({env2-env1:+.1f}p)")
    
    # Giderler
    for key, icon, name in [('Personel', '👥', 'Personel'), ('Kira', '🏠', 'Kira'), ('Elektrik', '⚡', 'Elektrik')]:
        tl1, tl2 = row.get(f'{d1}{key}', 0), row.get(f'{d2}{key}', 0)
        oran1, oran2 = row.get(f'{d1}{key}_Oran', 0), row.get(f'{d2}{key}_Oran', 0)
        
        if oran2 - oran1 > 1:
            if tl2 - tl1 > 5000:
                nedenler.append(f"{icon} {name}: TL arttı ({format_currency(tl1)}→{format_currency(tl2)})")
            else:
                nedenler.append(f"{icon} {name}: Ciro düşünce oran arttı (%{oran1:.1f}→%{oran2:.1f})")
    
    return nedenler if nedenler else ["✓ Belirgin bozulma yok"]


def karar_cumlesi_uret(df, n):
    kritik = df[df['Kategori'].isin(['🚨 Acil', '🔥 Yangın'])]
    gizli = df[(df['Kategori'].isin(['🟧 Dikkat', '🟥 Kritik'])) & (df[f'D{n}_EBITDA'] > 0)]
    
    # Kök neden analizi
    ana_problem = []
    for col, name in [(f'D{n}_Elektrik_Oran', 'Elektrik'), (f'D{n}_Env_Oran', 'Envanter'), (f'D{n}_Personel_Oran', 'Personel')]:
        if col in df.columns:
            bolge_med = df[col].median()
            yuksek_oran = (df[col] > bolge_med + 1).mean()
            if yuksek_oran > 0.3:
                ana_problem.append(name)
    
    return f"Bu ay **{len(kritik)} mağaza** acil/yangın seviyesinde. **{len(gizli)} mağaza** kâr ediyor ama hızla bozuluyor. Ana problem: **{', '.join(ana_problem) if ana_problem else 'Dağınık (mağaza bazlı)'}**."


def analyze_kok_neden(df, n):
    """SM ve BS bazında kök neden analizi - Yapısal/Akut"""
    results = []
    
    metrikler = [
        ('Elektrik_Oran', '⚡ Elektrik', 1.0),
        ('Env_Oran', '📦 Envanter', 0.5),
        ('Personel_Oran', '👥 Personel', 1.0),
        ('Iade_Oran', '↩️ İade', 0.3),
        ('SMM_Oran', '🏭 SMM', 1.0)
    ]
    
    for col_base, name, esik in metrikler:
        # 3 ay için medyanlar
        medyanlar = {}
        for i in range(1, n+1):
            col = f'D{i}_{col_base}'
            if col in df.columns:
                medyanlar[i] = df[col].median()
        
        if not medyanlar:
            continue
        
        son_col = f'D{n}_{col_base}'
        bolge_med = medyanlar[n]
        
        # SM bazında analiz
        for sm in df['SM'].unique():
            if not sm:
                continue
            sm_df = df[df['SM'] == sm]
            sm_count = len(sm_df)
            
            if sm_count < 3:
                continue
            
            # 3 ay için yüksek sayısı
            yuksek_by_ay = {}
            for i in range(1, n+1):
                col = f'D{i}_{col_base}'
                if col in df.columns:
                    yuksek_by_ay[i] = (sm_df[col] > medyanlar[i] + esik).sum()
            
            # Son ay yüksek olanlar
            son_yuksek = sm_df[sm_df[son_col] > bolge_med + esik]
            son_yuksek_oran = len(son_yuksek) / sm_count
            
            if son_yuksek_oran >= 0.40:  # %40+ SM bazlı
                # Yapısal mı Akut mu?
                d1_yuksek = yuksek_by_ay.get(1, 0) / sm_count >= 0.30 if n >= 1 else False
                d2_yuksek = yuksek_by_ay.get(2, 0) / sm_count >= 0.30 if n >= 2 else False
                d3_yuksek = yuksek_by_ay.get(3, 0) / sm_count >= 0.30 if n >= 3 else False
                
                tip, tip_class, badge_class, aciklama = get_yapisal_akut(d1_yuksek, d2_yuksek, d3_yuksek)
                
                if tip != '✓ NORMAL':
                    magazalar = son_yuksek['Magaza_Isim'].head(5).tolist()
                    results.append({
                        'seviye': 'SM',
                        'birim': sm,
                        'metrik': name,
                        'oran': son_yuksek_oran,
                        'sayi': len(son_yuksek),
                        'toplam': sm_count,
                        'tip': tip,
                        'tip_class': tip_class,
                        'badge_class': badge_class,
                        'aciklama': aciklama,
                        'magazalar': magazalar
                    })
        
        # BS bazında analiz
        for bs in df['BS'].unique():
            if not bs:
                continue
            bs_df = df[df['BS'] == bs]
            bs_count = len(bs_df)
            
            if bs_count < 3:
                continue
            
            # Son ay yüksek olanlar
            son_yuksek = bs_df[bs_df[son_col] > bolge_med + esik]
            son_yuksek_oran = len(son_yuksek) / bs_count
            
            if son_yuksek_oran >= 0.30 and len(son_yuksek) >= 3:  # %30+ veya en az 3 mağaza
                # Yapısal mı Akut mu?
                yuksek_by_ay = {}
                for i in range(1, n+1):
                    col = f'D{i}_{col_base}'
                    if col in df.columns:
                        yuksek_by_ay[i] = (bs_df[col] > medyanlar[i] + esik).sum()
                
                d1_yuksek = yuksek_by_ay.get(1, 0) / bs_count >= 0.25 if n >= 1 else False
                d2_yuksek = yuksek_by_ay.get(2, 0) / bs_count >= 0.25 if n >= 2 else False
                d3_yuksek = yuksek_by_ay.get(3, 0) / bs_count >= 0.25 if n >= 3 else False
                
                tip, tip_class, badge_class, aciklama = get_yapisal_akut(d1_yuksek, d2_yuksek, d3_yuksek)
                
                if tip != '✓ NORMAL':
                    # SM'yi bul
                    sm = bs_df['SM'].iloc[0] if len(bs_df) > 0 else ''
                    magazalar = son_yuksek['Magaza_Isim'].head(5).tolist()
                    results.append({
                        'seviye': 'BS',
                        'birim': f"{bs} ({sm})",
                        'metrik': name,
                        'oran': son_yuksek_oran,
                        'sayi': len(son_yuksek),
                        'toplam': bs_count,
                        'tip': tip,
                        'tip_class': tip_class,
                        'badge_class': badge_class,
                        'aciklama': aciklama,
                        'magazalar': magazalar
                    })
    
    return results


# === ANA UYGULAMA ===

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎯 EBITDA Karar Sistemi</h1>
        <p>Hibrit Skor Modeli | Seviye + Trend Analizi</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'data' not in st.session_state:
        st.session_state.data = None
        st.session_state.info = None
    
    uploaded_file = st.file_uploader("Excel dosyası yükle", type=['xlsx'], label_visibility="collapsed")
    
    if uploaded_file:
        with st.spinner("Veri işleniyor..."):
            result_df, info, error = load_and_process(uploaded_file)
        if error:
            st.error(error)
            return
        st.session_state.data = result_df
        st.session_state.info = info
    
    if st.session_state.data is None:
        st.info("📁 EBITDA Excel dosyasını yükleyin")
        return
    
    df = st.session_state.data
    info = st.session_state.info
    donemler = info['donemler']
    n = info['n']
    bolge_medyan = info['bolge_medyan']
    
    # === KARAR CÜMLESİ ===
    st.markdown(f'<div class="karar-box">💡 {karar_cumlesi_uret(df, n)}</div>', unsafe_allow_html=True)
    
    # === BÖLGE TREND ===
    st.subheader("📊 Bölge EBITDA Trendi")
    
    cols = st.columns(n)
    for i, (col, d) in enumerate(zip(cols, donemler)):
        ebitda = df[f'D{i+1}_EBITDA'].sum()
        satis = df[f'D{i+1}_NetSatis'].sum()
        oran = (ebitda / satis * 100) if satis > 0 else 0
        
        delta_html = ""
        if i > 0:
            onceki = df[f'D{i}_EBITDA'].sum()
            degisim = ebitda - onceki
            pct = ((ebitda - onceki) / abs(onceki) * 100) if onceki != 0 else 0
            delta_class = "negative" if degisim < 0 else "positive"
            delta_html = f'<div class="metric-delta {delta_class}">{format_currency(degisim)} ({pct:+.1f}%)</div>'
        
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{d}</div>
                <div class="metric-value">{format_currency(ebitda)}</div>
                <div class="metric-delta">%{oran:.2f}</div>
                {delta_html}
            </div>
            """, unsafe_allow_html=True)
    
    st.caption(f"📐 Bölge Medyanı: **%{bolge_medyan:.2f}** | Toplam: **{len(df)} mağaza**")
    
    # === KATEGORİ DAĞILIMI ===
    st.markdown("---")
    st.subheader("📦 Kategori Dağılımı")
    
    kategoriler = ['🟩 Başarılı', '🟧 Dikkat', '🟥 Kritik', '🚨 Acil', '🔥 Yangın']
    kat_class = ['kat-basarili', 'kat-dikkat', 'kat-kritik', 'kat-acil', 'kat-yangin']
    kategori_sayilari = {k: len(df[df['Kategori'] == k]) for k in kategoriler}
    
    cols = st.columns(5)
    for i, (kat, col, cls) in enumerate(zip(kategoriler, cols, kat_class)):
        sayi = kategori_sayilari[kat]
        with col:
            if st.button(f"{kat.split()[0]} {kat.split()[1]}\n{sayi}", key=f"kat_{i}", use_container_width=True):
                st.session_state.secili_kategori = kat
    
    # Seçili kategori detayı
    if 'secili_kategori' in st.session_state and st.session_state.secili_kategori:
        kat = st.session_state.secili_kategori
        kat_df = df[df['Kategori'] == kat].sort_values('Hibrit_Skor')
        
        st.markdown(f"### {kat} - {len(kat_df)} Mağaza")
        
        for _, row in kat_df.iterrows():
            band, band_class = get_ebitda_band(row['Seviye_Sapma'])
            
            with st.expander(f"**{row['Magaza_Isim']}** | {row['SM']} / {row['BS']} | Skor: {row['Hibrit_Skor']:.1f}"):
                # Trend
                if n == 3:
                    c1, c2, c3, c4, c5 = st.columns([1.2, 0.5, 1.2, 0.5, 1.2])
                    
                    c1.markdown(f"**{donemler[0]}**<br>{format_currency(row['D1_EBITDA'])}<br>%{row['D1_EBITDA_Oran']:.1f}", unsafe_allow_html=True)
                    
                    d1_d2 = row.get('D1_D2_EBITDA_Pct', 0)
                    c2.markdown(f"<br>{'🔴' if d1_d2 < 0 else '🟢'}<br>{d1_d2:+.0f}%", unsafe_allow_html=True)
                    
                    c3.markdown(f"**{donemler[1]}**<br>{format_currency(row['D2_EBITDA'])}<br>%{row['D2_EBITDA_Oran']:.1f}", unsafe_allow_html=True)
                    
                    d2_d3 = row.get('D2_D3_EBITDA_Pct', 0)
                    c4.markdown(f"<br>{'🔴' if d2_d3 < 0 else '🟢'}<br>{d2_d3:+.0f}%", unsafe_allow_html=True)
                    
                    c5.markdown(f"**{donemler[2]}**<br>{format_currency(row['D3_EBITDA'])}<br>%{row['D3_EBITDA_Oran']:.1f}", unsafe_allow_html=True)
                
                st.markdown(f"""
                **📐 Skor:** Seviye {row['Seviye_Sapma']:+.1f} + Trend {row['Trend_Degisim']:+.1f}×1.5 = **{row['Hibrit_Skor']:.1f}** | Band: `{band}`
                """)
                
                st.markdown("**📋 Neden?**")
                for neden in generate_neden(row, info):
                    st.markdown(f"- {neden}")
    
    # === SM PERFORMANS ===
    st.markdown("---")
    st.subheader("👥 SM Performans")
    
    sm_agg = {f'D{i}_EBITDA': 'sum' for i in range(1, n+1)}
    sm_agg.update({f'D{i}_NetSatis': 'sum' for i in range(1, n+1)})
    sm_agg['Kod'] = 'count'
    
    sm_df = df.groupby('SM').agg(sm_agg).reset_index()
    sm_df = sm_df[sm_df['Kod'] > 2]
    
    for i in range(1, n+1):
        sm_df[f'D{i}_Oran'] = (sm_df[f'D{i}_EBITDA'] / sm_df[f'D{i}_NetSatis'] * 100).fillna(0)
    
    if n >= 2:
        sm_df['D1_D2_Pct'] = ((sm_df['D2_EBITDA'] - sm_df['D1_EBITDA']) / sm_df['D1_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
    if n >= 3:
        sm_df['D2_D3_Pct'] = ((sm_df['D3_EBITDA'] - sm_df['D2_EBITDA']) / sm_df['D2_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
    
    for kat in kategoriler:
        for sm in sm_df['SM'].unique():
            sm_df.loc[sm_df['SM'] == sm, kat] = len(df[(df['SM'] == sm) & (df['Kategori'] == kat)])
    
    sm_df = sm_df.sort_values(f'D{n}_EBITDA', ascending=False)
    
    for _, sm_row in sm_df.iterrows():
        sm_name = sm_row['SM']
        kat_ozet = " ".join([f"{k.split()[0]}{int(sm_row.get(k, 0))}" for k in kategoriler if sm_row.get(k, 0) > 0])
        
        with st.expander(f"**{sm_name}** ({int(sm_row['Kod'])} mğz) | {kat_ozet}"):
            # SM Trend
            if n == 3:
                st.markdown(f"""
                | Dönem | EBITDA | Oran | Δ% |
                |-------|--------|------|-----|
                | {donemler[0]} | {format_currency(sm_row['D1_EBITDA'])} | %{sm_row['D1_Oran']:.1f} | - |
                | {donemler[1]} | {format_currency(sm_row['D2_EBITDA'])} | %{sm_row['D2_Oran']:.1f} | {sm_row.get('D1_D2_Pct', 0):+.1f}% |
                | {donemler[2]} | {format_currency(sm_row['D3_EBITDA'])} | %{sm_row['D3_Oran']:.1f} | {sm_row.get('D2_D3_Pct', 0):+.1f}% |
                """)
            
            # BS'ler
            st.markdown("**👔 Bölge Sorumluları:**")
            bs_df = df[df['SM'] == sm_name].groupby('BS').agg({
                f'D{n}_EBITDA': 'sum',
                f'D{n}_NetSatis': 'sum',
                'Kod': 'count',
                'Kategori': lambda x: dict(x.value_counts())
            }).reset_index()
            
            for _, bs_row in bs_df.iterrows():
                bs_name = bs_row['BS']
                bs_magazalar = df[(df['SM'] == sm_name) & (df['BS'] == bs_name)]
                bs_kritik = bs_magazalar[bs_magazalar['Kategori'].isin(['🚨 Acil', '🔥 Yangın', '🟥 Kritik'])]
                
                oran = (bs_row[f'D{n}_EBITDA'] / bs_row[f'D{n}_NetSatis'] * 100) if bs_row[f'D{n}_NetSatis'] > 0 else 0
                
                with st.expander(f"📁 {bs_name} ({int(bs_row['Kod'])} mğz) | {format_currency(bs_row[f'D{n}_EBITDA'])} | %{oran:.1f}"):
                    if len(bs_kritik) > 0:
                        st.markdown("**⚠️ Dikkat Gerektiren:**")
                        for _, m in bs_kritik.sort_values('Hibrit_Skor').iterrows():
                            st.markdown(f"- **{m['Magaza_Isim']}** | {m['Kategori']} | Skor: {m['Hibrit_Skor']:.1f}")
                    else:
                        st.success("✓ Kritik mağaza yok")
    
    # === KÖK NEDEN ANALİZİ ===
    st.markdown("---")
    st.subheader("🔍 Kök Neden Analizi")
    st.caption("SM/BS bazında yaygın problemler - Yapısal mı Akut mu?")
    
    kok_nedenler = analyze_kok_neden(df, n)
    
    if kok_nedenler:
        # SM bazlı
        sm_problemler = [k for k in kok_nedenler if k['seviye'] == 'SM']
        if sm_problemler:
            st.markdown("### 🔴 SM Bazlı Problemler")
            for p in sm_problemler:
                st.markdown(f"""
                <div class="problem-card {p['tip_class']}">
                    <div class="problem-header">
                        <div class="problem-title">{p['birim']} - {p['metrik']}</div>
                        <span class="problem-badge {p['badge_class']}">{p['tip']}</span>
                    </div>
                    <div class="problem-stats">%{p['oran']*100:.0f} ({p['sayi']}/{p['toplam']} mağaza)</div>
                    <div class="problem-desc">{p['aciklama']}</div>
                    <div class="problem-magazalar">📍 {', '.join(p['magazalar'])}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # BS bazlı
        bs_problemler = [k for k in kok_nedenler if k['seviye'] == 'BS']
        if bs_problemler:
            st.markdown("### 🟠 BS Bazlı Problemler")
            for p in bs_problemler:
                st.markdown(f"""
                <div class="problem-card {p['tip_class']}">
                    <div class="problem-header">
                        <div class="problem-title">{p['birim']} - {p['metrik']}</div>
                        <span class="problem-badge {p['badge_class']}">{p['tip']}</span>
                    </div>
                    <div class="problem-stats">%{p['oran']*100:.0f} ({p['sayi']}/{p['toplam']} mağaza)</div>
                    <div class="problem-desc">{p['aciklama']}</div>
                    <div class="problem-magazalar">📍 {', '.join(p['magazalar'])}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.success("✓ Yaygın SM/BS bazlı problem tespit edilmedi. Sorunlar mağaza bazında.")
    
    # === GİZLİ TEHLİKE ===
    st.markdown("---")
    st.subheader("⚠️ Gizli Tehlike: Kârlı ama Düşenler")
    
    gizli = df[(df[f'D{n}_EBITDA'] > 0) & (df['Kategori'].isin(['🟧 Dikkat', '🟥 Kritik']))].sort_values('Hibrit_Skor').head(10)
    
    if len(gizli) > 0:
        st.warning(f"{len(gizli)} mağaza kâr ediyor ama hızla bozuluyor!")
        
        for _, row in gizli.iterrows():
            with st.expander(f"**{row['Magaza_Isim']}** | {row['Kategori']} | EBITDA: {format_currency(row[f'D{n}_EBITDA'])} | Skor: {row['Hibrit_Skor']:.1f}"):
                st.markdown("**Neden tehlike?**")
                for neden in generate_neden(row, info):
                    st.markdown(f"- {neden}")
    else:
        st.success("✓ Gizli tehlike yok")
    
    # === EXPORT ===
    st.markdown("---")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='TÜM', index=False)
        for kat in kategoriler:
            kat_df = df[df['Kategori'] == kat]
            if len(kat_df) > 0:
                kat_df.to_excel(writer, sheet_name=kat.split()[1][:10], index=False)
    
    st.download_button("📥 Excel İndir", data=output.getvalue(),
                       file_name=f"EBITDA_Karar_{donemler[-1].replace(' ','_')}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


if __name__ == "__main__":
    main()
