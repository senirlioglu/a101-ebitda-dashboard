import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# page config removed for super app

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
    "Ambalaj": {"col": "Ambalaj Giderleri", "abs": 0.05, "rel": 0.30, "min_tl": 500},
    "Sigorta": {"col": "Sigorta Giderleri", "abs": 0.03, "rel": 0.20, "min_tl": 0},
    "Banka": {"col": "Banka Para Toplama Giderleri", "abs": 0.03, "rel": 0.30, "min_tl": 300},
    "Belediye": {"col": "Belediye Vergiler", "abs": 0.03, "rel": 0.30, "min_tl": 300},
    "Diger": {"col": "Diğer Giderler", "abs": 0.05, "rel": 0.50, "min_tl": 500},
    "Toplam": {"col": "Toplam Mağaza Giderleri", "abs": 0.50, "rel": 0.10, "min_tl": 0},
}

GELIR_RULES = {
    "NetSatis": {"level_drop": -0.08},
    "SMM": {"abs": 1.0},
    "Iade": {"abs": 0.3},
    "Envanter": {"abs": 0.3},
    "SabitGider_Oran": {"abs": 0.30},
    "SabitGider_TL": {"rel": 0.02},
}

# === STYLE - run() içinde uygulanacak ===
EBITDA_CSS = """
<style>
    .stApp { background-color: #f8fafc; }
    .main-header { background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white; padding: 20px 24px; border-radius: 12px; margin-bottom: 24px; }
    .main-header h1 { margin: 0; font-size: 1.8rem; }

    .bolge-strateji {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        color: white;
        border: 2px solid #334155;
    }
    .bolge-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        flex-wrap: wrap;
        margin-bottom: 16px;
    }
    .bolge-hukum {
        font-size: 1.4rem;
        font-weight: 700;
        padding: 12px 16px;
        border-radius: 8px;
        display: inline-block;
    }
    .bolge-hukum-erozyon { background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); }
    .bolge-hukum-kalite { background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%); }
    .bolge-hukum-disiplin { background: linear-gradient(135deg, #ca8a04 0%, #a16207 100%); }
    .bolge-hukum-yapisal { background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%); }
    .bolge-hukum-normal { background: linear-gradient(135deg, #059669 0%, #047857 100%); }

    .bolge-grid {
        display: flex;
        gap: 8px;
        margin-top: 16px;
        flex-wrap: wrap;
    }
    .bolge-grid > div {
        flex: 1;
        min-width: 100px;
    }
    .bolge-metrik {
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .bolge-metrik-value { font-size: 1.5rem; font-weight: 700; }
    .bolge-metrik-label { font-size: 0.7rem; opacity: 0.8; text-transform: uppercase; margin-top: 4px; }
    .bolge-metrik-sub { font-size: 0.7rem; opacity: 0.6; }
    .bolge-metrik-bad { color: #fca5a5; }
    .bolge-metrik-warn { color: #fcd34d; }
    .bolge-metrik-ok { color: #86efac; }

    .bolge-neden { background: rgba(255,255,255,0.05); border-radius: 8px; padding: 12px; margin-top: 12px; }
    .bolge-neden-title { font-weight: 600; margin-bottom: 8px; }
    .bolge-kaldirac { background: rgba(34,197,94,0.2); border: 1px solid rgba(34,197,94,0.5); border-radius: 8px; padding: 12px; margin-top: 12px; }
    .bolge-kaldirac-title { font-weight: 600; margin-bottom: 8px; }
    .bolge-count { font-size: 2rem; font-weight: 700; text-align: right; }
    .bolge-count-label { font-size: 0.8rem; opacity: 0.7; text-align: right; }

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
</style>
"""

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


# === 4 AJAN ANALİZİ ===
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
    
    # === 2. GELİR AJANI ===
    ns1 = row.get(f'{d1}NetSatis', 0) or 0
    ns2 = row.get(f'{d2}NetSatis', 0) or 0
    ns_pct = safe_pct(ns2, ns1)
    
    if n >= 3:
        ns0 = row.get('D1_NetSatis', 0) or 0
        monotonic_down = ns2 < ns1 < ns0
    else:
        monotonic_down = False
    
    # Sabit Gider Hesabı
    sabit_tl1 = (row.get(f'{d1}Kira_TL', 0) or 0) + (row.get(f'{d1}Sigorta_TL', 0) or 0) + (row.get(f'{d1}Aidat_TL', 0) or 0)
    sabit_tl2 = (row.get(f'{d2}Kira_TL', 0) or 0) + (row.get(f'{d2}Sigorta_TL', 0) or 0) + (row.get(f'{d2}Aidat_TL', 0) or 0)
    
    sabit_oran1 = safe_div(sabit_tl1, ns1)
    sabit_oran2 = safe_div(sabit_tl2, ns2)
    
    sabit_tl_degisim = abs(sabit_tl2 - sabit_tl1) / max(sabit_tl1, 1)
    sabit_tl_sabit = sabit_tl_degisim < GELIR_RULES['SabitGider_TL']['rel']
    sabit_oran_artis = (sabit_oran2 - sabit_oran1) >= GELIR_RULES['SabitGider_Oran']['abs']
    
    # Taşıma Gücü
    degisken2 = (row.get(f'{d2}SMM_Oran', 0) or 0) * ns2 / 100 + (row.get(f'{d2}Personel_TL', 0) or 0)
    katki_marji2 = ns2 - degisken2
    tasima_gucu = katki_marji2 / sabit_tl2 if sabit_tl2 > 0 else 99
    result['gelir']['tasima_gucu'] = tasima_gucu
    
    # Ciro Erozyonu
    ciro_erozyon = False
    erozyon_nedenleri = []
    
    if ns_pct <= GELIR_RULES['NetSatis']['level_drop'] * 100:
        ciro_erozyon = True
        erozyon_nedenleri.append(f"Seviye: {ns_pct:+.0f}%")
    
    if monotonic_down:
        ciro_erozyon = True
        erozyon_nedenleri.append(f"Yapısal: {fmt(ns0)}→{fmt(ns1)}→{fmt(ns2)}")
    
    if sabit_tl_sabit and sabit_oran_artis:
        ciro_erozyon = True
        erozyon_nedenleri.append(f"Taşıma: SabitTL aynı, oran +{sabit_oran2-sabit_oran1:.1f}p")
    
    if tasima_gucu < 1.2:
        ciro_erozyon = True
        erozyon_nedenleri.append(f"Taşıma Gücü KRİTİK: {tasima_gucu:.2f}")
    
    result['gelir']['ciro_erozyon'] = ciro_erozyon
    
    if ciro_erozyon:
        result['gelir']['problemler'].append(f"📉 CİRO EROZYONU: {fmt(ns1)}→{fmt(ns2)} ({ns_pct:+.0f}%)")
        for neden in erozyon_nedenleri[:2]:
            result['gelir']['problemler'].append(f"   └ {neden}")
    elif ns_pct < -5:
        result['gelir']['problemler'].append(f"📉 Ciro: {fmt(ns1)}→{fmt(ns2)} ({ns_pct:+.0f}%)")
    
    smm1 = row.get(f'{d1}SMM_Oran', 0) or 0
    smm2 = row.get(f'{d2}SMM_Oran', 0) or 0
    smm_delta = smm2 - smm1
    if smm_delta > GELIR_RULES['SMM']['abs']:
        result['gelir']['problemler'].append(f"🏭 SMM: %{smm1:.1f}→%{smm2:.1f} (+{smm_delta:.1f}p)")
    
    # === 3. GİDER AJANI ===
    # Minimum etki eşiği: EBITDA'yı en az 0.5 puan etkilemeli
    min_etki_tl = ns2 * 0.005 if ns2 > 0 else 5000  # Cironun %0.5'i
    
    for gider_key, gider_cfg in GIDER_RULES.items():
        oran1 = row.get(f'{d1}{gider_key}_Oran', 0) or 0
        oran2 = row.get(f'{d2}{gider_key}_Oran', 0) or 0
        tl1 = row.get(f'{d1}{gider_key}_TL', 0) or 0
        tl2 = row.get(f'{d2}{gider_key}_TL', 0) or 0
        
        delta_abs = oran2 - oran1
        delta_rel = (oran2 / max(oran1, 0.01)) - 1 if oran1 > 0 else 0
        tl_artis = tl2 - tl1
        
        # MİNİMUM ETKİ: TL artışı EBITDA'yı en az 0.5p etkilemeli
        if tl_artis < min_etki_tl:
            continue
        
        bozuk = (delta_abs >= gider_cfg['abs'] or delta_rel >= gider_cfg['rel']) and tl2 >= gider_cfg['min_tl']
        
        if bozuk and delta_abs > 0:
            if gider_key in ['Kira', 'Sigorta', 'Aidat']:
                tl_degisim = abs(tl2 - tl1) / max(tl1, 1) if tl1 > 0 else 0
                if tl_degisim < 0.05 and ciro_erozyon:
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
    gider_problem = len(result['gider']['problemler']) > 0
    gelir_problem = len(result['gelir']['problemler']) > 0
    
    tasima_risk = tasima_gucu < 1.5
    tasima_kritik = tasima_gucu < 1.2
    tasima_yangin = tasima_gucu < 1.0
    
    # === 0. TEK SEFERLİK ŞOK GİDER TESPİTİ (EN ÖNCE) ===
    sok_giderler = []
    for gider_key in GIDER_RULES:
        if gider_key == 'Toplam':
            continue
        tl1 = row.get(f'{d1}{gider_key}_TL', 0) or 0
        tl2 = row.get(f'{d2}{gider_key}_TL', 0) or 0
        
        # 5x artış VE en az 50K TL = ŞOK
        if tl1 > 0 and tl2 / tl1 >= 5 and tl2 >= 50000:
            sok_giderler.append(f"{gider_key} ({fmt(tl1)}→{fmt(tl2)})")
    
    # Ciro stabil ama EBITDA çökmüşse ve şok gider varsa
    ciro_stabil = abs(ns_pct) < 5  # %5'ten az değişim
    ebitda_coktu = eb_trend < -5  # 5 puan düşüş
    
    if sok_giderler and ciro_stabil and ebitda_coktu:
        result['hukum']['tip'] = "TEK_SEFERLIK_GIDER_SOKU"
        result['hukum']['aksiyon'].append(f"• 🧨 Anormal gider: {', '.join(sok_giderler)}")
        result['hukum']['aksiyon'].append("• Muhasebe fişi / tahakkuk / ceza kontrolü")
        result['hukum']['aksiyon'].append("• Normalleştirilmiş EBITDA hesapla")
        result['hukum']['aksiyon'].append("• SM/BS suçlanmamalı")
        return result
    
    # === 1. CİRO EROZYONU ===
    if ciro_erozyon:
        result['hukum']['tip'] = "CİRO_EROZYONU"
        result['hukum']['aksiyon'].append("• Ciro erozyonu ana problem")
        if tasima_yangin:
            result['hukum']['aksiyon'].append(f"• 🔥 YANGIN: Taşıma gücü {tasima_gucu:.2f}")
        elif tasima_kritik:
            result['hukum']['aksiyon'].append(f"• ⚠️ KRİTİK: Taşıma gücü {tasima_gucu:.2f}")
        if gider_problem:
            result['hukum']['aksiyon'].append("• NOT: Gider oran artışı ciro düşüşünün SONUCU")
    
    # === 2. ENVANTER ===
    elif result['envanter']['durum'].startswith("🔴"):
        result['hukum']['tip'] = "ENVANTER_KAYNAKLI"
        result['hukum']['aksiyon'].append("• Envanter kaybı ana problem")
    
    # === 3. GİDER (sadece gerçek TL artışı varsa) ===
    elif gider_problem:
        result['hukum']['tip'] = "GIDER_KAYNAKLI"
        result['hukum']['aksiyon'].append("• Gider artışı ana problem")
    
    # === 4. SMM ===
    elif any('SMM' in p for p in result['gelir']['problemler']):
        result['hukum']['tip'] = "SATIS_KALITE_KAYBI"
        result['hukum']['aksiyon'].append("• SMM oranı bozulmuş")
    
    else:
        result['hukum']['tip'] = "NORMAL"
    
    return result


# === 5️⃣ BÖLGE STRATEJİ AJANI ===
def bolge_strateji_ajani(df, info):
    """
    Bölge düzeyinde tek ve net karar üretir.
    Mağaza bazlı sinyalleri toplar, oranlarla konuşur.
    """
    N = len(df)
    if N == 0:
        return None
    
    n = info['n']
    d1, d2 = (f'D{n-1}_', f'D{n}_') if n >= 2 else ('D1_', 'D2_')
    
    # Her mağaza için analiz yap ve sonuçları topla
    analizler = []
    for _, row in df.iterrows():
        a = ajan_analiz(row, info)
        
        # Gerçek gider artışı kontrolü (TL bazında)
        gercek_gider_artisi = False
        for gider_key in ['Personel', 'Elektrik', 'Temizlik', 'Toplam']:
            tl1 = row.get(f'{d1}{gider_key}_TL', 0) or 0
            tl2 = row.get(f'{d2}{gider_key}_TL', 0) or 0
            if tl1 > 0 and (tl2 - tl1) / tl1 > 0.10:  # %10+ TL artış
                gercek_gider_artisi = True
                break
        
        analizler.append({
            'ciro_erozyon': a['gelir']['ciro_erozyon'],
            'tasima_gucu': a['gelir']['tasima_gucu'] or 99,
            'envanter_bozuk': a['envanter']['durum'].startswith("🔴"),
            'gider_problem': len(a['gider']['problemler']) > 0,
            'gercek_gider_artisi': gercek_gider_artisi,
            'smm_problem': any('SMM' in p for p in a['gelir']['problemler']),
            'hukum_tip': a['hukum']['tip'],
            'kategori': row.get('Kategori', '')
        })
    
    adf = pd.DataFrame(analizler)
    
    # Bölgesel Metrikler
    ciro_erozyon_oran = adf['ciro_erozyon'].sum() / N
    env_karsiliksiz_oran = adf['envanter_bozuk'].sum() / N
    # Gider yoğunluk: sadece GERÇEK TL artışı olanlar
    gider_yogunluk_oran = adf['gercek_gider_artisi'].sum() / N
    tasima_kritik_oran = (adf['tasima_gucu'] < 1.2).sum() / N
    smm_problem_oran = adf['smm_problem'].sum() / N
    yangin_oran = adf['kategori'].isin(['🔥 Yangın', '🚨 Acil']).sum() / N
    
    metrikler = {
        'ciro_erozyon': {'oran': ciro_erozyon_oran, 'sayi': int(ciro_erozyon_oran * N)},
        'env_karsiliksiz': {'oran': env_karsiliksiz_oran, 'sayi': int(env_karsiliksiz_oran * N)},
        'gider_yogunluk': {'oran': gider_yogunluk_oran, 'sayi': int(gider_yogunluk_oran * N)},
        'tasima_kritik': {'oran': tasima_kritik_oran, 'sayi': int(tasima_kritik_oran * N)},
        'smm_problem': {'oran': smm_problem_oran, 'sayi': int(smm_problem_oran * N)},
        'yangin': {'oran': yangin_oran, 'sayi': int(yangin_oran * N)},
        'toplam': N
    }
    
    # === BÖLGE HÜKÜM MATRİSİ ===
    hukum = None
    nedenler = []
    kaldiraclar = []
    
    # 1. BÖLGESEL CİRO EROZYONU
    if ciro_erozyon_oran >= 0.40 and gider_yogunluk_oran >= 0.40:
        hukum = "BÖLGESEL CİRO EROZYONU"
        nedenler.append(f"Mağazaların %{ciro_erozyon_oran*100:.0f}'inde ciro erozyonu var ({metrikler['ciro_erozyon']['sayi']}/{N})")
        nedenler.append(f"Gider oranları %{gider_yogunluk_oran*100:.0f} mağazada yükselmiş - ama bu SONUÇ")
        nedenler.append("Sabit giderler TL bazında stabil, satış hacmi düşüyor")
        kaldiraclar.append("🎯 Satış hacmi artırıcı kampanya")
        kaldiraclar.append("📍 Lokasyon/trafik analizi")
        kaldiraclar.append("🏪 Rekabet haritası çıkar")
    
    # 2. SATIŞ KALİTE PROBLEMİ
    elif ciro_erozyon_oran < 0.30 and smm_problem_oran >= 0.30:
        hukum = "SATIŞ KALİTE KAYBI"
        nedenler.append(f"Mağazaların %{smm_problem_oran*100:.0f}'inde SMM oranı bozulmuş ({metrikler['smm_problem']['sayi']}/{N})")
        nedenler.append("Satış hacmi görece stabil ama marj eriyor")
        kaldiraclar.append("💰 Tedarikçi fiyat revizyonu")
        kaldiraclar.append("📊 Ürün mix analizi")
        kaldiraclar.append("🏷️ Fiyatlama stratejisi gözden geçir")
    
    # 3. SAHA DİSİPLİN PROBLEMİ
    elif env_karsiliksiz_oran >= 0.20:
        hukum = "SAHA DİSİPLİN PROBLEMİ"
        nedenler.append(f"Mağazaların %{env_karsiliksiz_oran*100:.0f}'inde envanter kaybı kritik ({metrikler['env_karsiliksiz']['sayi']}/{N})")
        nedenler.append("Bu satıştan bağımsız bir kontrol problemi")
        kaldiraclar.append("🔍 Sayım disiplini sıkılaştır")
        kaldiraclar.append("📹 Güvenlik/fire kontrolü")
        kaldiraclar.append("👥 BS bazlı sorumluluk ata")
    
    # 4. YAPISAL BÖLGE RİSKİ
    elif tasima_kritik_oran >= 0.25:
        hukum = "YAPISAL BÖLGE RİSKİ"
        nedenler.append(f"Mağazaların %{tasima_kritik_oran*100:.0f}'inde taşıma gücü <1.2 ({metrikler['tasima_kritik']['sayi']}/{N})")
        nedenler.append("Bu bölgenin mevcut ciro seviyesi gider yapısını taşıyamıyor")
        kaldiraclar.append("🏗️ Yapısal maliyet revizyonu")
        kaldiraclar.append("📉 Düşük performanslı mağaza kararı")
        kaldiraclar.append("💡 Kira yeniden müzakeresi")
    
    # 5. NORMAL
    else:
        hukum = "BÖLGE PERFORMANSI NORMAL"
        nedenler.append("Kritik eşiklerin altında")
        nedenler.append(f"Yangın/Acil oranı: %{yangin_oran*100:.0f}")
        kaldiraclar.append("✅ Mevcut stratejiyi sürdür")
        kaldiraclar.append("📈 Başarılı mağazaları ödüllendir")
    
    return {
        'hukum': hukum,
        'nedenler': nedenler,
        'kaldiraclar': kaldiraclar,
        'metrikler': metrikler
    }


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
            profil.append({'kalem': gider_key, 'oran': oran, 'tip': tip})
    
    return sorted(profil, key=lambda x: x['oran'], reverse=True)


# === MAIN ===
def run():
    # CSS uygula
    st.markdown(EBITDA_CSS, unsafe_allow_html=True)

    st.markdown('<div class="main-header"><h1>🎯 EBITDA Karar Motoru</h1><p>5 Ajanlı Sistem | Bölge Strateji • EBITDA • Gelir • Gider • Envanter</p></div>', unsafe_allow_html=True)
    
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
        st.error("Veri bilgisi eksik")
        return
    
    df = st.session_state.data
    info = st.session_state.info
    donemler, n, med = info['donemler'], info['n'], info['med']
    dk = [d.split()[0][:3] for d in donemler]
    
    # === 5️⃣ BÖLGE STRATEJİ AJANI - EN ÜSTTE ===
    bolge = bolge_strateji_ajani(df, info)
    
    if bolge:
        m = bolge['metrikler']
        
        # Hüküm rengini belirle
        hukum_class = "bolge-hukum-normal"
        if "EROZYON" in bolge['hukum']:
            hukum_class = "bolge-hukum-erozyon"
        elif "KALİTE" in bolge['hukum']:
            hukum_class = "bolge-hukum-kalite"
        elif "DİSİPLİN" in bolge['hukum']:
            hukum_class = "bolge-hukum-disiplin"
        elif "YAPISAL" in bolge['hukum']:
            hukum_class = "bolge-hukum-yapisal"
        
        # Metrik renkleri
        def mc(oran, w=0.20, b=0.35):
            if oran >= b: return "bolge-metrik-bad"
            if oran >= w: return "bolge-metrik-warn"
            return "bolge-metrik-ok"
        
        # Nedenler ve kaldıraçlar HTML
        nedenler_html = "".join([f"<div>• {nd}</div>" for nd in bolge['nedenler']])
        kaldirac_html = "".join([f"<div>{kd}</div>" for kd in bolge['kaldiraclar']])
        
        # Ana kart
        st.markdown(f'''<div class="bolge-strateji">
<div class="bolge-header">
<div>
<div class="bolge-metrik-sub">5️⃣ BÖLGE STRATEJİ AJANI</div>
<div class="bolge-hukum {hukum_class}">📍 {bolge['hukum']}</div>
</div>
<div>
<div class="bolge-count">{m['toplam']}</div>
<div class="bolge-count-label">MAĞAZA</div>
</div>
</div>
<div class="bolge-grid">
<div class="bolge-metrik">
<div class="bolge-metrik-value {mc(m['ciro_erozyon']['oran'], 0.25, 0.40)}">%{m['ciro_erozyon']['oran']*100:.0f}</div>
<div class="bolge-metrik-label">Ciro Erozyon</div>
<div class="bolge-metrik-sub">{m['ciro_erozyon']['sayi']} mğz</div>
</div>
<div class="bolge-metrik">
<div class="bolge-metrik-value {mc(m['tasima_kritik']['oran'], 0.15, 0.25)}">%{m['tasima_kritik']['oran']*100:.0f}</div>
<div class="bolge-metrik-label">Taşıma Kritik</div>
<div class="bolge-metrik-sub">{m['tasima_kritik']['sayi']} mğz</div>
</div>
<div class="bolge-metrik">
<div class="bolge-metrik-value {mc(m['env_karsiliksiz']['oran'], 0.10, 0.20)}">%{m['env_karsiliksiz']['oran']*100:.0f}</div>
<div class="bolge-metrik-label">Envanter Kritik</div>
<div class="bolge-metrik-sub">{m['env_karsiliksiz']['sayi']} mğz</div>
</div>
<div class="bolge-metrik">
<div class="bolge-metrik-value {mc(m['gider_yogunluk']['oran'], 0.30, 0.50)}">%{m['gider_yogunluk']['oran']*100:.0f}</div>
<div class="bolge-metrik-label">Gider Yoğunluk</div>
<div class="bolge-metrik-sub">{m['gider_yogunluk']['sayi']} mğz</div>
</div>
<div class="bolge-metrik">
<div class="bolge-metrik-value {mc(m['yangin']['oran'], 0.10, 0.20)}">%{m['yangin']['oran']*100:.0f}</div>
<div class="bolge-metrik-label">Yangın/Acil</div>
<div class="bolge-metrik-sub">{m['yangin']['sayi']} mğz</div>
</div>
</div>
<div class="bolge-neden">
<div class="bolge-neden-title">📋 NEDENLER</div>
{nedenler_html}
</div>
<div class="bolge-kaldirac">
<div class="bolge-kaldirac-title">🎯 ÖNERİLEN KALDIRACLAR</div>
{kaldirac_html}
</div>
</div>''', unsafe_allow_html=True)
    
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
    
    # === KATEGORİ + FİLTRE ===
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
        
        # === 1. GİDER FİLTRE BUTONLARI (ÖNCE) ===
        st.markdown("#### 💰 Gider Filtresi")
        
        # Her gider için problemli mağaza say
        gider_sayilari = {}
        gider_keys = ['Kira', 'Personel', 'Elektrik', 'Temizlik', 'Prim', 'Aidat', 'Toplam']
        d1, d2 = (f'D{n-1}_', f'D{n}_') if n >= 2 else ('D1_', 'D2_')
        
        for gk in gider_keys:
            count = 0
            for _, row in kdf.iterrows():
                oran1 = row.get(f'{d1}{gk}_Oran', 0) or 0
                oran2 = row.get(f'{d2}{gk}_Oran', 0) or 0
                tl1 = row.get(f'{d1}{gk}_TL', 0) or 0
                tl2 = row.get(f'{d2}{gk}_TL', 0) or 0
                ns2 = row.get(f'{d2}NetSatis', 0) or 0
                min_etki = ns2 * 0.005 if ns2 > 0 else 5000
                
                if tl2 - tl1 >= min_etki and oran2 - oran1 >= GIDER_RULES.get(gk, {}).get('abs', 0.05):
                    count += 1
            gider_sayilari[gk] = count
        
        # Butonlar
        gcols = st.columns(len(gider_keys))
        for i, (gk, gcol) in enumerate(zip(gider_keys, gcols)):
            with gcol:
                if st.button(f"{gk}\n{gider_sayilari[gk]}", key=f"gf_{gk}", use_container_width=True):
                    st.session_state.sel_gider = gk
        
        # Temizle butonu
        if st.button("🔄 Gider Filtresini Temizle", key="gf_clear"):
            st.session_state.sel_gider = None
        
        # === 2. SM/BS FİLTRELERİ (SONRA) ===
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
            if sel_sm != 'Tümü' and sel_bs != 'Tümü':
                mag_list = ['Tümü'] + sorted(kdf[(kdf['SM'] == sel_sm) & (kdf['BS'] == sel_bs)]['Magaza_Isim'].tolist())
            elif sel_sm != 'Tümü':
                mag_list = ['Tümü'] + sorted(kdf[kdf['SM'] == sel_sm]['Magaza_Isim'].tolist())
            else:
                mag_list = ['Tümü'] + sorted(kdf['Magaza_Isim'].tolist())
            sel_mag = st.selectbox("Mağaza", mag_list, key="filter_mag")
        
        # Filtreleri uygula
        if sel_sm != 'Tümü':
            kdf = kdf[kdf['SM'] == sel_sm]
        if sel_bs != 'Tümü':
            kdf = kdf[kdf['BS'] == sel_bs]
        if sel_mag != 'Tümü':
            kdf = kdf[kdf['Magaza_Isim'] == sel_mag]
        
        # === 3. GİDER FİLTRESİ UYGULAMASI ===
        sel_gider = st.session_state.get('sel_gider', None)
        
        if sel_gider:
            # Sadece bu giderde problemi olan mağazaları filtrele
            filtered_codes = []
            for _, row in kdf.iterrows():
                oran1 = row.get(f'{d1}{sel_gider}_Oran', 0) or 0
                oran2 = row.get(f'{d2}{sel_gider}_Oran', 0) or 0
                tl1 = row.get(f'{d1}{sel_gider}_TL', 0) or 0
                tl2 = row.get(f'{d2}{sel_gider}_TL', 0) or 0
                ns2 = row.get(f'{d2}NetSatis', 0) or 0
                min_etki = ns2 * 0.005 if ns2 > 0 else 5000
                
                if tl2 - tl1 >= min_etki and oran2 - oran1 >= GIDER_RULES.get(sel_gider, {}).get('abs', 0.05):
                    filtered_codes.append(row['Kod'])
            
            kdf = kdf[kdf['Kod'].isin(filtered_codes)]
            st.info(f"🎯 **{sel_gider}** problemi olan mağazalar gösteriliyor ({len(kdf)} mağaza)")
        
        kdf = kdf.sort_values('Skor')
        st.markdown(f"### {k} ({len(kdf)} mağaza)")
        
        # === 4. MAĞAZA LİSTESİ ===
        for _, row in kdf.iterrows():
            analiz = ajan_analiz(row, info)
            tum_prob = analiz['gelir']['problemler'] + analiz['gider']['problemler']
            prob_str = " | ".join([p.split(':')[0].replace('🔴','').replace('📉','').replace('🏭','').replace('   └','').strip() for p in tum_prob[:2]]) if tum_prob else "Normal"
            
            with st.expander(f"**{row['Magaza_Isim']}** | {row['SM']}/{row['BS']} | Skor:{row['Skor']:.1f} | {prob_str}"):
                if n == 3:
                    st.markdown(f"**EBITDA:** {dk[0]} %{row.get('D1_EBITDA_Oran',0):.1f} → {dk[1]} %{row.get('D2_EBITDA_Oran',0):.1f} → {dk[2]} %{row.get('D3_EBITDA_Oran',0):.1f}")
                
                # Eğer gider filtresi seçiliyse, o giderin detayını göster
                if sel_gider:
                    oran1 = row.get(f'{d1}{sel_gider}_Oran', 0) or 0
                    oran2 = row.get(f'{d2}{sel_gider}_Oran', 0) or 0
                    tl1 = row.get(f'{d1}{sel_gider}_TL', 0) or 0
                    tl2 = row.get(f'{d2}{sel_gider}_TL', 0) or 0
                    tl_artis = tl2 - tl1
                    tl_artis_pct = ((tl2 / tl1) - 1) * 100 if tl1 > 0 else 0
                    oran_artis = oran2 - oran1
                    ns2 = row.get(f'{d2}NetSatis', 0) or 0
                    ebitda_etki = -tl_artis / ns2 * 100 if ns2 > 0 else 0
                    
                    st.markdown(f"""
**💰 {sel_gider} Detayı:**
- **Oran:** %{oran1:.2f} → %{oran2:.2f} (+{oran_artis:.2f}p)
- **TL:** {fmt(tl1)} → {fmt(tl2)} (+{fmt(tl_artis)}, +{tl_artis_pct:.0f}%)
- **EBITDA Etkisi:** {ebitda_etki:.2f} puan
""")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f'<div class="ajan-box ajan-ebitda"><div class="ajan-title">1️⃣ EBITDA</div>{"🔴 ALARM" if analiz["ebitda"]["alarm"] else "✅ Normal"}<br><small>{analiz["ebitda"]["mesaj"]}</small></div>', unsafe_allow_html=True)
                    gider_html = " ".join([f'<span class="problem-item">{p}</span>' for p in analiz['gider']['problemler'][:3]]) or '<span class="ok-item">✅ Normal</span>'
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
    st.subheader("👥 SM Performans")
    
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
                profil_str = " | ".join([f"{p['kalem']} %{p['oran']*100:.0f} {p['tip']}" for p in gider_profil[:3]])
                st.markdown(f'<div class="sm-alert">⚠️ {profil_str}</div>', unsafe_allow_html=True)
            
            # === BS DRILL-DOWN ===
            st.markdown("---")
            st.markdown("**👔 Bölge Sorumluları:**")
            
            bs_list = []
            for bs in df[df['SM'] == sm]['BS'].unique():
                if not bs:
                    continue
                bt = df[(df['SM'] == sm) & (df['BS'] == bs)]
                bs_ebitda = bt[f'D{n}_EBITDA'].sum()
                bs_ns = bt[f'D{n}_NetSatis'].sum()
                bs_oran = safe_div(bs_ebitda, bs_ns)
                bs_kritik = len(bt[bt['Kategori'].isin(['🔥 Yangın', '🚨 Acil', '🟥 Kritik'])])
                bs_list.append({
                    'bs': bs,
                    'count': len(bt),
                    'ebitda': bs_ebitda,
                    'oran': bs_oran,
                    'kritik': bs_kritik,
                    'df': bt
                })
            
            bs_list = sorted(bs_list, key=lambda x: x['kritik'], reverse=True)
            
            for b in bs_list:
                kritik_emoji = "🔴" if b['kritik'] > 2 else "🟡" if b['kritik'] > 0 else "🟢"
                
                with st.expander(f"📁 {b['bs']} | {b['count']} mğz | {fmt(b['ebitda'])} | %{b['oran']:.1f} | {kritik_emoji} {b['kritik']} kritik"):
                    # Kritik mağazalar
                    km = b['df'][b['df']['Kategori'].isin(['🔥 Yangın', '🚨 Acil', '🟥 Kritik'])].sort_values('Skor')
                    
                    if len(km) > 0:
                        for _, m in km.iterrows():
                            ma = ajan_analiz(m, info)
                            hukum_tip = ma['hukum']['tip']
                            
                            # Rakamsal detaylar
                            ns1 = m.get(f'D{n-1}_NetSatis', 0) or 0
                            ns2 = m.get(f'D{n}_NetSatis', 0) or 0
                            ns_pct = safe_pct(ns2, ns1)
                            eb1 = m.get(f'D{n-1}_EBITDA_Oran', 0) or 0
                            eb2 = m.get(f'D{n}_EBITDA_Oran', 0) or 0
                            eb_delta = eb2 - eb1
                            tasima = ma['gelir'].get('tasima_gucu') or 0
                            
                            st.markdown(f"**• {m['Magaza_Isim']}** | {m['Kategori']} | `{hukum_tip}`")
                            
                            # Detay satırları
                            detay_parts = []
                            detay_parts.append(f"Ciro: {fmt(ns1)}→{fmt(ns2)} ({ns_pct:+.0f}%)")
                            detay_parts.append(f"EBITDA: %{eb1:.1f}→%{eb2:.1f} ({eb_delta:+.1f}p)")
                            if tasima < 1.5:
                                tasima_durum = "🔥 YANGIN" if tasima < 1.0 else "⚠️ KRİTİK" if tasima < 1.2 else "📉 RİSK"
                                detay_parts.append(f"Taşıma: {tasima:.2f} {tasima_durum}")
                            
                            st.caption(f"  ├─ {detay_parts[0]}")
                            st.caption(f"  ├─ {detay_parts[1]}")
                            if len(detay_parts) > 2:
                                st.caption(f"  └─ {detay_parts[2]}")
                            
                            # Ana sorun özeti
                            if ma['hukum']['aksiyon']:
                                st.caption(f"  **→ {ma['hukum']['aksiyon'][0].replace('• ', '')}**")
                    else:
                        st.success("✅ Kritik mağaza yok")
    
    # === EXPORT ===
    st.markdown("---")
    out = BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as w:
        df.to_excel(w, sheet_name='TÜM', index=False)
    st.download_button("📥 Excel İndir", data=out.getvalue(), file_name=f"EBITDA_5Ajan.xlsx")


if __name__ == "__main__":
    run()
