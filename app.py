import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="EBITDA Karar Sistemi", page_icon="🎯", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .main-header { background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white; padding: 20px 24px; border-radius: 12px; margin-bottom: 24px; }
    .main-header h1 { margin: 0; font-size: 1.8rem; }
    .main-header p { margin: 4px 0 0 0; opacity: 0.9; font-size: 0.9rem; }
    .karar-box { background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-left: 4px solid #f59e0b; padding: 16px 20px; border-radius: 0 12px 12px 0; margin-bottom: 24px; color: #92400e; }
    .metric-card { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .metric-label { color: #64748b; font-size: 0.75rem; text-transform: uppercase; }
    .metric-value { color: #1e293b; font-size: 1.6rem; font-weight: 700; margin: 8px 0; }
    .metric-delta.positive { color: #059669; }
    .metric-delta.negative { color: #dc2626; }
    .problem-card { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
    .problem-card.yapisal { border-left: 4px solid #6366f1; }
    .problem-card.akut { border-left: 4px solid #ef4444; }
    .sm-problem-alert { background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 8px 12px; margin-top: 8px; color: #991b1b; }
    .badge-yapisal { background: #e0e7ff; color: #4338ca; padding: 4px 10px; border-radius: 20px; font-size: 0.7rem; }
    .badge-akut { background: #fee2e2; color: #dc2626; padding: 4px 10px; border-radius: 20px; font-size: 0.7rem; }
</style>
""", unsafe_allow_html=True)

def extract_code(m):
    return str(m).split()[0] if pd.notna(m) else None

def get_isim(m):
    if pd.isna(m): return ""
    p = str(m).split(' ', 1)
    return p[1][:35] if len(p) > 1 else str(m)[:35]

def fmt(v):
    if pd.isna(v) or v == 0: return "-"
    if abs(v) >= 1e6: return f"{v/1e6:.2f}M₺"
    if abs(v) >= 1e3: return f"{v/1e3:.0f}K₺"
    return f"{v:,.0f}₺"

def get_yapisal(d1, d2, d3):
    s = sum([d1, d2, d3])
    if s >= 2: return '📌 YAPISAL', 'yapisal', 'badge-yapisal', '3 aydır yüksek'
    if d3 and not d2: return '⚡ AKUT', 'akut', 'badge-akut', 'Son ay ani artış'
    return '✓ NORMAL', '', '', ''

@st.cache_data
def load_data(f):
    df = pd.read_excel(f, sheet_name='EBITDA', header=1)
    df = df[df['Kar / Zarar'] != 'GENEL'].copy()
    ay = {'Ocak':1,'Şubat':2,'Mart':3,'Nisan':4,'Mayıs':5,'Haziran':6,'Temmuz':7,'Ağustos':8,'Eylül':9,'Ekim':10,'Kasım':11,'Aralık':12}
    donemler = sorted(df['Mali yıl/dönem - Orta uzunl.metin'].dropna().unique(), key=lambda d: ay.get(d.split()[0], 0))[-3:]
    if len(donemler) < 2: return None, None, "2 dönem gerekli"
    
    donem_data = {}
    for d in donemler:
        t = df[df['Mali yıl/dönem - Orta uzunl.metin'] == d].copy()
        t['Kod'] = t['Mağaza'].apply(extract_code)
        donem_data[d] = t.set_index('Kod')
    
    son = donem_data[donemler[-1]]
    son['_NS'] = pd.to_numeric(son['Net Satış (KDV Hariç)'], errors='coerce').fillna(0)
    valid = set(son[son['_NS'] > 0].index)
    for d in donemler[:-1]: valid &= set(donem_data[d].index)
    
    results = []
    for kod in valid:
        row = {'Kod': kod}
        s = son.loc[kod]
        if isinstance(s, pd.DataFrame): s = s.iloc[0]
        row['Magaza_Isim'] = get_isim(s['Mağaza'])
        row['SM'] = str(s['Satış Müdürü - Metin']).split()[0] if pd.notna(s['Satış Müdürü - Metin']) else ''
        row['BS'] = str(s['Bölge Sorumlusu - Metin']).split()[0] if pd.notna(s['Bölge Sorumlusu - Metin']) else ''
        
        for i, d in enumerate(donemler):
            p = f'D{i+1}_'
            if kod in donem_data[d].index:
                r = donem_data[d].loc[kod]
                if isinstance(r, pd.DataFrame): r = r.iloc[0]
                ns = pd.to_numeric(r.get('Net Satış (KDV Hariç)', 0), errors='coerce') or 0
                eb = pd.to_numeric(r.get('Mağaza Kar/Zararı', 0), errors='coerce') or 0
                row[f'{p}NetSatis'], row[f'{p}EBITDA'] = ns, eb
                row[f'{p}EBITDA_Oran'] = (eb/ns*100) if ns > 0 else 0
                for k, c in [('Env', 'Envanter Kaybı Mağaza'), ('Personel', 'Personel Giderleri'), ('Elektrik', 'Su\\Elektrik\\Telefon Giderleri '), ('SMM', 'SMM')]:
                    v = abs(pd.to_numeric(r.get(c, 0), errors='coerce') or 0)
                    row[f'{p}{k}_Oran'] = (v/ns*100) if ns > 0 else 0
        results.append(row)
    
    rdf = pd.DataFrame(results)
    n = len(donemler)
    med = rdf[f'D{n}_EBITDA_Oran'].median()
    rdf['Seviye'] = rdf[f'D{n}_EBITDA_Oran'] - med
    rdf['Trend'] = rdf[f'D{n}_EBITDA_Oran'] - rdf[f'D{n-1}_EBITDA_Oran'] if n >= 2 else 0
    rdf['Skor'] = rdf['Seviye'] + rdf['Trend'] * 1.5
    
    def kat(r):
        if n >= 3 and r['D2_EBITDA'] < 0 and r['D3_EBITDA'] < 0: return '🔥 Yangın'
        if r['Skor'] >= 0: return '🟩 Başarılı'
        if r['Skor'] >= -1: return '🟧 Dikkat'
        if r['Skor'] >= -2.5: return '🟥 Kritik'
        return '🚨 Acil'
    rdf['Kategori'] = rdf.apply(kat, axis=1)
    return rdf, {'donemler': donemler, 'n': n, 'med': med}, None

def neden_kisa(r, n):
    d1, d2 = ('D2_', 'D3_') if n >= 3 else ('D1_', 'D2_')
    nd = []
    c1, c2 = r.get(f'{d1}NetSatis', 0), r.get(f'{d2}NetSatis', 0)
    if c1 > 0 and (c2-c1)/c1*100 < -10: nd.append(f"Ciro↓{abs((c2-c1)/c1*100):.0f}%")
    for k, nm in [('Env_Oran','Env'), ('Personel_Oran','Pers'), ('Elektrik_Oran','Elek')]:
        if r.get(f'{d2}{k}', 0) - r.get(f'{d1}{k}', 0) > 0.5: nd.append(f"{nm}↑")
    return ", ".join(nd[:3]) if nd else "Bozulma"

def neden_detay(r, info):
    n, d = info['n'], info['donemler']
    d1, d2 = ('D2_', 'D3_') if n >= 3 else ('D1_', 'D2_')
    nd = []
    o1, o2 = r.get(f'{d1}EBITDA_Oran', 0), r.get(f'{d2}EBITDA_Oran', 0)
    if o2 - o1 < -2: nd.append(f"📊 EBITDA Oran: %{o1:.1f}→%{o2:.1f}")
    c1, c2 = r.get(f'{d1}NetSatis', 0), r.get(f'{d2}NetSatis', 0)
    if c1 > 0 and (c2-c1)/c1*100 < -10: nd.append(f"📉 Ciro: {fmt(c1)}→{fmt(c2)}")
    for k, ic, nm in [('Env_Oran','📦','Envanter'), ('Personel_Oran','👥','Personel'), ('Elektrik_Oran','⚡','Elektrik')]:
        v1, v2 = r.get(f'{d1}{k}', 0), r.get(f'{d2}{k}', 0)
        if v2 - v1 > 0.5: nd.append(f"{ic} {nm}: %{v1:.1f}→%{v2:.1f}")
    return nd if nd else ["✓ Belirgin bozulma yok"]

def sm_prob(df, sm, n):
    sdf = df[df['SM'] == sm]
    if len(sdf) < 3: return []
    pr = []
    for c, nm, e in [(f'D{n}_Elektrik_Oran','⚡Elek',1), (f'D{n}_Env_Oran','📦Env',0.5), (f'D{n}_Personel_Oran','👥Pers',1)]:
        if c in df.columns:
            m = df[c].median()
            o = (sdf[c] > m + e).sum() / len(sdf)
            if o >= 0.30: pr.append(f"{nm} %{o*100:.0f}")
    return pr

def main():
    st.markdown('<div class="main-header"><h1>🎯 EBITDA Karar Sistemi</h1><p>Hibrit Skor | Seviye + Trend</p></div>', unsafe_allow_html=True)
    
    if 'data' not in st.session_state: st.session_state.data = None
    
    f = st.file_uploader("Excel yükle", type=['xlsx'], label_visibility="collapsed")
    if f:
        rdf, info, err = load_data(f)
        if err: st.error(err); return
        st.session_state.data, st.session_state.info = rdf, info
    
    if st.session_state.data is None: st.info("📁 Excel yükleyin"); return
    
    df, info = st.session_state.data, st.session_state.info
    donemler, n, med = info['donemler'], info['n'], info['med']
    dk = [d.split()[0][:3] for d in donemler]
    
    kritik = len(df[df['Kategori'].isin(['🚨 Acil', '🔥 Yangın'])])
    gizli = len(df[(df['Kategori'].isin(['🟧 Dikkat', '🟥 Kritik'])) & (df[f'D{n}_EBITDA'] > 0)])
    st.markdown(f'<div class="karar-box">💡 **{kritik} mağaza** acil/yangın. **{gizli} mağaza** kâr ediyor ama bozuluyor.</div>', unsafe_allow_html=True)
    
    # BÖLGE TREND
    st.subheader("📊 Bölge Trendi")
    cols = st.columns(n)
    for i, (col, d) in enumerate(zip(cols, donemler)):
        eb = df[f'D{i+1}_EBITDA'].sum()
        ns = df[f'D{i+1}_NetSatis'].sum()
        o = (eb/ns*100) if ns > 0 else 0
        dlt = ""
        if i > 0:
            prv = df[f'D{i}_EBITDA'].sum()
            pct = ((eb-prv)/abs(prv)*100) if prv != 0 else 0
            dlt = f'<div class="metric-delta {"negative" if pct<0 else "positive"}">{fmt(eb-prv)} ({pct:+.1f}%)</div>'
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-label">{d}</div><div class="metric-value">{fmt(eb)}</div><div>%{o:.1f}</div>{dlt}</div>', unsafe_allow_html=True)
    st.caption(f"Medyan: **%{med:.1f}** | **{len(df)} mğz**")
    
    # KATEGORİ
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
        kdf = df[df['Kategori'] == k].sort_values('Skor')
        st.markdown(f"### {k} ({len(kdf)})")
        for _, r in kdf.iterrows():
            with st.expander(f"**{r['Magaza_Isim']}** | {r['SM']}/{r['BS']} | Skor:{r['Skor']:.1f} | {neden_kisa(r,n)}"):
                if n == 3: st.write(f"Trend: {dk[0]} %{r['D1_EBITDA_Oran']:.1f} → {dk[1]} %{r['D2_EBITDA_Oran']:.1f} → {dk[2]} %{r['D3_EBITDA_Oran']:.1f}")
                for nd in neden_detay(r, info): st.markdown(f"- {nd}")
    
    # SM
    st.markdown("---")
    st.subheader("👥 SM Performans")
    smagg = {f'D{i}_EBITDA': 'sum' for i in range(1, n+1)}
    smagg.update({f'D{i}_NetSatis': 'sum' for i in range(1, n+1)})
    smagg['Kod'] = 'count'
    smdf = df.groupby('SM').agg(smagg).reset_index()
    smdf = smdf[smdf['Kod'] > 2]
    for i in range(1, n+1): smdf[f'D{i}_O'] = (smdf[f'D{i}_EBITDA']/smdf[f'D{i}_NetSatis']*100).fillna(0)
    for k in kats:
        for sm in smdf['SM'].unique(): smdf.loc[smdf['SM']==sm, k] = len(df[(df['SM']==sm)&(df['Kategori']==k)])
    smdf['KT'] = smdf['🔥 Yangın'] + smdf['🚨 Acil'] + smdf['🟥 Kritik']
    smdf = smdf.sort_values('KT', ascending=False)
    
    for _, sr in smdf.iterrows():
        sm = sr['SM']
        ko = " ".join([f"{k.split()[0]}{int(sr.get(k,0))}" for k in kats if sr.get(k,0) > 0])
        prob = sm_prob(df, sm, n)
        if n == 3:
            p1 = ((sr['D2_O']-sr['D1_O'])/abs(sr['D1_O'])*100) if sr['D1_O'] != 0 else 0
            p2 = ((sr['D3_O']-sr['D2_O'])/abs(sr['D2_O'])*100) if sr['D2_O'] != 0 else 0
            tr = f"{dk[0]} %{sr['D1_O']:.1f} → {dk[1]} %{sr['D2_O']:.1f} ({'↓' if p1<0 else '↑'}{abs(p1):.0f}%) → {dk[2]} %{sr['D3_O']:.1f} ({'↓' if p2<0 else '↑'}{abs(p2):.0f}%)"
        else:
            tr = f"{dk[0]} %{sr['D1_O']:.1f} → {dk[1]} %{sr['D2_O']:.1f}"
        
        with st.expander(f"**{sm}** ({int(sr['Kod'])} mğz) | {ko}"):
            st.markdown(f"**{fmt(sr[f'D{n}_EBITDA'])}** | {tr}")
            if prob: st.markdown(f'<div class="sm-problem-alert">⚠️ {" | ".join(prob)} mğzda yüksek</div>', unsafe_allow_html=True)
            
            st.markdown("**BS'ler:**")
            bsl = []
            for bs in df[df['SM']==sm]['BS'].unique():
                if not bs: continue
                bt = df[(df['SM']==sm)&(df['BS']==bs)]
                bso = [(bt[f'D{i}_EBITDA'].sum()/bt[f'D{i}_NetSatis'].sum()*100) if bt[f'D{i}_NetSatis'].sum()>0 else 0 for i in range(1,n+1)]
                bsl.append({'bs':bs, 'c':len(bt), 'eb':bt[f'D{n}_EBITDA'].sum(), 'o':bso, 'kr':len(bt[bt['Kategori'].isin(['🔥 Yangın','🚨 Acil','🟥 Kritik'])]), 'df':bt})
            bsl = sorted(bsl, key=lambda x: x['kr'], reverse=True)
            
            for b in bsl:
                if n == 3:
                    q1 = ((b['o'][1]-b['o'][0])/abs(b['o'][0])*100) if b['o'][0] != 0 else 0
                    q2 = ((b['o'][2]-b['o'][1])/abs(b['o'][1])*100) if b['o'][1] != 0 else 0
                    btr = f"{dk[0]} %{b['o'][0]:.1f} → {dk[1]} %{b['o'][1]:.1f} ({'↓' if q1<0 else '↑'}{abs(q1):.0f}%) → {dk[2]} %{b['o'][2]:.1f} ({'↓' if q2<0 else '↑'}{abs(q2):.0f}%)"
                else:
                    btr = f"{dk[0]} %{b['o'][0]:.1f} → {dk[1]} %{b['o'][1]:.1f}"
                
                with st.expander(f"📁 {b['bs']} ({b['c']} mğz) | {fmt(b['eb'])} | {btr}"):
                    km = b['df'][b['df']['Kategori'].isin(['🔥 Yangın','🚨 Acil','🟥 Kritik'])].sort_values('Skor')
                    if len(km) > 0:
                        st.markdown("**⚠️ Dikkat:**")
                        for _, m in km.iterrows():
                            with st.expander(f"• {m['Magaza_Isim']} | {m['Kategori']} | {m['Skor']:.1f} | {neden_kisa(m,n)}"):
                                for nd in neden_detay(m, info): st.markdown(f"- {nd}")
                    else:
                        st.success("✓ OK")
    
    # EXPORT
    st.markdown("---")
    out = BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as w:
        df.to_excel(w, sheet_name='TÜM', index=False)
    st.download_button("📥 Excel", data=out.getvalue(), file_name=f"EBITDA_{donemler[-1].replace(' ','_')}.xlsx")

if __name__ == "__main__":
    main()
