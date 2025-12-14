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
    donemler = sorted(donemler, key=lambda d: ay_map.get(d.split()[0], 0))[-3:]

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


def generate_sebep_text(row, donem_info):
    """Detaylı sebep analizi - metin olarak"""

    n = donem_info['n']
    donemler = donem_info['donemler']

    lines = []

    if n >= 3:
        d1, d2 = 'D2_', 'D3_'
        d1_name, d2_name = donemler[1], donemler[2]
    else:
        d1, d2 = 'D1_', 'D2_'
        d1_name, d2_name = donemler[0], donemler[1]

    # === EBITDA ORAN DEĞİŞİMİ ===
    oran1 = row.get(f'{d1}EBITDA_Oran', 0)
    oran2 = row.get(f'{d2}EBITDA_Oran', 0)
    oran_degisim = oran2 - oran1

    lines.append(f"**EBITDA Orani:** %{oran1:.1f} → %{oran2:.1f} ({oran_degisim:+.1f} puan)")
    lines.append("")
    lines.append("**NEDEN?**")

    # === CİRO DEĞİŞİMİ ===
    ciro1 = row.get(f'{d1}NetSatis', 0)
    ciro2 = row.get(f'{d2}NetSatis', 0)
    ciro_pct = ((ciro2 - ciro1) / ciro1 * 100) if ciro1 > 0 else 0

    if ciro_pct < -10:
        lines.append(f"- 📉 **Ciro DUSTU:** {format_currency(ciro1)}₺ → {format_currency(ciro2)}₺ ({ciro_pct:+.1f}%)")
    elif ciro_pct > 10:
        lines.append(f"- 📈 Ciro artti: {format_currency(ciro1)}₺ → {format_currency(ciro2)}₺ ({ciro_pct:+.1f}%)")
    else:
        lines.append(f"- ➖ Ciro sabit: {format_currency(ciro2)}₺ ({ciro_pct:+.1f}%)")

    # === SMM DEĞİŞİMİ ===
    smm_oran1 = row.get(f'{d1}SMM_Oran', 0)
    smm_oran2 = row.get(f'{d2}SMM_Oran', 0)
    smm_degisim = smm_oran2 - smm_oran1

    if smm_degisim > 1:
        lines.append(f"- 🏭 **SMM Orani ARTTI:** %{smm_oran1:.1f} → %{smm_oran2:.1f} ({smm_degisim:+.1f} puan)")

    # === İADE DEĞİŞİMİ ===
    iade_oran1 = row.get(f'{d1}Iade_Oran', 0)
    iade_oran2 = row.get(f'{d2}Iade_Oran', 0)
    iade_degisim = iade_oran2 - iade_oran1

    if iade_degisim > 0.5:
        lines.append(f"- ↩️ **Iade Orani ARTTI:** %{iade_oran1:.2f} → %{iade_oran2:.2f} ({iade_degisim:+.2f} puan)")

    # === ENVANTER KAYBI ===
    env_oran1 = row.get(f'{d1}Envanter_Oran', 0)
    env_oran2 = row.get(f'{d2}Envanter_Oran', 0)
    env_degisim = env_oran2 - env_oran1

    if env_degisim > 0.3:
        lines.append(f"- 📦 **Envanter Kaybi ARTTI:** %{env_oran1:.2f} → %{env_oran2:.2f} ({env_degisim:+.2f} puan)")

    # === GİDER KALEMLERİ ===
    gider_kalemleri = [
        ('Personel', 'Personel'),
        ('Kira', 'Kira'),
        ('Elektrik', 'Elektrik/Su/Tel')
    ]

    for key, name in gider_kalemleri:
        tl1 = row.get(f'{d1}{key}', 0)
        tl2 = row.get(f'{d2}{key}', 0)
        gider_oran1 = row.get(f'{d1}{key}_Oran', 0)
        gider_oran2 = row.get(f'{d2}{key}_Oran', 0)

        tl_degisim = tl2 - tl1
        gider_oran_degisim = gider_oran2 - gider_oran1

        if gider_oran_degisim > 1:
            if tl_degisim > 5000:
                lines.append(f"- ⚠️ **{name}:** TL artti ({format_currency(tl1)}₺ → {format_currency(tl2)}₺), Oran: %{gider_oran1:.1f} → %{gider_oran2:.1f}")
            elif abs(tl_degisim) < 5000:
                lines.append(f"- ⚠️ **{name}:** TL sabit ({format_currency(tl2)}₺), ciro dusunce oran artti: %{gider_oran1:.1f} → %{gider_oran2:.1f}")

    return "\n".join(lines)


def render_magaza_card(row, donem_info):
    """Mağaza kartını Streamlit native ile render et"""

    donemler = donem_info['donemler']
    n = donem_info['n']

    kod = row['Kod']
    magaza = row['Magaza'][:50] if len(row['Magaza']) > 50 else row['Magaza']

    st.markdown(f"### {kod}")
    st.caption(magaza)

    # Zaman serisi - metrics
    if n == 3:
        cols = st.columns(5)
        with cols[0]:
            st.metric(
                donemler[0],
                f"{format_currency(row['D1_EBITDA'])}₺",
                f"%{row['D1_EBITDA_Oran']:.1f}"
            )
        with cols[1]:
            delta1 = row.get('D1_D2_EBITDA_Pct', 0)
            st.metric("Degisim", f"{delta1:+.1f}%", "")
        with cols[2]:
            st.metric(
                donemler[1],
                f"{format_currency(row['D2_EBITDA'])}₺",
                f"%{row['D2_EBITDA_Oran']:.1f}"
            )
        with cols[3]:
            delta2 = row.get('D2_D3_EBITDA_Pct', 0)
            st.metric("Degisim", f"{delta2:+.1f}%", "")
        with cols[4]:
            st.metric(
                donemler[2],
                f"{format_currency(row['D3_EBITDA'])}₺",
                f"%{row['D3_EBITDA_Oran']:.1f}"
            )
    else:
        cols = st.columns(3)
        with cols[0]:
            st.metric(
                donemler[0],
                f"{format_currency(row['D1_EBITDA'])}₺",
                f"%{row['D1_EBITDA_Oran']:.1f}"
            )
        with cols[1]:
            delta1 = row.get('D1_D2_EBITDA_Pct', 0)
            st.metric("Degisim", f"{delta1:+.1f}%", "")
        with cols[2]:
            st.metric(
                donemler[1],
                f"{format_currency(row['D2_EBITDA'])}₺",
                f"%{row['D2_EBITDA_Oran']:.1f}"
            )

    # Sebep analizi
    sebep_text = generate_sebep_text(row, donem_info)
    st.markdown(sebep_text)
    st.divider()


# === ANA UYGULAMA ===

def main():
    st.title("🎯 EBITDA Karar Motoru")

    # Session state - dosya kalıcılığı
    if 'data' not in st.session_state:
        st.session_state.data = None
        st.session_state.donem_info = None

    # Dosya yükleme
    uploaded_file = st.file_uploader("Excel Dosyasi Yukle", type=['xlsx'], key="file_uploader")

    # Yeni dosya yüklendiyse işle
    if uploaded_file is not None:
        with st.spinner("Veri isleniyor..."):
            result_df, donem_info, error = load_and_process(uploaded_file)

        if error:
            st.error(error)
            return

        st.session_state.data = result_df
        st.session_state.donem_info = donem_info
        st.success(f"✓ {len(result_df)} magaza yuklendi")

    # Veri yoksa uyarı göster
    if st.session_state.data is None:
        st.warning("📁 EBITDA dosyasini yukleyin")
        st.info("""
        - Dosya bir kez yuklenir, oturumda kalir
        - Her ay yeni rapor geldiginde guncelleyin
        - En az 2 donem verisi gerekli
        """)
        return

    # Veriyi al
    df = st.session_state.data
    donem_info = st.session_state.donem_info
    donemler = donem_info['donemler']
    n = donem_info['n']

    st.caption(f"{' → '.join(donemler)} | {len(df)} magaza")

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

    acil_count = int(df['Acil'].sum())
    yangin_count = int(df['Yangin'].sum())

    # KPI Kartları
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            f"💰 {donemler[-1]} EBITDA",
            f"{format_currency(toplam_ebitda)}₺",
            f"{format_currency(ebitda_degisim)}₺"
        )

    with col2:
        st.metric(
            "📊 EBITDA Orani",
            f"%{genel_oran:.2f}",
            f"{oran_degisim:+.2f} puan"
        )

    with col3:
        st.metric(
            "🚨 Acil Mudahale",
            acil_count,
            "EBITDA < 0 & trend kotu"
        )

    with col4:
        st.metric(
            "🔥 Yangin",
            yangin_count,
            "Ust uste 2 ay negatif"
        )

    st.divider()

    # === SM PERFORMANS TABLOSU ===
    st.subheader("👥 SM Performans")

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

    # SM tablosu
    for _, sm_row in sm_df.iterrows():
        sm_name = sm_row['SM'].split()[0] if pd.notna(sm_row['SM']) else 'N/A'
        magaza_sayisi = int(sm_row['Kod'])
        acil_sm = int(sm_row['Acil'])
        yangin_sm = int(sm_row['Yangin'])

        durum = ""
        if acil_sm > 0:
            durum += f"🚨{acil_sm} "
        if yangin_sm > 0:
            durum += f"🔥{yangin_sm}"

        with st.expander(f"**{sm_name}** ({magaza_sayisi} magaza) {durum}"):
            if n == 3:
                cols = st.columns(6)
                with cols[0]:
                    st.metric(donemler[0], f"{format_currency(sm_row['D1_EBITDA'])}₺", f"%{sm_row['D1_Oran']:.1f}")
                with cols[1]:
                    st.metric("Δ", f"{sm_row.get('D1_D2_Pct', 0):+.1f}%", "")
                with cols[2]:
                    st.metric(donemler[1], f"{format_currency(sm_row['D2_EBITDA'])}₺", f"%{sm_row['D2_Oran']:.1f}")
                with cols[3]:
                    st.metric("Δ", f"{sm_row.get('D2_D3_Pct', 0):+.1f}%", "")
                with cols[4]:
                    st.metric(donemler[2], f"{format_currency(sm_row['D3_EBITDA'])}₺", f"%{sm_row['D3_Oran']:.1f}")
                with cols[5]:
                    st.metric("Acil/Yangin", f"{acil_sm}/{yangin_sm}", "")
            else:
                cols = st.columns(4)
                with cols[0]:
                    st.metric(donemler[0], f"{format_currency(sm_row['D1_EBITDA'])}₺", f"%{sm_row['D1_Oran']:.1f}")
                with cols[1]:
                    st.metric("Δ", f"{sm_row.get('D1_D2_Pct', 0):+.1f}%", "")
                with cols[2]:
                    st.metric(donemler[1], f"{format_currency(sm_row['D2_EBITDA'])}₺", f"%{sm_row['D2_Oran']:.1f}")
                with cols[3]:
                    st.metric("Acil/Yangin", f"{acil_sm}/{yangin_sm}", "")

    st.divider()

    # === ACİL VE YANGIN SEKMELERI ===
    tab1, tab2 = st.tabs([f"🚨 Acil Mudahale ({acil_count})", f"🔥 Yangin ({yangin_count})"])

    with tab1:
        if acil_count > 0:
            acil_df = df[df['Acil']].sort_values(f'D{n}_EBITDA')

            # SM bazında grupla
            for sm in acil_df['SM'].unique():
                sm_name = sm.split()[0] if pd.notna(sm) else 'N/A'
                sm_magazalar = acil_df[acil_df['SM'] == sm]

                with st.expander(f"📁 {sm_name} ({len(sm_magazalar)} magaza)", expanded=True):
                    for _, row in sm_magazalar.iterrows():
                        render_magaza_card(row, donem_info)
        else:
            st.success("✅ Acil mudahale gerektiren magaza yok")

    with tab2:
        if yangin_count > 0:
            st.error("⚠️ Bu magazalara ONCE gidilmeli - Ust uste 2 ay negatif EBITDA")

            yangin_df = df[df['Yangin']].sort_values(f'D{n}_EBITDA')

            for sm in yangin_df['SM'].unique():
                sm_name = sm.split()[0] if pd.notna(sm) else 'N/A'
                sm_magazalar = yangin_df[yangin_df['SM'] == sm]

                with st.expander(f"🔥 {sm_name} ({len(sm_magazalar)} magaza)", expanded=True):
                    for _, row in sm_magazalar.iterrows():
                        render_magaza_card(row, donem_info)
        else:
            st.success("✅ Yangin durumunda magaza yok")

    st.divider()

    # === EXPORT ===
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='TUM VERI', index=False)
        if acil_count > 0:
            df[df['Acil']].to_excel(writer, sheet_name='ACIL', index=False)
        if yangin_count > 0:
            df[df['Yangin']].to_excel(writer, sheet_name='YANGIN', index=False)
        sm_df.to_excel(writer, sheet_name='SM OZET', index=False)

    st.download_button(
        "📥 Excel Indir",
        data=output.getvalue(),
        file_name=f"EBITDA_Karar_{donemler[-1].replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.caption(f"🎯 EBITDA Karar Motoru | {' → '.join(donemler)}")


if __name__ == "__main__":
    main()
