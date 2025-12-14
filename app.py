import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="EBITDA Karar Motoru", page_icon="🎯", layout="wide")

# Basit CSS - sadece renkler
st.markdown("""
<style>
    .stApp { background-color: #0f172a; }
    .stMetric label { color: #94a3b8 !important; }
    .stMetric [data-testid="stMetricValue"] { color: #ffffff !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #1e293b; color: #94a3b8; border-radius: 8px; }
    .stTabs [aria-selected="true"] { background-color: #f59e0b !important; color: #000000 !important; }
    .stExpander { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; }
    div[data-testid="stExpander"] details summary p { color: #f59e0b !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

def extract_code(magaza):
    if pd.isna(magaza):
        return None
    return str(magaza).split()[0]

def format_currency(value):
    if pd.isna(value) or value == 0:
        return "-"
    if abs(value) >= 1000000:
        return f"{value/1000000:.2f}M₺"
    elif abs(value) >= 1000:
        return f"{value/1000:.0f}K₺"
    return f"{value:,.0f}₺"

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
        row['SM'] = str(son['Satış Müdürü - Metin']).split()[0] if pd.notna(son['Satış Müdürü - Metin']) else ''
        
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
    
    if n >= 2:
        result_df['D1_D2_Pct'] = ((result_df['D2_EBITDA'] - result_df['D1_EBITDA']) / result_df['D1_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
    if n >= 3:
        result_df['D2_D3_Pct'] = ((result_df['D3_EBITDA'] - result_df['D2_EBITDA']) / result_df['D2_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
    
    if n >= 3:
        result_df['Yangin'] = (result_df['D2_EBITDA'] < 0) & (result_df['D3_EBITDA'] < 0)
        result_df['Acil'] = (result_df['D3_EBITDA'] < 0) & ((result_df['D2_D3_Pct'] < 0) | (result_df['D1_D2_Pct'] < 0))
    else:
        result_df['Yangin'] = (result_df['D1_EBITDA'] < 0) & (result_df['D2_EBITDA'] < 0)
        result_df['Acil'] = (result_df['D2_EBITDA'] < 0) & (result_df['D1_D2_Pct'] < 0)
    
    return result_df, {'donemler': donemler, 'n': n}, None


def generate_sebep(row, donem_info):
    n = donem_info['n']
    donemler = donem_info['donemler']
    sebepler = []
    
    if n >= 3:
        d1, d2 = 'D2_', 'D3_'
        d1_name, d2_name = donemler[1], donemler[2]
    else:
        d1, d2 = 'D1_', 'D2_'
        d1_name, d2_name = donemler[0], donemler[1]
    
    # EBITDA Oran
    oran1 = row.get(f'{d1}EBITDA_Oran', 0)
    oran2 = row.get(f'{d2}EBITDA_Oran', 0)
    if oran2 - oran1 < -2:
        sebepler.append(f"📊 **EBITDA Oranı DÜŞTÜ**: %{oran1:.1f} → %{oran2:.1f} ({oran2-oran1:+.1f} puan)")
    
    # Ciro
    ciro1 = row.get(f'{d1}NetSatis', 0)
    ciro2 = row.get(f'{d2}NetSatis', 0)
    ciro_pct = ((ciro2 - ciro1) / ciro1 * 100) if ciro1 > 0 else 0
    if ciro_pct < -10:
        sebepler.append(f"📉 **Net Satış DÜŞTÜ**: {format_currency(ciro1)} → {format_currency(ciro2)} ({ciro_pct:+.1f}%)")
    
    # SMM
    smm1 = row.get(f'{d1}SMM_Oran', 0)
    smm2 = row.get(f'{d2}SMM_Oran', 0)
    if smm2 - smm1 > 1:
        sebepler.append(f"🏭 **SMM Oranı ARTTI**: %{smm1:.1f} → %{smm2:.1f} ({smm2-smm1:+.1f} puan)")
    
    # İade
    iade1 = row.get(f'{d1}Iade_Oran', 0)
    iade2 = row.get(f'{d2}Iade_Oran', 0)
    if iade2 - iade1 > 0.5:
        sebepler.append(f"↩️ **İade Oranı ARTTI**: %{iade1:.2f} → %{iade2:.2f}")
    
    # Envanter
    env1 = row.get(f'{d1}Env_Oran', 0)
    env2 = row.get(f'{d2}Env_Oran', 0)
    if env2 - env1 > 0.3:
        sebepler.append(f"📦 **Envanter Kaybı ARTTI**: %{env1:.2f} → %{env2:.2f} ({env2-env1:+.2f} puan)")
    
    # Gider kalemleri
    for key, name in [('Personel', 'Personel'), ('Kira', 'Kira'), ('Elektrik', 'Su/Elektrik/Tel')]:
        tl1 = row.get(f'{d1}{key}', 0)
        tl2 = row.get(f'{d2}{key}', 0)
        oran1 = row.get(f'{d1}{key}_Oran', 0)
        oran2 = row.get(f'{d2}{key}_Oran', 0)
        
        if oran2 - oran1 > 1:
            if tl2 - tl1 > 5000:
                sebepler.append(f"⚠️ **{name}: TL ARTTI** {format_currency(tl1)} → {format_currency(tl2)} | Oran: %{oran1:.1f} → %{oran2:.1f}")
            elif abs(tl2 - tl1) < 5000:
                sebepler.append(f"⚠️ **{name}: CİRO DÜŞÜNCE ORAN ARTTI** TL sabit ({format_currency(tl2)}) | Oran: %{oran1:.1f} → %{oran2:.1f}")
    
    return sebepler if sebepler else ["✓ Belirgin bozulma tespit edilemedi"]


def main():
    st.title("🎯 EBITDA Karar Motoru")
    
    if 'data' not in st.session_state:
        st.session_state.data = None
        st.session_state.donem_info = None
    
    uploaded_file = st.file_uploader("Excel dosyası yükle", type=['xlsx'])
    
    if uploaded_file:
        with st.spinner("Veri işleniyor..."):
            result_df, donem_info, error = load_and_process(uploaded_file)
        
        if error:
            st.error(error)
            return
        
        st.session_state.data = result_df
        st.session_state.donem_info = donem_info
        st.success(f"✓ {len(result_df)} mağaza yüklendi")
    
    if st.session_state.data is None:
        st.info("📁 EBITDA dosyasını yükleyin")
        return
    
    df = st.session_state.data
    donem_info = st.session_state.donem_info
    donemler = donem_info['donemler']
    n = donem_info['n']
    
    st.caption(f"{' → '.join(donemler)} | {len(df)} mağaza")
    
    # KPI'lar
    son = f'D{n}_'
    onceki = f'D{n-1}_'
    
    toplam_ebitda = df[f'{son}EBITDA'].sum()
    toplam_satis = df[f'{son}NetSatis'].sum()
    genel_oran = (toplam_ebitda / toplam_satis * 100) if toplam_satis > 0 else 0
    
    onceki_ebitda = df[f'{onceki}EBITDA'].sum()
    onceki_satis = df[f'{onceki}NetSatis'].sum()
    onceki_oran = (onceki_ebitda / onceki_satis * 100) if onceki_satis > 0 else 0
    
    acil_count = int(df['Acil'].sum())
    yangin_count = int(df['Yangin'].sum())
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(f"💰 {donemler[-1]} EBITDA", format_currency(toplam_ebitda), f"{format_currency(toplam_ebitda - onceki_ebitda)}")
    with col2:
        st.metric("📊 EBITDA Oranı", f"%{genel_oran:.2f}", f"{genel_oran - onceki_oran:+.2f} puan")
    with col3:
        st.metric("🚨 Acil Müdahale", acil_count, "mağaza")
    with col4:
        st.metric("🔥 Yangın", yangin_count, "üst üste negatif")
    
    st.divider()
    
    # SM Performans
    st.subheader("👥 SM Performans")
    
    sm_agg = {f'D{i}_EBITDA': 'sum' for i in range(1, n+1)}
    sm_agg.update({f'D{i}_NetSatis': 'sum' for i in range(1, n+1)})
    sm_agg['Kod'] = 'count'
    sm_agg['Acil'] = 'sum'
    sm_agg['Yangin'] = 'sum'
    
    sm_df = df.groupby('SM').agg(sm_agg).reset_index()
    sm_df = sm_df[sm_df['Kod'] > 2].sort_values(f'D{n}_EBITDA', ascending=False)
    
    for i in range(1, n+1):
        sm_df[f'D{i}_Oran'] = (sm_df[f'D{i}_EBITDA'] / sm_df[f'D{i}_NetSatis'] * 100).fillna(0)
    
    if n >= 2:
        sm_df['D1_D2_Pct'] = ((sm_df['D2_EBITDA'] - sm_df['D1_EBITDA']) / sm_df['D1_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
    if n >= 3:
        sm_df['D2_D3_Pct'] = ((sm_df['D3_EBITDA'] - sm_df['D2_EBITDA']) / sm_df['D2_EBITDA'].abs().replace(0, np.nan) * 100).fillna(0)
    
    for _, sm_row in sm_df.iterrows():
        sm_name = sm_row['SM']
        
        with st.container():
            if n == 3:
                cols = st.columns([2, 1.5, 1.5, 0.8, 1.5, 0.8, 1.5])
                cols[0].write(f"**{sm_name}** ({int(sm_row['Kod'])} mğz)")
                cols[1].write(f"{format_currency(sm_row['D1_EBITDA'])}\n\n%{sm_row['D1_Oran']:.1f}")
                cols[2].write(f"{format_currency(sm_row['D2_EBITDA'])}\n\n%{sm_row['D2_Oran']:.1f}")
                cols[3].write(f":{'red' if sm_row['D1_D2_Pct'] < 0 else 'green'}[{sm_row['D1_D2_Pct']:+.1f}%]")
                cols[4].write(f"{format_currency(sm_row['D3_EBITDA'])}\n\n%{sm_row['D3_Oran']:.1f}")
                cols[5].write(f":{'red' if sm_row['D2_D3_Pct'] < 0 else 'green'}[{sm_row['D2_D3_Pct']:+.1f}%]")
                
                durum = ""
                if sm_row['Acil'] > 0:
                    durum += f"🚨{int(sm_row['Acil'])} "
                if sm_row['Yangin'] > 0:
                    durum += f"🔥{int(sm_row['Yangin'])}"
                cols[6].write(durum if durum else "-")
            else:
                cols = st.columns([2, 1.5, 1.5, 1, 1.5])
                cols[0].write(f"**{sm_name}** ({int(sm_row['Kod'])} mğz)")
                cols[1].write(f"{format_currency(sm_row['D1_EBITDA'])} | %{sm_row['D1_Oran']:.1f}")
                cols[2].write(f"{format_currency(sm_row['D2_EBITDA'])} | %{sm_row['D2_Oran']:.1f}")
                cols[3].write(f":{'red' if sm_row['D1_D2_Pct'] < 0 else 'green'}[{sm_row['D1_D2_Pct']:+.1f}%]")
                cols[4].write(f"🚨{int(sm_row['Acil'])}" if sm_row['Acil'] > 0 else "-")
    
    st.divider()
    
    # Acil ve Yangın
    tab1, tab2 = st.tabs([f"🚨 Acil Müdahale ({acil_count})", f"🔥 Yangın ({yangin_count})"])
    
    with tab1:
        if acil_count > 0:
            acil_df = df[df['Acil']].sort_values(f'D{n}_EBITDA')
            
            for sm in acil_df['SM'].unique():
                sm_magazalar = acil_df[acil_df['SM'] == sm]
                
                with st.expander(f"📁 {sm} ({len(sm_magazalar)} mağaza)", expanded=True):
                    for _, row in sm_magazalar.iterrows():
                        st.markdown(f"### {row['Kod']} - {row['Magaza'][:40]}")
                        
                        # Zaman serisi
                        if n == 3:
                            cols = st.columns(5)
                            cols[0].metric(donemler[0], format_currency(row['D1_EBITDA']), f"%{row['D1_EBITDA_Oran']:.1f}")
                            cols[1].metric("→", f"{row.get('D1_D2_Pct', 0):+.1f}%", "")
                            cols[2].metric(donemler[1], format_currency(row['D2_EBITDA']), f"%{row['D2_EBITDA_Oran']:.1f}")
                            cols[3].metric("→", f"{row.get('D2_D3_Pct', 0):+.1f}%", "")
                            cols[4].metric(donemler[2], format_currency(row['D3_EBITDA']), f"%{row['D3_EBITDA_Oran']:.1f}")
                        else:
                            cols = st.columns(3)
                            cols[0].metric(donemler[0], format_currency(row['D1_EBITDA']), f"%{row['D1_EBITDA_Oran']:.1f}")
                            cols[1].metric("→", f"{row.get('D1_D2_Pct', 0):+.1f}%", "")
                            cols[2].metric(donemler[1], format_currency(row['D2_EBITDA']), f"%{row['D2_EBITDA_Oran']:.1f}")
                        
                        # Sebep
                        st.markdown("**📋 NEDEN?**")
                        sebepler = generate_sebep(row, donem_info)
                        for s in sebepler:
                            st.markdown(f"- {s}")
                        
                        st.markdown("---")
        else:
            st.success("✅ Acil müdahale gerektiren mağaza yok")
    
    with tab2:
        if yangin_count > 0:
            st.warning("⚠️ Bu mağazalara ÖNCE gidilmeli - Üst üste 2 ay negatif EBITDA")
            
            yangin_df = df[df['Yangin']].sort_values(f'D{n}_EBITDA')
            
            for sm in yangin_df['SM'].unique():
                sm_magazalar = yangin_df[yangin_df['SM'] == sm]
                
                with st.expander(f"🔥 {sm} ({len(sm_magazalar)} mağaza)", expanded=True):
                    for _, row in sm_magazalar.iterrows():
                        st.markdown(f"### 🔥 {row['Kod']} - {row['Magaza'][:40]}")
                        
                        if n == 3:
                            st.write(f"{donemler[0]}: {format_currency(row['D1_EBITDA'])} → {donemler[1]}: {format_currency(row['D2_EBITDA'])} → {donemler[2]}: {format_currency(row['D3_EBITDA'])}")
                        else:
                            st.write(f"{donemler[0]}: {format_currency(row['D1_EBITDA'])} → {donemler[1]}: {format_currency(row['D2_EBITDA'])}")
                        
                        st.markdown("**📋 NEDEN?**")
                        sebepler = generate_sebep(row, donem_info)
                        for s in sebepler:
                            st.markdown(f"- {s}")
                        
                        st.markdown("---")
        else:
            st.success("✅ Yangın durumunda mağaza yok")
    
    # Export
    st.divider()
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='TÜM', index=False)
        if acil_count > 0:
            df[df['Acil']].to_excel(writer, sheet_name='ACİL', index=False)
        if yangin_count > 0:
            df[df['Yangin']].to_excel(writer, sheet_name='YANGIN', index=False)
    
    st.download_button("📥 Excel İndir", data=output.getvalue(), 
                       file_name=f"EBITDA_Karar_{donemler[-1].replace(' ', '_')}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()
