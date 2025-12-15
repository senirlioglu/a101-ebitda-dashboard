import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="EBITDA Karar Motoru", page_icon="🎯", layout="wide")

# === CONFIG ===
GIDER_RULES = {
    "Personel": {"col": "Personel Giderleri", "abs": 0.30, "rel": 0.15, "min_tl": 0},
    "Prim": {"col": "Personel Primleri", "abs": 0.10, "rel": 0.30, "min_tl": 0},
    "Kira": {"col": "Mağaza Kira Giderleri", "abs": 0.10, "rel": 0.10, "min_tl": 0},
    "Aidat": {"col": "Mağaza Aidat Giderleri", "abs": 0.05, "rel": 0.30, "min_tl": 500},
    "Reklam": {"col": "İlan Reklam Giderleri", "abs": 0.05, "rel": 0.50, "min_tl": 1000},
    "Elektrik": {"col": "Su\\Elektrik\\Telefon Giderleri ", "abs": 0.20, "rel": 0.30, "min_tl": 0},
    "Bilgisayar": {"col": "Bilgisayar Bakım Onarım Giderleri ", "abs": 0.05, "rel": 1.00, "min_tl": 500},
    "Temizlik": {"col": "Temizlik ve Bakım Onarım Giderleri", "abs": 0.05, "rel": 1.00, "min_tl": 2000},
    "Amortisman": {"col": "Amoritsman Giderleri", "abs": 0.05, "rel": 0.20, "min_tl": 0},
    "Ambalaj": {"col": "Ambalaj Giderleri", "abs": 0.05, "rel": 0.30, "min_tl": 500},
    "Sigorta": {"col": "Sigorta Giderleri", "abs": 0.03, "rel": 0.20, "min_tl": 0},
    "Banka": {"col": "Banka Para Toplama Giderleri", "abs": 0.03, "rel": 0.30, "min_tl": 300},
    "Belediye": {"col": "Belediye Vergiler", "abs": 0.03, "rel": 0.30, "min_tl": 300},
    "Diger": {"col": "Diğer Giderler", "abs": 0.05, "rel": 0.50, "min_tl": 500},
    "Toplam": {"col": "Toplam Mağaza Giderleri", "abs": 0.50, "rel": 0.10, "min_tl": 0},
}

GELIR_RULES = {
    "NetSatis": {"level_drop": -0.08},  # %8 düşüş
    "SMM": {"abs": 1.0},
    "Iade": {"abs": 0.3},
    "Envanter": {"abs": 0.3},
    "SabitGider_Oran": {"abs": 0.30},  # 0.30 puan artış
    "SabitGider_TL": {"rel": 0.02},    # %2'den az değişim = sabit
}

# === STYLE ===
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .main-header { background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white; padding: 20px 24px; border-radius: 12px; margin-bottom: 24px; }
    .main-header h1 { margin: 0; font-size: 1.8rem; }
    .karar-box { background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-left: 4px solid #f59e0b; padding: 16px 20px; border-radius: 0 12px 12px 0; margin-bottom: 24px; color: #92400e; }
    .metric-card { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .metric-value { font-size: 1.5rem; font-weight: 700; color: #1e293b; }
    .metric-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; }
    .ajan-box { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin: 8px 0; }
    .ajan-ebitda { border-left: 4px solid #6366f1; }
    .ajan-gelir { border-left: 4px solid #10b981; }
    .ajan-gider { border-left: 4px solid #f59e0b; }
    .ajan-envanter { border-left: 4px solid #ef4444; }
    .ajan-title { font-weight: 600; font-size: 0.9rem; margin-bottom: 8px; }
    .hukum-box { background: #fef2f2; border: 2px solid #ef4444; border-radius: 12px; padding: 16px; margin-top: 12px; }
    .problem-item { background: #fee2e2; padding: 4px 8px; border-radius: 4px; margin: 2px; display: inline-block; font-size: 0.8rem; }
    .ok-item { background: #d1fae5; padding: 4px 8px; border-radius: 4px; margin: 2px; display: inline-block; font-size: 0.8rem; }
    .sm-alert { background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 8px 12px; margin-top: 8px; color: #991b1b; font-size: 0.85rem; }
    .filter-box { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-bottom: 16px; }
</style>
""", unsafe_allow_html=True)

# === HELPERS ===
def extract_code(m):
    return str(m).split()[0] if pd.notna(m) else None

def get_isim(m):
    if pd.isna(m): return ""
    p = str(m).split(' ', 1)
    return p[1][:40] if len(p) > 1 else str(m)[:40]

def fmt(v):
    if pd.isna(v) or v == 0: return "-"
    if abs(v) >= 1e6: return f"{v/1e6:.2f}M₺"
    if abs(v) >= 1e3: return f"{v/1e3:.0f}K₺"
    return f"{v:,.0f}₺"

def safe_div(a, b):
    return (a / b * 100) if b and b != 0 else 0

def safe_pct(new, old):
    if old == 0 or pd.isna(old): return 0
    return ((new - old) / abs(old)) * 100

# === DATA LOADING ===
@st.cache_data
def load_data(f):
    try:
        df = pd.read_excel(f, sheet_name='EBITDA', header=1)
    except Exception as e:
        return None, None, f"Excel okuma hatası: {str(e)}"
    
    df = df[df['Kar / Zarar'] != 'GENEL'].copy()
    
    if 'Mali yıl/dönem - Orta uzunl.metin' not in df.columns:
        return None, None, "Dönem kolonu bulunamadı"
    
    ay_map = {'Ocak':1,'Şubat':2,'Mart':3,'Nisan':4,'Mayıs':5,'Haziran':6,'Temmuz':7,'Ağustos':8,'Eylül':9,'Ekim':10,'Kasım':11,'Aralık':12}
    donemler = sorted(df['Mali yıl/dönem - Orta uzunl.metin'].dropna().unique(), key=lambda d: ay_map.get(str(d).split()[0], 0))[-3:]
    
    if len(donemler) < 2:
        return None, None, "En az 2 dönem gerekli"
    
    donem_data = {}
    for d in donemler:
        t = df[df['Mali yıl/dönem - Orta uzunl.metin'] == d].copy()
        t['Kod'] = t['Mağaza'].apply(extract_code)
        donem_data[d] = t.set_index('Kod')
    
    son = donem_data[donemler[-1]]
    son['_NS'] = pd.to_numeric(son['Net Satış (KDV Hariç)'], errors='coerce').fillna(0)
    valid = set(son[son['_NS'] > 0].index)
    for d in donemler[:-1]:
        valid &= set(donem_data[d].index)
    
    if len(valid) == 0:
        return None, None, "Geçerli mağaza bulunamadı"
    
    results = []
    for kod in valid:
        row = {'Kod': kod}
        s = son.loc[kod]
        if isinstance(s, pd.DataFrame): s = s.iloc[0]
        
        row['Magaza_Isim'] = get_isim(s.get('Mağaza', ''))
        row['SM'] = str(s.get('Satış Müdürü - Metin', '')).split()[0] if pd.notna(s.get('Satış Müdürü - Metin')) else ''
        row['BS'] = str(s.get('Bölge Sorumlusu - Metin', '')).split()[0] if pd.notna(s.get('Bölge Sorumlusu - Metin')) else ''
        
        for i, d in enumerate(donemler):
            p = f'D{i+1}_'
            if kod not in donem_data[d].index:
                continue
            r = donem_data[d].loc[kod]
            if isinstance(r, pd.DataFrame): r = r.iloc[0]
            
            ns = pd.to_numeric(r.get('Net Satış (KDV Hariç)', 0), errors='coerce') or 0
            eb = pd.to_numeric(r.get('Mağaza Kar/Zararı', 0), errors='coerce') or 0
            smm = abs(pd.to_numeric(r.get('SMM', 0), errors='coerce') or 0)
            iade = abs(pd.to_numeric(r.get('Satış İade ve İskontoları', 0), errors='coerce') or 0)
            brut = pd.to_numeric(r.get('Brüt Satış', 0), errors='coerce') or 0
            env = abs(pd.to_numeric(r.get('Envanter Kaybı Mağaza', 0), errors='coerce') or 0)
            
            row[f'{p}NetSatis'] = ns
            row[f'{p}EBITDA'] = eb
            row[f'{p}EBITDA_Oran'] = safe_div(eb, ns)
            row[f'{p}SMM_Oran'] = safe_div(smm, ns)
            row[f'{p}Iade_Oran'] = safe_div(iade, brut) if brut > 0 else 0
            row[f'{p}Env_Oran'] = safe_div(env, ns)
            
            for gider_key, gider_cfg in GIDER_RULES.items():
                col = gider_cfg['col']
                val = abs(pd.to_numeric(r.get(col, 0), errors='coerce') or 0)
                row[f'{p}{gider_key}_TL'] = val
                row[f'{p}{gider_key}_Oran'] = safe_div(val, ns)
        
        results.append(row)
    
    rdf = pd.DataFrame(results)
    n = len(donemler)
    
    if f'D{n}_EBITDA_Oran' not in rdf.columns:
        return None, None, "EBITDA Oran hesaplanamadı"
    
    med = rdf[f'D{n}_EBITDA_Oran'].median()
    rdf['Seviye'] = rdf[f'D{n}_EBITDA_Oran'] - med
    
    if n >= 2 and f'D{n-1}_EBITDA_Oran' in rdf.columns:
        rdf['Trend'] = rdf[f'D{n}_EBITDA_Oran'] - rdf[f'D{n-1}_EBITDA_Oran']
    else:
        rdf['Trend'] = 0
    
    rdf['Skor'] = rdf['Seviye'] + rdf['Trend'] * 1.5
    
    def kat(r):
        if n >= 3 and r.get('D2_EBITDA', 0) < 0 and r.get('D3_EBITDA', 0) < 0:
            return '🔥 Yangın'
        if r['Skor'] >= 0: return '🟩 Başarılı'
        if r['Skor'] >= -1: return '🟧 Dikkat'
        if r['Skor'] >= -2.5: return '🟥 Kritik'
        return '🚨 Acil'
    
    rdf['Kategori'] = rdf.apply(kat, axis=1)
    
    return rdf, {'donemler': donemler, 'n': n, 'med': med}, None


# === 4 AJAN ANALİZİ - GÜÇLENDİRİLMİŞ GELİR AJANI ===
def ajan_analiz(row, info):
    n = info['n']
    d1, d2 = (f'D{n-1}_', f'D{n}_') if n >= 2 else ('D1_', 'D2_')
    
    result = {
        'ebitda': {'alarm': False, 'mesaj': '', 'detay': []},
        'gelir': {'problemler': [], 'ok': [], 'ciro_erozyon': False, 'tasima_gucu': None},
        'gider': {'problemler': [], 'ok': []},
        'envanter': {'durum': '', 'karsilik': ''},
        'hukum': {'etiket': '', 'tip': '', 'aksiyon': []}
    }
    
    # === 1. EBITDA AJANI ===
    eb1 = row.get(f'{d1}EBITDA_Oran', 0) or 0
    eb2 = row.get(f'{d2}EBITDA_Oran', 0) or 0
    eb_trend = eb2 - eb1
    
    if n >= 3:
        eb0 = row.get('D1_EBITDA_Oran', 0) or 0
        if eb2 < eb1 < eb0 and (eb0 - eb2) >= 1:
            result['ebitda']['alarm'] = True
            result['ebitda']['mesaj'] = f"SESSİZ BOZULMA: %{eb0:.1f} → %{eb1:.1f} → %{eb2:.1f}"
    
    if eb_trend < -1:
        result['ebitda']['alarm'] = True
        result['ebitda']['detay'].append(f"EBITDA: %{eb1:.1f} → %{eb2:.1f}")
    
    # === 2. GELİR AJANI - GÜÇLENDİRİLMİŞ ===
    ns1 = row.get(f'{d1}NetSatis', 0) or 0
    ns2 = row.get(f'{d2}NetSatis', 0) or 0
    ns_pct = safe_pct(ns2, ns1)
    
    # 3 ay verisi varsa monoton kontrol
    if n >= 3:
        ns0 = row.get('D1_NetSatis', 0) or 0
        monotonic_down = ns2 < ns1 < ns0
    else:
        monotonic_down = False
    
    # Sabit Gider Hesabı (Kira + Amortisman + Sigorta + Aidat)
    sabit_tl1 = (row.get(f'{d1}Kira_TL', 0) or 0) + (row.get(f'{d1}Amortisman_TL', 0) or 0) + \
                (row.get(f'{d1}Sigorta_TL', 0) or 0) + (row.get(f'{d1}Aidat_TL', 0) or 0)
    sabit_tl2 = (row.get(f'{d2}Kira_TL', 0) or 0) + (row.get(f'{d2}Amortisman_TL', 0) or 0) + \
                (row.get(f'{d2}Sigorta_TL', 0) or 0) + (row.get(f'{d2}Aidat_TL', 0) or 0)
    
    sabit_oran1 = safe_div(sabit_tl1, ns1)
    sabit_oran2 = safe_div(sabit_tl2, ns2)
    
    # Sabit gider TL değişimi
    sabit_tl_degisim = abs(sabit_tl2 - sabit_tl1) / max(sabit_tl1, 1)
    sabit_tl_sabit = sabit_tl_degisim < GELIR_RULES['SabitGider_TL']['rel']  # %2'den az
    
    # Sabit gider oran artışı
    sabit_oran_artis = (sabit_oran2 - sabit_oran1) >= GELIR_RULES['SabitGider_Oran']['abs']  # 0.30 puan
    
    # Taşıma Gücü Hesabı
    # Katkı Marjı = Net Satış - Değişken Gider (SMM + Personel)
    degisken1 = (row.get(f'{d1}SMM_Oran', 0) or 0) * ns1 / 100 + (row.get(f'{d1}Personel_TL', 0) or 0)
    degisken2 = (row.get(f'{d2}SMM_Oran', 0) or 0) * ns2 / 100 + (row.get(f'{d2}Personel_TL', 0) or 0)
    
    katki_marji2 = ns2 - degisken2
    tasima_gucu = katki_marji2 / sabit_tl2 if sabit_tl2 > 0 else 99
    result['gelir']['tasima_gucu'] = tasima_gucu
    
    # CİRO EROZYONU KARARI
    ciro_erozyon = False
    erozyon_nedenleri = []
    
    # A) Seviye Erozyonu
    if ns_pct <= GELIR_RULES['NetSatis']['level_drop'] * 100:  # -8%
        ciro_erozyon = True
        erozyon_nedenleri.append(f"Seviye: {ns_pct:+.0f}%")
    
    # B) Yapısal Erozyon (3 ay monoton düşüş)
    if monotonic_down:
        ciro_erozyon = True
        erozyon_nedenleri.append(f"Yapısal: {fmt(ns0)}→{fmt(ns1)}→{fmt(ns2)}")
    
    # C) Taşıma Gücü Bozulması
    if sabit_tl_sabit and sabit_oran_artis:
        ciro_erozyon = True
        erozyon_nedenleri.append(f"Taşıma: SabitTL aynı ({fmt(sabit_tl1)}→{fmt(sabit_tl2)}), oran +{sabit_oran2-sabit_oran1:.1f}p")
    
    # D) Taşıma Gücü Kritik
    if tasima_gucu < 1.0:
        ciro_erozyon = True
        erozyon_nedenleri.append(f"Taşıma Gücü: {tasima_gucu:.2f} (<1.0 KRİTİK)")
    
    result['gelir']['ciro_erozyon'] = ciro_erozyon
    
    # Gelir Problemleri
    if ciro_erozyon:
        result['gelir']['problemler'].append(f"📉 CİRO EROZYONU: {fmt(ns1)}→{fmt(ns2)} ({ns_pct:+.0f}%)")
        for neden in erozyon_nedenleri[:2]:
            result['gelir']['problemler'].append(f"   └ {neden}")
    elif ns_pct < -5:
        result['gelir']['problemler'].append(f"📉 Ciro: {fmt(ns1)}→{fmt(ns2)} ({ns_pct:+.0f}%)")
    else:
        result['gelir']['ok'].append(f"Ciro: {ns_pct:+.0f}%")
    
    # SMM kontrolü
    smm1 = row.get(f'{d1}SMM_Oran', 0) or 0
    smm2 = row.get(f'{d2}SMM_Oran', 0) or 0
    smm_delta = smm2 - smm1
    if smm_delta > GELIR_RULES['SMM']['abs']:
        result['gelir']['problemler'].append(f"🏭 SMM: %{smm1:.1f}→%{smm2:.1f} (+{smm_delta:.1f}p)")
    
    # İade kontrolü
    iade1 = row.get(f'{d1}Iade_Oran', 0) or 0
    iade2 = row.get(f'{d2}Iade_Oran', 0) or 0
    iade_delta = iade2 - iade1
    if iade_delta > GELIR_RULES['Iade']['abs']:
        result['gelir']['problemler'].append(f"↩️ İade: %{iade1:.2f}→%{iade2:.2f}")
    
    # === 3. GİDER AJANI ===
    for gider_key, gider_cfg in GIDER_RULES.items():
        oran1 = row.get(f'{d1}{gider_key}_Oran', 0) or 0
        oran2 = row.get(f'{d2}{gider_key}_Oran', 0) or 0
        tl1 = row.get(f'{d1}{gider_key}_TL', 0) or 0
        tl2 = row.get(f'{d2}{gider_key}_TL', 0) or 0
        
        delta_abs = oran2 - oran1
        delta_rel = (oran2 / max(oran1, 0.01)) - 1 if oran1 > 0 else 0
        
        bozuk = (delta_abs >= gider_cfg['abs'] or delta_rel >= gider_cfg['rel']) and tl2 >= gider_cfg['min_tl']
        
        if bozuk and delta_abs > 0:
            # Sabit gider + ciro erozyonu varsa, gideri suçlama
            if gider_key in ['Kira', 'Amortisman', 'Sigorta', 'Aidat']:
                tl_degisim = abs(tl2 - tl1) / max(tl1, 1) if tl1 > 0 else 0
                if tl_degisim < 0.05 and ciro_erozyon:
                    # TL değişmemiş, sadece ciro düşünce oran arttı - GİDER SUÇLANMAZ
                    continue
            
            tip = "AKUT"
            if n >= 3:
                oran0 = row.get(f'D1_{gider_key}_Oran', 0) or 0
                if oran1 > oran0 * 1.1:
                    tip = "YAPISAL"
            
            if delta_rel > 1:
                result['gider']['problemler'].append(f"🔴 {gider_key}: %{oran1:.2f}→%{oran2:.2f} ({fmt(tl1)}→{fmt(tl2)}) +{delta_rel*100:.0f}% {tip}")
            else:
                result['gider']['problemler'].append(f"🔴 {gider_key}: %{oran1:.2f}→%{oran2:.2f} ({fmt(tl1)}→{fmt(tl2)}) +{delta_abs:.2f}p {tip}")
    
    if not result['gider']['problemler']:
        result['gider']['ok'].append("Tüm giderler normal")
    
    # === 4. ENVANTER AJANI ===
    env1 = row.get(f'{d1}Env_Oran', 0) or 0
    env2 = row.get(f'{d2}Env_Oran', 0) or 0
    env_delta = env2 - env1
    env_tl1 = ns1 * env1 / 100 if ns1 > 0 else 0
    env_tl2 = ns2 * env2 / 100 if ns2 > 0 else 0
    
    if env_delta < -0.2:
        result['envanter']['durum'] = f"✅ İYİLEŞTİ: %{env1:.2f}→%{env2:.2f} ({fmt(env_tl1)}→{fmt(env_tl2)})"
        if result['gider']['problemler']:
            result['envanter']['karsilik'] = "Gider artışı KARŞILIKLI"
    elif env_delta > GELIR_RULES['Envanter']['abs']:
        result['envanter']['durum'] = f"🔴 BOZULDU: %{env1:.2f}→%{env2:.2f} ({fmt(env_tl1)}→{fmt(env_tl2)})"
        result['envanter']['karsilik'] = "KARŞILIKSIZ"
    else:
        result['envanter']['durum'] = f"➖ STABİL: %{env2:.2f} ({fmt(env_tl2)})"
        if result['gider']['problemler']:
            result['envanter']['karsilik'] = "Gider artışı KARŞILIKSIZ"
    
    # === NİHAİ HÜKÜM ===
    gelir_problem = len(result['gelir']['problemler']) > 0
    gider_problem = len(result['gider']['problemler']) > 0
    
    if ciro_erozyon and not gider_problem:
        result['hukum']['tip'] = "CİRO_EROZYONU"
    elif ciro_erozyon and gider_problem:
        result['hukum']['tip'] = "KARISIK"
    elif gelir_problem and gider_problem:
        result['hukum']['tip'] = "KARISIK"
    elif gelir_problem:
        result['hukum']['tip'] = "MARJ_KAYNAKLI" if any('SMM' in p for p in result['gelir']['problemler']) else "SATIS_KAYNAKLI"
    elif gider_problem:
        result['hukum']['tip'] = "GIDER_KAYNAKLI"
    else:
        result['hukum']['tip'] = "NORMAL"
    
    if result['hukum']['tip'] != "NORMAL":
        if ciro_erozyon:
            result['hukum']['aksiyon'].append("• Ciro erozyonu kaynağını araştır")
            if tasima_gucu < 1.2:
                result['hukum']['aksiyon'].append(f"• Taşıma gücü kritik ({tasima_gucu:.2f})")
        if any('SMM' in p for p in result['gelir']['problemler']):
            result['hukum']['aksiyon'].append("• Tedarikçi/fiyat revizyonu")
        if any('Personel' in p for p in result['gider']['problemler']):
            result['hukum']['aksiyon'].append("• Vardiya optimizasyonu")
        if any('Elektrik' in p for p in result['gider']['problemler']):
            result['hukum']['aksiyon'].append("• Enerji tüketimi kontrol")
        if any('Temizlik' in p for p in result['gider']['problemler']):
            result['hukum']['aksiyon'].append("• Temizlik sözleşmesi kontrol")
    
    return result


def get_sm_gider_profil(df, sm, n):
    sm_df = df[df['SM'] == sm]
    if len(sm_df) < 3:
        return []
    
    profil = []
    for gider_key, gider_cfg in GIDER_RULES.items():
        if gider_key == 'Toplam':
            continue
        col = f'D{n}_{gider_key}_Oran'
        if col not in df.columns:
            continue
        
        bolge_med = df[col].median()
        esik = bolge_med + gider_cfg['abs']
        yuksek = sm_df[sm_df[col] > esik]
        oran = len(yuksek) / len(sm_df) if len(sm_df) > 0 else 0
        
        if oran >= 0.30:
            tip = "AKUT"
            if n >= 3:
                col_prev = f'D{n-1}_{gider_key}_Oran'
                if col_prev in df.columns:
                    prev_yuksek = sm_df[sm_df[col_prev] > bolge_med + gider_cfg['abs']]
                    if len(prev_yuksek) / len(sm_df) >= 0.25:
                        tip = "YAPISAL"
            profil.append({
                'kalem': gider_key, 
                'oran': oran, 
                'tip': tip,
                'magazalar': yuksek['Magaza_Isim'].head(3).tolist()
            })
    
    return sorted(profil, key=lambda x: x['oran'], reverse=True)


def get_bs_gider_profil(df, sm, bs, n):
    bs_df = df[(df['SM'] == sm) & (df['BS'] == bs)]
    if len(bs_df) < 2:
        return []
    
    profil = []
    for gider_key, gider_cfg in GIDER_RULES.items():
        if gider_key == 'Toplam':
            continue
        col = f'D{n}_{gider_key}_Oran'
        if col not in df.columns:
            continue
        
        bolge_med = df[col].median()
        esik = bolge_med + gider_cfg['abs']
        yuksek = bs_df[bs_df[col] > esik]
        oran = len(yuksek) / len(bs_df) if len(bs_df) > 0 else 0
        
        if oran >= 0.30 and len(yuksek) >= 2:
            tip = "AKUT"
            if n >= 3:
                col_prev = f'D{n-1}_{gider_key}_Oran'
                if col_prev in df.columns:
                    prev_yuksek = bs_df[bs_df[col_prev] > bolge_med + gider_cfg['abs']]
                    if len(prev_yuksek) / len(bs_df) >= 0.25:
                        tip = "YAPISAL"
            profil.append({
                'kalem': gider_key, 
                'oran': oran, 
                'tip': tip
            })
    
    return sorted(profil, key=lambda x: x['oran'], reverse=True)


# === MAIN ===
def main():
    st.markdown('<div class="main-header"><h1>🎯 EBITDA Karar Motoru</h1><p>4 Ajanlı Analiz | EBITDA • Gelir • Gider • Envanter</p></div>', unsafe_allow_html=True)
    
    f = st.file_uploader("Excel yükle", type=['xlsx'], label_visibility="collapsed")
    
    if f:
        rdf, info, err = load_data(f)
        if err:
            st.error(err)
            return
        if rdf is None or info is None:
            st.error("Veri yüklenemedi")
            return
        st.session_state.data = rdf
        st.session_state.info = info
    
    if 'data' not in st.session_state or st.session_state.data is None:
        st.info("📁 EBITDA Excel dosyası yükleyin")
        return
    
    if 'info' not in st.session_state or st.session_state.info is None:
        st.error("Veri bilgisi eksik, dosyayı tekrar yükleyin")
        return
    
    df = st.session_state.data
    info = st.session_state.info
    donemler, n, med = info['donemler'], info['n'], info['med']
    dk = [d.split()[0][:3] for d in donemler]
    
    # === ÖZET ===
    kritik = len(df[df['Kategori'].isin(['🚨 Acil', '🔥 Yangın'])])
    gizli = len(df[(df['Kategori'].isin(['🟧 Dikkat', '🟥 Kritik'])) & (df[f'D{n}_EBITDA'] > 0)])
    st.markdown(f'<div class="karar-box">💡 **{kritik} mağaza** acil/yangın | **{gizli} mağaza** kâr ediyor ama bozuluyor</div>', unsafe_allow_html=True)
    
    # === BÖLGE TREND ===
    st.subheader("📊 Bölge Trendi")
    cols = st.columns(n)
    for i, (col, d) in enumerate(zip(cols, donemler)):
        eb = df[f'D{i+1}_EBITDA'].sum()
        ns = df[f'D{i+1}_NetSatis'].sum()
        o = safe_div(eb, ns)
        with col:
            delta = ""
            if i > 0:
                prv = df[f'D{i}_EBITDA'].sum()
                pct = safe_pct(eb, prv)
                delta = f"<br><small style='color:{'#dc2626' if pct<0 else '#059669'}'>{fmt(eb-prv)} ({pct:+.1f}%)</small>"
            st.markdown(f'<div class="metric-card"><div class="metric-label">{d}</div><div class="metric-value">{fmt(eb)}</div><div>%{o:.1f}</div>{delta}</div>', unsafe_allow_html=True)
    
    st.caption(f"Medyan: **%{med:.1f}** | **{len(df)} mağaza**")
    
    # === KATEGORİ ===
    st.markdown("---")
    st.subheader("📦 Kategoriler")
    kats = ['🔥 Yangın', '🚨 Acil', '🟥 Kritik', '🟧 Dikkat', '🟩 Başarılı']
    cols = st.columns(5)
    for i, (k, col) in enumerate(zip(kats, cols)):
        s = len(df[df['Kategori'] == k])
        with col:
            if st.button(f"{k}\n{s}", key=f"k{i}", use_container_width=True):
                st.session_state.sel_kat = k
    
    if 'sel_kat' in st.session_state and st.session_state.sel_kat:
        k = st.session_state.sel_kat
        kdf = df[df['Kategori'] == k].copy()
        
        # === FİLTRELER ===
        st.markdown("#### 🔍 Filtreler")
        fcol1, fcol2, fcol3 = st.columns(3)
        
        with fcol1:
            sm_list = ['Tümü'] + sorted(kdf['SM'].unique().tolist())
            sel_sm = st.selectbox("SM", sm_list, key="filter_sm")
        
        with fcol2:
            if sel_sm != 'Tümü':
                bs_list = ['Tümü'] + sorted(kdf[kdf['SM'] == sel_sm]['BS'].unique().tolist())
            else:
                bs_list = ['Tümü'] + sorted(kdf['BS'].unique().tolist())
            sel_bs = st.selectbox("BS", bs_list, key="filter_bs")
        
        with fcol3:
            magaza_list = ['Tümü']
            if sel_sm != 'Tümü' and sel_bs != 'Tümü':
                magaza_list += sorted(kdf[(kdf['SM'] == sel_sm) & (kdf['BS'] == sel_bs)]['Magaza_Isim'].unique().tolist())
            elif sel_sm != 'Tümü':
                magaza_list += sorted(kdf[kdf['SM'] == sel_sm]['Magaza_Isim'].unique().tolist())
            elif sel_bs != 'Tümü':
                magaza_list += sorted(kdf[kdf['BS'] == sel_bs]['Magaza_Isim'].unique().tolist())
            else:
                magaza_list += sorted(kdf['Magaza_Isim'].unique().tolist())
            sel_magaza = st.selectbox("Mağaza", magaza_list, key="filter_magaza")
        
        # Filtre uygula
        if sel_sm != 'Tümü':
            kdf = kdf[kdf['SM'] == sel_sm]
        if sel_bs != 'Tümü':
            kdf = kdf[kdf['BS'] == sel_bs]
        if sel_magaza != 'Tümü':
            kdf = kdf[kdf['Magaza_Isim'] == sel_magaza]
        
        kdf = kdf.sort_values('Skor')
        
        st.markdown(f"### {k} ({len(kdf)} mağaza)")
        
        for _, row in kdf.iterrows():
            analiz = ajan_analiz(row, info)
            tum_prob = analiz['gelir']['problemler'] + analiz['gider']['problemler']
            prob_str = " | ".join([p.split(':')[0].replace('🔴','').replace('📉','').replace('🏭','').replace('   └','').strip() for p in tum_prob[:2]]) if tum_prob else "Normal"
            
            with st.expander(f"**{row['Magaza_Isim']}** | {row['SM']}/{row['BS']} | Skor:{row['Skor']:.1f} | {prob_str}"):
                if n == 3:
                    st.markdown(f"**EBITDA:** {dk[0]} %{row.get('D1_EBITDA_Oran',0):.1f} → {dk[1]} %{row.get('D2_EBITDA_Oran',0):.1f} → {dk[2]} %{row.get('D3_EBITDA_Oran',0):.1f}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f'<div class="ajan-box ajan-ebitda"><div class="ajan-title">1️⃣ EBITDA</div>{"🔴 ALARM" if analiz["ebitda"]["alarm"] else "✅ Normal"}<br><small>{analiz["ebitda"]["mesaj"]}</small></div>', unsafe_allow_html=True)
                    gider_html = " ".join([f'<span class="problem-item">{p}</span>' for p in analiz['gider']['problemler'][:4]]) or '<span class="ok-item">✅ Normal</span>'
                    st.markdown(f'<div class="ajan-box ajan-gider"><div class="ajan-title">3️⃣ GİDER</div>{gider_html}</div>', unsafe_allow_html=True)
                
                with col2:
                    gelir_html = ""
                    for p in analiz['gelir']['problemler']:
                        if '└' in p:
                            gelir_html += f'<div style="font-size:0.75rem;color:#666;margin-left:10px">{p}</div>'
                        else:
                            gelir_html += f'<span class="problem-item">{p}</span> '
                    if not gelir_html:
                        gelir_html = '<span class="ok-item">✅ Normal</span>'
                    
                    tasima = analiz['gelir'].get('tasima_gucu')
                    tasima_str = f"<br><small>Taşıma Gücü: {tasima:.2f}</small>" if tasima and tasima < 2 else ""
                    st.markdown(f'<div class="ajan-box ajan-gelir"><div class="ajan-title">2️⃣ GELİR</div>{gelir_html}{tasima_str}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="ajan-box ajan-envanter"><div class="ajan-title">4️⃣ ENVANTER</div>{analiz["envanter"]["durum"]}<br><small>{analiz["envanter"]["karsilik"]}</small></div>', unsafe_allow_html=True)
                
                if analiz['hukum']['tip'] != 'NORMAL':
                    aksiyon_html = "<br>".join(analiz['hukum']['aksiyon'])
                    st.markdown(f'<div class="hukum-box"><strong>📋 HÜKÜM: {analiz["hukum"]["tip"]}</strong><br><small>{aksiyon_html}</small></div>', unsafe_allow_html=True)
    
    # === SM PERFORMANS ===
    st.markdown("---")
    st.subheader("👥 SM Performans (Kötüden İyiye)")
    
    sm_agg = {f'D{i}_EBITDA': 'sum' for i in range(1, n+1)}
    sm_agg.update({f'D{i}_NetSatis': 'sum' for i in range(1, n+1)})
    sm_agg['Kod'] = 'count'
    smdf = df.groupby('SM').agg(sm_agg).reset_index()
    smdf = smdf[smdf['Kod'] > 2]
    
    for i in range(1, n+1):
        smdf[f'D{i}_O'] = (smdf[f'D{i}_EBITDA'] / smdf[f'D{i}_NetSatis'] * 100).fillna(0)
    
    for kat in kats:
        for sm in smdf['SM'].unique():
            smdf.loc[smdf['SM'] == sm, kat] = len(df[(df['SM'] == sm) & (df['Kategori'] == kat)])
    
    smdf['KT'] = smdf.get('🔥 Yangın', 0) + smdf.get('🚨 Acil', 0) + smdf.get('🟥 Kritik', 0)
    smdf = smdf.sort_values('KT', ascending=False)
    
    for _, sr in smdf.iterrows():
        sm = sr['SM']
        ko = " ".join([f"{kat.split()[0]}{int(sr.get(kat,0))}" for kat in kats if sr.get(kat,0) > 0])
        gider_profil = get_sm_gider_profil(df, sm, n)
        
        if n == 3:
            p1 = safe_pct(sr['D2_O'], sr['D1_O'])
            p2 = safe_pct(sr['D3_O'], sr['D2_O'])
            tr = f"{dk[0]} %{sr['D1_O']:.1f} → {dk[1]} %{sr['D2_O']:.1f} ({'↓' if p1<0 else '↑'}{abs(p1):.0f}%) → {dk[2]} %{sr['D3_O']:.1f} ({'↓' if p2<0 else '↑'}{abs(p2):.0f}%)"
        else:
            tr = f"{dk[0]} %{sr['D1_O']:.1f} → {dk[1]} %{sr['D2_O']:.1f}"
        
        with st.expander(f"**{sm}** ({int(sr['Kod'])} mğz) | {ko}"):
            st.markdown(f"**{fmt(sr[f'D{n}_EBITDA'])}** | {tr}")
            
            if gider_profil:
                profil_parts = []
                for p in gider_profil[:3]:
                    profil_parts.append(f"{p['kalem']} %{p['oran']*100:.0f} {p['tip']}")
                st.markdown(f'<div class="sm-alert">⚠️ {" | ".join(profil_parts)}</div>', unsafe_allow_html=True)
                for p in gider_profil[:2]:
                    if p.get('magazalar'):
                        st.caption(f"  └ {p['kalem']}: {', '.join(p['magazalar'][:3])}")
            
            st.markdown("---")
            st.markdown("**👔 Bölge Sorumluları:**")
            
            bs_list = []
            for bs in df[df['SM'] == sm]['BS'].unique():
                if not bs:
                    continue
                bt = df[(df['SM'] == sm) & (df['BS'] == bs)]
                bs_oranlar = [safe_div(bt[f'D{i}_EBITDA'].sum(), bt[f'D{i}_NetSatis'].sum()) for i in range(1, n+1)]
                bs_kritik = len(bt[bt['Kategori'].isin(['🔥 Yangın', '🚨 Acil', '🟥 Kritik'])])
                bs_list.append({
                    'bs': bs,
                    'count': len(bt),
                    'ebitda': bt[f'D{n}_EBITDA'].sum(),
                    'oranlar': bs_oranlar,
                    'kritik': bs_kritik,
                    'df': bt
                })
            
            bs_list = sorted(bs_list, key=lambda x: x['kritik'], reverse=True)
            
            for b in bs_list:
                if n == 3:
                    q1 = safe_pct(b['oranlar'][1], b['oranlar'][0])
                    q2 = safe_pct(b['oranlar'][2], b['oranlar'][1])
                    btr = f"{dk[0]} %{b['oranlar'][0]:.1f} → {dk[1]} %{b['oranlar'][1]:.1f} ({'↓' if q1<0 else '↑'}{abs(q1):.0f}%) → {dk[2]} %{b['oranlar'][2]:.1f} ({'↓' if q2<0 else '↑'}{abs(q2):.0f}%)"
                else:
                    btr = f"{dk[0]} %{b['oranlar'][0]:.1f} → {dk[1]} %{b['oranlar'][1]:.1f}"
                
                bs_gider = get_bs_gider_profil(df, sm, b['bs'], n)
                
                with st.expander(f"📁 {b['bs']} ({b['count']} mğz) | {fmt(b['ebitda'])} | {btr}"):
                    if bs_gider:
                        bs_gider_str = " | ".join([f"{g['kalem']} %{g['oran']*100:.0f} {g['tip']}" for g in bs_gider[:3]])
                        st.markdown(f'<div class="sm-alert">⚠️ {bs_gider_str}</div>', unsafe_allow_html=True)
                    
                    km = b['df'][b['df']['Kategori'].isin(['🔥 Yangın', '🚨 Acil', '🟥 Kritik'])].sort_values('Skor')
                    
                    if len(km) > 0:
                        st.markdown("**⚠️ Dikkat Gerektiren:**")
                        for _, m in km.iterrows():
                            ma = ajan_analiz(m, info)
                            prob = " | ".join([p.split(':')[0].replace('🔴','').replace('📉','').replace('🏭','').replace('   └','').strip() for p in (ma['gelir']['problemler'] + ma['gider']['problemler'])[:2]]) or "Bozulma"
                            
                            with st.expander(f"• {m['Magaza_Isim']} | {m['Kategori']} | Skor:{m['Skor']:.1f} | {prob}"):
                                if n == 3:
                                    st.markdown(f"**Trend:** {dk[0]} %{m.get('D1_EBITDA_Oran',0):.1f} → {dk[1]} %{m.get('D2_EBITDA_Oran',0):.1f} → {dk[2]} %{m.get('D3_EBITDA_Oran',0):.1f}")
                                
                                st.markdown("**Problemler:**")
                                for p in ma['gelir']['problemler']:
                                    st.markdown(f"- {p}")
                                for p in ma['gider']['problemler'][:4]:
                                    st.markdown(f"- {p}")
                                
                                st.markdown(f"**Envanter:** {ma['envanter']['durum']}")
                                if ma['envanter']['karsilik']:
                                    st.caption(ma['envanter']['karsilik'])
                                
                                if ma['hukum']['aksiyon']:
                                    st.markdown("**Aksiyon:**")
                                    for a in ma['hukum']['aksiyon']:
                                        st.markdown(a)
                    else:
                        st.success("✅ Kritik mağaza yok")
    
    # === GİZLİ TEHLİKE ===
    st.markdown("---")
    st.subheader("⚠️ Gizli Tehlike: Kârlı ama Düşenler")
    
    gizli_df = df[(df[f'D{n}_EBITDA'] > 0) & (df['Kategori'].isin(['🟧 Dikkat', '🟥 Kritik']))].sort_values('Skor').head(10)
    
    if len(gizli_df) > 0:
        st.warning(f"{len(gizli_df)} mağaza kâr ediyor ama hızla bozuluyor!")
        for _, row in gizli_df.iterrows():
            analiz = ajan_analiz(row, info)
            prob = " | ".join([p.split(':')[0].replace('🔴','').replace('   └','').strip() for p in (analiz['gelir']['problemler'] + analiz['gider']['problemler'])[:2]]) or "Bozulma"
            
            with st.expander(f"**{row['Magaza_Isim']}** | {row['Kategori']} | {fmt(row[f'D{n}_EBITDA'])} | {prob}"):
                for p in analiz['gelir']['problemler']:
                    st.markdown(f"- {p}")
                for p in analiz['gider']['problemler'][:3]:
                    st.markdown(f"- {p}")
    else:
        st.success("✅ Gizli tehlike yok")
    
    # === EXPORT ===
    st.markdown("---")
    out = BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as w:
        df.to_excel(w, sheet_name='TÜM', index=False)
        for kat in kats:
            katdf = df[df['Kategori'] == kat]
            if len(katdf) > 0:
                katdf.to_excel(w, sheet_name=kat.split()[1][:10], index=False)
    st.download_button("📥 Excel İndir", data=out.getvalue(), file_name=f"EBITDA_4Ajan_{donemler[-1].replace(' ','_')}.xlsx")


if __name__ == "__main__":
    main()
