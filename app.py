import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client

st.set_page_config(page_title="A101 Delist", page_icon="🏪", layout="wide")

# AYARLAR
SUPABASE_URL = "https://tlcgcdiycgfxpxwzkwuf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRsY2djZGl5Y2dmeHB4d3prd3VmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU2NDgwMjksImV4cCI6MjA4MTIyNDAyOX0.4GnWTvUmdLzqcP0v8MAqaNUQkYgk0S8qrw6nSPsz-t4"

KOLON_MAP = {
    'SM': 'sm', 'BS': 'bs', 'ay': 'ay',
    'Mağaza - Anahtar': 'magaza_kodu',
    'Mağaza - Orta uzunl.metin': 'magaza_adi',
    'Malzeme Kodu': 'malzeme_kodu',
    'Malzeme Tanımı': 'malzeme_tanimi',
    'Ürün Grubu - Orta uzunl.metin': 'urun_grubu',
    'Üst Mal Grubu - Orta uzunl.metin': 'ust_mal_grubu',
    'Net Marj': 'net_marj',
    'Satış Miktarı': 'satis_miktari',
    'Satış Hasılatı (SAF)': 'satis_hasilati',
    'Envanter Tutarı': 'envanter_tutari',
    'Fire Tutarı': 'fire_tutari',
    'Toplam Kampanya Zararı': 'kampanya_zarari'
}

def kategori_belirle(row):
    t = str(row.get('malzeme_tanimi', '')).upper()
    u = str(row.get('ust_mal_grubu', '')).upper()
    k = str(row.get('malzeme_kodu', ''))
    if 'KASA' in t or k.startswith('98'): return 'KASA'
    if 'EKMEK' in t or 'EKMEK' in u: return 'EKMEK'
    if 'POŞET' in t: return 'POSET'
    if 'MEYVE' in u or 'SEBZE' in u: return 'MEYVE_SEBZE'
    if 'TAVUK' in t or 'PİLİÇ' in t: return 'TAVUK'
    return 'DIGER'

def process_excel(df, yil, ay):
    df.columns = df.columns.str.strip()
    mevcut = [c for c in KOLON_MAP if c in df.columns]
    df = df[mevcut].rename(columns=KOLON_MAP)
    
    for c in ['net_marj', 'satis_miktari', 'satis_hasilati', 'envanter_tutari', 'fire_tutari', 'kampanya_zarari']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    
    df['yil_ay'] = f"{yil}-{ay:02d}"
    df['yil'] = yil
    df['kategori'] = df.apply(kategori_belirle, axis=1)
    df['delist_edilebilir'] = df['kategori'].isin(['TAVUK', 'DIGER'])
    df['gercek_marj'] = df['net_marj'] - df.get('kampanya_zarari', 0)
    df['toplam_kayip'] = df['envanter_tutari'] + df['fire_tutari']
    
    return df

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_months():
    try:
        sb = get_supabase()
        r = sb.table('delist_monthly_summary').select('yil_ay').order('yil_ay', desc=True).execute()
        return [x['yil_ay'] for x in r.data]
    except:
        return []

def get_data(yil_ay):
    try:
        sb = get_supabase()
        r = sb.table('delist_raw_data').select('*').eq('yil_ay', yil_ay).execute()
        if r.data:
            return pd.DataFrame(r.data)
    except:
        pass
    return None

def upload_to_supabase(df, yil_ay):
    sb = get_supabase()
    
    try:
        sb.table('delist_raw_data').delete().eq('yil_ay', yil_ay).execute()
    except:
        pass
    
    batch_size = 500
    total = len(df)
    progress = st.progress(0)
    
    for i in range(0, total, batch_size):
        batch = df.iloc[i:i+batch_size].copy()
        batch = batch.replace({np.nan: None, np.inf: None, -np.inf: None})
        
        cols = ['yil_ay', 'yil', 'sm', 'bs', 'magaza_kodu', 'magaza_adi', 
                'malzeme_kodu', 'malzeme_tanimi', 'urun_grubu', 'ust_mal_grubu',
                'net_marj', 'satis_miktari', 'satis_hasilati', 'envanter_tutari', 
                'fire_tutari', 'kampanya_zarari', 'kategori', 'delist_edilebilir', 
                'gercek_marj', 'toplam_kayip']
        
        batch_cols = [c for c in cols if c in batch.columns]
        batch = batch[batch_cols]
        
        try:
            sb.table('delist_raw_data').insert(batch.to_dict('records')).execute()
        except Exception as e:
            st.error(f"Hata: {e}")
            return False
        
        progress.progress(min((i + batch_size) / total, 1.0))
    
    summary = {
        'yil_ay': yil_ay,
        'toplam_magaza': int(df['magaza_kodu'].nunique()),
        'toplam_urun': int(df['malzeme_kodu'].nunique()),
        'toplam_net_marj': float(df['net_marj'].sum()),
        'toplam_gercek_marj': float(df['gercek_marj'].sum()),
        'toplam_satis': float(df['satis_hasilati'].sum()),
        'toplam_envanter_kayip': float(df[df['envanter_tutari'] < 0]['envanter_tutari'].sum()),
        'toplam_fire': float(df['fire_tutari'].sum()),
        'toplam_kayit': len(df)
    }
    
    try:
        sb.table('delist_monthly_summary').delete().eq('yil_ay', yil_ay).execute()
        sb.table('delist_monthly_summary').insert(summary).execute()
    except:
        pass
    
    return True

# SIDEBAR
st.sidebar.title("🏪 A101 Delist")
page = st.sidebar.radio("Sayfa", ["📊 Dashboard", "🔴 Delist", "🚨 Hırsızlık", "📤 Yükle"])

months = get_months()
month = st.sidebar.selectbox("Ay", months) if months else None

# SAYFALAR
if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    
    if not months:
        st.warning("Veri yok! '📤 Yükle' sayfasından Excel yükle.")
    elif month:
        df = get_data(month)
        if df is not None:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Mağaza", f"{df['magaza_kodu'].nunique():,}")
            c2.metric("Ürün", f"{df['malzeme_kodu'].nunique():,}")
            c3.metric("Net Marj", f"{df['net_marj'].sum():,.0f} ₺")
            c4.metric("Envanter Kaybı", f"{df[df['envanter_tutari']<0]['envanter_tutari'].sum():,.0f} ₺")
            
            st.markdown("---")
            st.subheader("Kategori Özeti")
            kat = df.groupby('kategori').agg({'net_marj': 'sum', 'malzeme_kodu': 'nunique'}).reset_index()
            st.dataframe(kat, use_container_width=True, hide_index=True)

elif page == "🔴 Delist":
    st.title("🔴 Delist Önerileri")
    
    if month:
        df = get_data(month)
        if df is not None:
            ddf = df[df['delist_edilebilir'] == True]
            bolge = ddf.groupby(['malzeme_kodu', 'malzeme_tanimi', 'kategori']).agg({
                'gercek_marj': 'sum', 'satis_hasilati': 'sum', 'magaza_kodu': 'nunique'
            }).reset_index()
            
            oneri = bolge[bolge['gercek_marj'] < -1000].sort_values('gercek_marj')
            st.info(f"**{len(oneri)}** ürün delist önerisi")
            st.dataframe(oneri.head(50), use_container_width=True, hide_index=True)

elif page == "🚨 Hırsızlık":
    st.title("🚨 Hırsızlık Şüphesi")
    
    if month:
        df = get_data(month)
        if df is not None:
            h = df[(df['fire_tutari'] == 0) & (df['envanter_tutari'] < -500)].sort_values('envanter_tutari')
            st.error(f"**{len(h)}** kayıt (Fire=0, Kayıp>500₺)")
            st.dataframe(h[['sm', 'bs', 'magaza_kodu', 'malzeme_kodu', 'malzeme_tanimi', 'envanter_tutari']].head(50), 
                        use_container_width=True, hide_index=True)

elif page == "📤 Yükle":
    st.title("📤 Veri Yükle")
    
    c1, c2 = st.columns(2)
    yil = c1.selectbox("Yıl", [2025, 2024])
    ay = c2.selectbox("Ay", range(1, 13))
    
    st.success(f"Dönem: **{yil}-{ay:02d}**")
    
    uploaded = st.file_uploader("Excel Seç", type=['xlsx'])
    
    if uploaded and st.button("🚀 Yükle", type="primary"):
        with st.spinner("İşleniyor..."):
            try:
                df = pd.read_excel(uploaded)
                st.info(f"Okundu: {len(df):,} satır")
                
                df = process_excel(df, yil, ay)
                yil_ay = f"{yil}-{ay:02d}"
                
                if upload_to_supabase(df, yil_ay):
                    st.success(f"✅ {yil_ay} yüklendi! ({len(df):,} satır)")
                    st.cache_resource.clear()
                    st.balloons()
            except Exception as e:
                st.error(f"Hata: {e}")
    
    st.markdown("---")
    st.write("**Yüklü:**", months if months else "Yok")

st.sidebar.markdown("---")
st.sidebar.caption("v2.0")
