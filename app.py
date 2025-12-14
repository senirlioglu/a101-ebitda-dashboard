import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="EBITDA Karar Sistemi", page_icon="🎯", layout="wide")

# Tema
st.markdown("""
<style>
    .stApp { background-color: #0f172a; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { background-color: #1e293b; border-radius: 8px; padding: 8px 16px; }
    .stTabs [aria-selected="true"] { background-color: #f59e0b !important; }
    .kategori-btn { 
        display: inline-block; padding: 8px 16px; margin: 4px; border-radius: 8px; 
        cursor: pointer; font-weight: 600; 
    }
    .basarili { background: #065f46; color: #6ee7b7; }
    .dikkat { background: #92400e; color: #fcd34d; }
    .kritik { background: #991b1b; color: #fca5a5; }
    .acil { background: #7f1d1d; color: #ff6b6b; border: 2px solid #ef4444; }
    .yangin { background: #7c2d12; color: #ffedd5; border: 2px solid #f97316; }
</style>
""", unsafe_allow_html=True)

# === YARDIMCI FONKSİYONLAR ===

def extract_code(magaza):
    if pd.isna(magaza):
        return None
    return str(magaza).split()[0]

def get_magaza_isim(magaza_full):
    """Mağaza kodunu çıkar, sadece isim döndür"""
    if pd.isna(magaza_full):
        return ""
    parts = str(magaza_full).split(' ', 1)
    return parts[1] if len(parts) > 1 else str(magaza_full)

def format_currency(value):
    if pd.isna(value) or value == 0:
        return "-"
    if abs(value) >= 1000000:
        return f"{value/1000000:.2f}M₺"
    elif abs(value) >= 1000:
        return f"{value/1000:.0f}K₺"
    return f"{value:,.0f}₺"

def format_delta(value):
    if pd.isna(value):
        return "-"
    color = "🔴" if value < 0 else "🟢"
    return f"{color} {value:+.1f}%"

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
                toplam_gider = pd.to_numeric(r.get('Toplam Mağaza Giderleri', 0), errors='coerce') or 0
                
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
                row[f'{prefix}ToplamGider_Oran'] = (toplam_gider / ns * 100) if ns > 0 else 0
        
        results.append(row)
    
    result_df = pd.DataFrame(results)
    n = len(donemler)
    
    # Değişimler
    if n >= 2:
        result_df['D1_D2_EBITDA_Pct'] = ((result_df['D2_EBITDA'] - result_df['D1_EBITDA']) / result_df['D1_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
        result_df['D1_D2_Satis_Pct'] = ((result_df['D2_NetSatis'] - result_df['D1_NetSatis']) / result_df['D1_NetSatis'].replace(0, np.nan) * 100).fillna(0)
    if n >= 3:
        result_df['D2_D3_EBITDA_Pct'] = ((result_df['D3_EBITDA'] - result_df['D2_EBITDA']) / result_df['D2_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
        result_df['D2_D3_Satis_Pct'] = ((result_df['D3_NetSatis'] - result_df['D2_NetSatis']) / result_df['D2_NetSatis'].replace(0, np.nan) * 100).fillna(0)
    
    # === HİBRİT SKOR HESAPLAMA ===
    
    # Bölge medyanı (son ay)
    son_oran_col = f'D{n}_EBITDA_Oran'
    bolge_medyan = result_df[son_oran_col].median()
    
    # Seviye Sapma = Mağaza Oranı - Bölge Medyanı
    result_df['Seviye_Sapma'] = result_df[son_oran_col] - bolge_medyan
    
    # Trend Değişim = Son Ay Oran - Önceki Ay Oran
    if n >= 3:
        result_df['Trend_Degisim'] = result_df['D3_EBITDA_Oran'] - result_df['D2_EBITDA_Oran']
    else:
        result_df['Trend_Degisim'] = result_df['D2_EBITDA_Oran'] - result_df['D1_EBITDA_Oran']
    
    # Hibrit Skor = Seviye + (Trend × 1.5)
    result_df['Hibrit_Skor'] = result_df['Seviye_Sapma'] + (result_df['Trend_Degisim'] * 1.5)
    
    # === KATEGORİ BELİRLEME ===
    
    def kategorize(row):
        skor = row['Hibrit_Skor']
        
        # Yangın: Üst üste 2 ay negatif EBITDA
        if n >= 3:
            if row['D2_EBITDA'] < 0 and row['D3_EBITDA'] < 0:
                return '🔥 Yangın'
        else:
            if row['D1_EBITDA'] < 0 and row['D2_EBITDA'] < 0:
                return '🔥 Yangın'
        
        # Skor bazlı kategoriler
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
    """Detaylı neden analizi üret"""
    n = donem_info['n']
    donemler = donem_info['donemler']
    nedenler = []
    
    if n >= 3:
        d1, d2 = 'D2_', 'D3_'
        d1_name, d2_name = donemler[1], donemler[2]
    else:
        d1, d2 = 'D1_', 'D2_'
        d1_name, d2_name = donemler[0], donemler[1]
    
    # EBITDA Oran değişimi
    oran1 = row.get(f'{d1}EBITDA_Oran', 0)
    oran2 = row.get(f'{d2}EBITDA_Oran', 0)
    if oran2 - oran1 < -2:
        nedenler.append(f"📊 EBITDA Oranı: %{oran1:.1f} → %{oran2:.1f} ({oran2-oran1:+.1f}p)")
    
    # Ciro
    ciro1 = row.get(f'{d1}NetSatis', 0)
    ciro2 = row.get(f'{d2}NetSatis', 0)
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
    
    # İade
    iade1, iade2 = row.get(f'{d1}Iade_Oran', 0), row.get(f'{d2}Iade_Oran', 0)
    if iade2 - iade1 > 0.3:
        nedenler.append(f"↩️ İade: %{iade1:.2f} → %{iade2:.2f} ({iade2-iade1:+.2f}p)")
    
    # Giderler
    for key, icon, name in [('Personel', '👥', 'Personel'), ('Kira', '🏠', 'Kira'), ('Elektrik', '⚡', 'Elektrik')]:
        tl1, tl2 = row.get(f'{d1}{key}', 0), row.get(f'{d2}{key}', 0)
        oran1, oran2 = row.get(f'{d1}{key}_Oran', 0), row.get(f'{d2}{key}_Oran', 0)
        
        if oran2 - oran1 > 1:
            if tl2 - tl1 > 5000:
                nedenler.append(f"{icon} {name}: TL arttı ({format_currency(tl1)}→{format_currency(tl2)}), oran %{oran1:.1f}→%{oran2:.1f}")
            elif abs(tl2 - tl1) < 5000:
                nedenler.append(f"{icon} {name}: TL sabit, ciro düşünce oran %{oran1:.1f}→%{oran2:.1f}")
    
    return nedenler if nedenler else ["✓ Belirgin bozulma yok"]


# === ANA UYGULAMA ===

def main():
    st.title("🎯 EBITDA Karar Sistemi")
    
    if 'data' not in st.session_state:
        st.session_state.data = None
        st.session_state.info = None
    
    uploaded_file = st.file_uploader("Excel yükle", type=['xlsx'])
    
    if uploaded_file:
        with st.spinner("İşleniyor..."):
            result_df, info, error = load_and_process(uploaded_file)
        if error:
            st.error(error)
            return
        st.session_state.data = result_df
        st.session_state.info = info
        st.success(f"✓ {len(result_df)} mağaza")
    
    if st.session_state.data is None:
        st.info("📁 EBITDA dosyası yükleyin")
        return
    
    df = st.session_state.data
    info = st.session_state.info
    donemler = info['donemler']
    n = info['n']
    bolge_medyan = info['bolge_medyan']
    
    # === BÖLGE ÖZET ===
    st.markdown("---")
    st.subheader("📊 BÖLGE ÖZET")
    
    # EBITDA Trend
    col1, col2, col3 = st.columns(3)
    
    for i, (col, d) in enumerate(zip([col1, col2, col3][:n], donemler)):
        ebitda = df[f'D{i+1}_EBITDA'].sum()
        satis = df[f'D{i+1}_NetSatis'].sum()
        oran = (ebitda / satis * 100) if satis > 0 else 0
        
        if i > 0:
            onceki_ebitda = df[f'D{i}_EBITDA'].sum()
            degisim_tl = ebitda - onceki_ebitda
            degisim_pct = ((ebitda - onceki_ebitda) / abs(onceki_ebitda) * 100) if onceki_ebitda != 0 else 0
            delta_str = f"{format_currency(degisim_tl)} ({degisim_pct:+.1f}%)"
        else:
            delta_str = None
        
        with col:
            st.metric(
                label=d,
                value=f"{format_currency(ebitda)} | %{oran:.1f}",
                delta=delta_str
            )
    
    st.caption(f"📐 Bölge EBITDA Oranı Medyanı: **%{bolge_medyan:.2f}**")
    
    # === KATEGORİ DAĞILIMI ===
    st.markdown("---")
    st.subheader("📦 KATEGORİ DAĞILIMI")
    st.caption("Tıkla → Mağaza listesi + Neden")
    
    kategoriler = ['🟩 Başarılı', '🟧 Dikkat', '🟥 Kritik', '🚨 Acil', '🔥 Yangın']
    kategori_sayilari = {k: len(df[df['Kategori'] == k]) for k in kategoriler}
    
    # Butonlar
    cols = st.columns(5)
    secili_kategori = None
    
    for i, (kat, col) in enumerate(zip(kategoriler, cols)):
        sayi = kategori_sayilari[kat]
        with col:
            if st.button(f"{kat}\n**{sayi}**", key=f"kat_{i}", use_container_width=True):
                st.session_state.secili_kategori = kat
    
    # Seçili kategori detayı
    if 'secili_kategori' in st.session_state and st.session_state.secili_kategori:
        kat = st.session_state.secili_kategori
        kat_df = df[df['Kategori'] == kat].sort_values('Hibrit_Skor')
        
        st.markdown(f"### {kat} ({len(kat_df)} mağaza)")
        
        for _, row in kat_df.iterrows():
            with st.expander(f"**{row['Magaza_Isim'][:35]}** | SM: {row['SM']} | BS: {row['BS']} | Skor: {row['Hibrit_Skor']:.1f}"):
                # Zaman serisi
                if n == 3:
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric(donemler[0], format_currency(row['D1_EBITDA']), f"%{row['D1_EBITDA_Oran']:.1f}")
                    c2.metric("→", f"{row.get('D1_D2_EBITDA_Pct', 0):+.1f}%")
                    c3.metric(donemler[1], format_currency(row['D2_EBITDA']), f"%{row['D2_EBITDA_Oran']:.1f}")
                    c4.metric("→", f"{row.get('D2_D3_EBITDA_Pct', 0):+.1f}%")
                    c5.metric(donemler[2], format_currency(row['D3_EBITDA']), f"%{row['D3_EBITDA_Oran']:.1f}")
                else:
                    c1, c2, c3 = st.columns(3)
                    c1.metric(donemler[0], format_currency(row['D1_EBITDA']), f"%{row['D1_EBITDA_Oran']:.1f}")
                    c2.metric("→", f"{row.get('D1_D2_EBITDA_Pct', 0):+.1f}%")
                    c3.metric(donemler[1], format_currency(row['D2_EBITDA']), f"%{row['D2_EBITDA_Oran']:.1f}")
                
                # Skor detayı
                st.markdown(f"""
                **📐 Skor Hesabı:**
                - Seviye Sapma: {row['Seviye_Sapma']:+.2f} (Bölge medyanı %{bolge_medyan:.1f}, Mağaza %{row[f'D{n}_EBITDA_Oran']:.1f})
                - Trend Değişim: {row['Trend_Degisim']:+.2f}
                - **Hibrit Skor: {row['Hibrit_Skor']:.2f}** = {row['Seviye_Sapma']:.2f} + ({row['Trend_Degisim']:.2f} × 1.5)
                """)
                
                # Neden
                st.markdown("**📋 NEDEN?**")
                nedenler = generate_neden(row, info)
                for neden in nedenler:
                    st.markdown(f"- {neden}")
    
    # === SM PERFORMANS ===
    st.markdown("---")
    st.subheader("👥 SM PERFORMANS")
    st.caption("Tıkla → BS Detayı")
    
    # SM grupla
    sm_agg = {}
    for i in range(1, n+1):
        sm_agg[f'D{i}_EBITDA'] = 'sum'
        sm_agg[f'D{i}_NetSatis'] = 'sum'
    sm_agg['Kod'] = 'count'
    
    sm_df = df.groupby('SM').agg(sm_agg).reset_index()
    sm_df = sm_df[sm_df['Kod'] > 2]
    
    # Oranlar ve değişimler
    for i in range(1, n+1):
        sm_df[f'D{i}_Oran'] = (sm_df[f'D{i}_EBITDA'] / sm_df[f'D{i}_NetSatis'] * 100).fillna(0)
    
    if n >= 2:
        sm_df['D1_D2_Pct'] = ((sm_df['D2_EBITDA'] - sm_df['D1_EBITDA']) / sm_df['D1_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
    if n >= 3:
        sm_df['D2_D3_Pct'] = ((sm_df['D3_EBITDA'] - sm_df['D2_EBITDA']) / sm_df['D2_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
    
    # Kategori sayıları
    for sm in sm_df['SM'].unique():
        sm_magazalar = df[df['SM'] == sm]
        for kat in kategoriler:
            sm_df.loc[sm_df['SM'] == sm, kat] = len(sm_magazalar[sm_magazalar['Kategori'] == kat])
    
    sm_df = sm_df.sort_values(f'D{n}_EBITDA', ascending=False)
    
    # SM tablosu
    for _, sm_row in sm_df.iterrows():
        sm_name = sm_row['SM']
        
        # Kategori özeti
        kat_ozet = " | ".join([f"{k.split()[0]}{int(sm_row.get(k, 0))}" for k in kategoriler if sm_row.get(k, 0) > 0])
        
        with st.expander(f"**{sm_name}** ({int(sm_row['Kod'])} mğz) | {kat_ozet}"):
            # SM trend
            if n == 3:
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric(donemler[0], f"{format_currency(sm_row['D1_EBITDA'])}", f"%{sm_row['D1_Oran']:.1f}")
                c2.metric("→", f"{sm_row.get('D1_D2_Pct', 0):+.1f}%")
                c3.metric(donemler[1], f"{format_currency(sm_row['D2_EBITDA'])}", f"%{sm_row['D2_Oran']:.1f}")
                c4.metric("→", f"{sm_row.get('D2_D3_Pct', 0):+.1f}%")
                c5.metric(donemler[2], f"{format_currency(sm_row['D3_EBITDA'])}", f"%{sm_row['D3_Oran']:.1f}")
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric(donemler[0], f"{format_currency(sm_row['D1_EBITDA'])}", f"%{sm_row['D1_Oran']:.1f}")
                c2.metric("→", f"{sm_row.get('D1_D2_Pct', 0):+.1f}%")
                c3.metric(donemler[1], f"{format_currency(sm_row['D2_EBITDA'])}", f"%{sm_row['D2_Oran']:.1f}")
            
            st.markdown("---")
            st.markdown("**👔 BS'ler:**")
            
            # BS detay
            bs_df = df[df['SM'] == sm_name].groupby('BS').agg({
                **{f'D{i}_EBITDA': 'sum' for i in range(1, n+1)},
                **{f'D{i}_NetSatis': 'sum' for i in range(1, n+1)},
                'Kod': 'count',
                'Kategori': lambda x: x.value_counts().to_dict()
            }).reset_index()
            
            for i in range(1, n+1):
                bs_df[f'D{i}_Oran'] = (bs_df[f'D{i}_EBITDA'] / bs_df[f'D{i}_NetSatis'] * 100).fillna(0)
            
            if n >= 2:
                bs_df['D1_D2_Pct'] = ((bs_df['D2_EBITDA'] - bs_df['D1_EBITDA']) / bs_df['D1_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
            if n >= 3:
                bs_df['D2_D3_Pct'] = ((bs_df['D3_EBITDA'] - bs_df['D2_EBITDA']) / bs_df['D2_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
            
            for _, bs_row in bs_df.iterrows():
                bs_name = bs_row['BS']
                bs_magazalar = df[(df['SM'] == sm_name) & (df['BS'] == bs_name)]
                
                # BS kategori özeti
                bs_kat = {k: len(bs_magazalar[bs_magazalar['Kategori'] == k]) for k in kategoriler}
                bs_kat_str = " ".join([f"{k.split()[0]}{v}" for k, v in bs_kat.items() if v > 0])
                
                with st.expander(f"📁 {bs_name} ({int(bs_row['Kod'])} mğz) | {bs_kat_str}"):
                    # BS trend
                    if n == 3:
                        st.write(f"{donemler[0]}: {format_currency(bs_row['D1_EBITDA'])} (%{bs_row['D1_Oran']:.1f}) → "
                                f"{donemler[1]}: {format_currency(bs_row['D2_EBITDA'])} ({bs_row.get('D1_D2_Pct', 0):+.1f}%) → "
                                f"{donemler[2]}: {format_currency(bs_row['D3_EBITDA'])} ({bs_row.get('D2_D3_Pct', 0):+.1f}%)")
                    
                    # Kritik mağazalar
                    kritik_magazalar = bs_magazalar[bs_magazalar['Kategori'].isin(['🚨 Acil', '🔥 Yangın', '🟥 Kritik'])]
                    
                    if len(kritik_magazalar) > 0:
                        st.markdown("**⚠️ Dikkat Gerektiren Mağazalar:**")
                        for _, m in kritik_magazalar.sort_values('Hibrit_Skor').iterrows():
                            st.markdown(f"- **{m['Magaza_Isim'][:30]}** | {m['Kategori']} | Skor: {m['Hibrit_Skor']:.1f}")
                            nedenler = generate_neden(m, info)
                            for neden in nedenler[:2]:  # İlk 2 neden
                                st.markdown(f"  - {neden}")
    
    # === GİZLİ TEHLİKE ===
    st.markdown("---")
    st.subheader("🔍 GİZLİ TEHLİKE: Pozitif ama Düşenler")
    
    son_ebitda = f'D{n}_EBITDA'
    gizli_tehlike = df[
        (df[son_ebitda] > 0) & 
        (df['Kategori'].isin(['🟧 Dikkat', '🟥 Kritik']))
    ].sort_values('Hibrit_Skor').head(10)
    
    if len(gizli_tehlike) > 0:
        st.warning(f"⚠️ {len(gizli_tehlike)} mağaza kâr ediyor ama hızla kötüleşiyor!")
        
        for _, row in gizli_tehlike.iterrows():
            with st.expander(f"**{row['Magaza_Isim'][:35]}** | {row['Kategori']} | EBITDA: {format_currency(row[son_ebitda])} | Skor: {row['Hibrit_Skor']:.1f}"):
                if n == 3:
                    st.write(f"{donemler[0]}: {format_currency(row['D1_EBITDA'])} (%{row['D1_EBITDA_Oran']:.1f}) → "
                            f"{donemler[1]}: {format_currency(row['D2_EBITDA'])} (%{row['D2_EBITDA_Oran']:.1f}) → "
                            f"{donemler[2]}: {format_currency(row['D3_EBITDA'])} (%{row['D3_EBITDA_Oran']:.1f})")
                
                st.markdown("**Neden tehlike?**")
                nedenler = generate_neden(row, info)
                for neden in nedenler:
                    st.markdown(f"- {neden}")
    else:
        st.success("✓ Gizli tehlike yok")
    
    # === KÖK NEDEN ===
    st.markdown("---")
    st.subheader("🗺️ KÖK NEDEN HARİTASI")
    
    son_prefix = f'D{n}_'
    metrikler = [
        ('Elektrik_Oran', '⚡ Elektrik'),
        ('Env_Oran', '📦 Envanter'),
        ('Iade_Oran', '↩️ İade'),
        ('Personel_Oran', '👥 Personel'),
        ('SMM_Oran', '🏭 SMM')
    ]
    
    kok_neden_data = []
    for col, name in metrikler:
        bolge_med = df[f'{son_prefix}{col}'].median()
        
        # SM bazında
        sm_analiz = []
        for sm in df['SM'].unique():
            sm_med = df[df['SM'] == sm][f'{son_prefix}{col}'].median()
            fark = sm_med - bolge_med
            if abs(fark) > 0.5:
                sm_analiz.append((sm, fark))
        
        # BS bazında
        bs_analiz = []
        for bs in df['BS'].unique():
            bs_med = df[df['BS'] == bs][f'{son_prefix}{col}'].median()
            fark = bs_med - bolge_med
            if abs(fark) > 0.8:
                bs_analiz.append((bs, fark))
        
        # Yorum
        if len(bs_analiz) > len(df['BS'].unique()) * 0.7:
            yorum = "🔴 SİSTEMİK"
        elif len(bs_analiz) > 0:
            yorum = f"🟠 BS: {', '.join([b[0] for b in bs_analiz[:2]])}"
        elif len(sm_analiz) > 0:
            yorum = f"🟡 SM: {', '.join([s[0] for s in sm_analiz[:2]])}"
        else:
            yorum = "🟢 Normal"
        
        kok_neden_data.append({
            'Metrik': name,
            'Bölge Medyan': f"%{bolge_med:.1f}",
            'Durum': yorum
        })
    
    st.dataframe(pd.DataFrame(kok_neden_data), use_container_width=True, hide_index=True)
    
    # === EXPORT ===
    st.markdown("---")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='TÜM', index=False)
        for kat in kategoriler:
            kat_df = df[df['Kategori'] == kat]
            if len(kat_df) > 0:
                sheet_name = kat.split()[1][:10]
                kat_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    st.download_button("📥 Excel İndir", data=output.getvalue(),
                       file_name=f"EBITDA_Karar_{donemler[-1].replace(' ', '_')}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()
