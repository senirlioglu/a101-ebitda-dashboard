"""
A101 SUPER APP - Tüm Analiz Araçları Tek Çatı Altında
"""
import streamlit as st

st.set_page_config(page_title="A101 Super App", page_icon="🏪", layout="wide", initial_sidebar_state="expanded")

# CSS
st.markdown("""
<style>
    .super-header {
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 50%, #db2777 100%);
        color: white; padding: 30px; border-radius: 16px; margin-bottom: 30px; text-align: center;
    }
    .super-header h1 { margin: 0; font-size: 2.5rem; font-weight: 800; }
    .super-header p { margin: 10px 0 0 0; opacity: 0.9; }
    .module-card {
        background: white; border: 2px solid #e2e8f0; border-radius: 16px;
        padding: 24px; text-align: center; height: 180px;
    }
    .module-icon { font-size: 3rem; margin-bottom: 12px; }
    .module-title { font-size: 1.2rem; font-weight: 700; color: #1e293b; }
    .module-desc { font-size: 0.85rem; color: #64748b; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

def show_home():
    st.markdown('<div class="super-header"><h1>🏪 A101 Super App</h1><p>Tüm Analiz Araçları Tek Çatı Altında</p></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="module-card"><div class="module-icon">📊</div><div class="module-title">EBITDA Karar Motoru</div><div class="module-desc">5 Ajanlı Sistem ile mağaza karlılık analizi</div></div>', unsafe_allow_html=True)
        if st.button("EBITDA'ya Git", key="btn_ebitda", use_container_width=True):
            st.session_state.active_module = "ebitda"
            st.rerun()

    with col2:
        st.markdown('<div class="module-card"><div class="module-icon">📈</div><div class="module-title">Satış Performans</div><div class="module-desc">Ürün ve mağaza bazlı satış analizi</div></div>', unsafe_allow_html=True)
        if st.button("Performans'a Git", key="btn_perf", use_container_width=True):
            st.session_state.active_module = "performans"
            st.rerun()

    with col3:
        st.markdown('<div class="module-card"><div class="module-icon">🔍</div><div class="module-title">Envanter Risk</div><div class="module-desc">Mağaza envanter risk analizi</div></div>', unsafe_allow_html=True)
        if st.button("Envanter'e Git", key="btn_env", use_container_width=True):
            st.session_state.active_module = "envanter"
            st.rerun()

def main():
    if 'active_module' not in st.session_state:
        st.session_state.active_module = None

    with st.sidebar:
        st.markdown("## 🏪 A101 Super App")
        st.markdown("---")

        if st.button("🏠 Ana Sayfa", use_container_width=True):
            st.session_state.active_module = None
            st.rerun()

        st.markdown("### Modüller")
        if st.button("📊 EBITDA", use_container_width=True):
            st.session_state.active_module = "ebitda"
            st.rerun()
        if st.button("📈 Performans", use_container_width=True):
            st.session_state.active_module = "performans"
            st.rerun()
        if st.button("🔍 Envanter", use_container_width=True):
            st.session_state.active_module = "envanter"
            st.rerun()

        st.markdown("---")
        if st.session_state.active_module:
            names = {"ebitda": "📊 EBITDA", "performans": "📈 Performans", "envanter": "🔍 Envanter"}
            st.info(f"Aktif: {names.get(st.session_state.active_module)}")

    if st.session_state.active_module == "ebitda":
        from modules import ebitda
        ebitda.run()
    elif st.session_state.active_module == "performans":
        from modules import performans
        performans.run()
    elif st.session_state.active_module == "envanter":
        from modules import envanter
        envanter.run()
    else:
        show_home()

if __name__ == "__main__":
    main()
