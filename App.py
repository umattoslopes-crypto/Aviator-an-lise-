import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import easyocr
import numpy as np
from PIL import Image

# Configuração e Banco de Dados
st.set_page_config(page_title="Analisador Pro", layout="centered")
URL_DB = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA" # Link da Planilha Google (Editor)

conn = st.connection("gsheets", type=GSheetsConnection)

def carregar():
    try:
        df = conn.read(spreadsheet=URL_DB)
        return [float(x) for x in df['velas'].tolist() if str(x).replace('.','').isdigit()]
    except: return []

if 'velas' not in st.session_state:
    st.session_state.velas = carregar()

@st.cache_resource
def get_reader(): return easyocr.Reader(['en'])

# Interface conforme seu layout
st.title("📈 Analisador Pro: Histórico & Padrões")

with st.expander("🚨 ADICIONAR NOVAS VELAS", expanded=True):
    modo = st.tabs(["📝 Texto", "📷 Foto"])
    
    with modo[0]:
        entrada = st.text_area("Velas:", placeholder="2.50, 1.10...")
        if st.button("GRAVAR TEXTO"):
            if entrada:
                novas = [float(v.strip()) for v in entrada.replace(",", " ").split() if v.strip()]
                st.session_state.velas.extend(novas)
                conn.update(spreadsheet=URL_DB, data=pd.DataFrame({"velas": st.session_state.velas}))
                st.success("Salvo!")
                st.rerun()

    with modo[1]:
        foto = st.file_uploader("Print:", type=['png', 'jpg'])
        if foto and st.button("LER E SALVAR"):
            res = get_reader().readtext(np.array(Image.open(foto)))
            lidas = []
            for (_, t, _) in res:
                try:
                    v = float(t.replace('x','').replace(',','.').strip())
                    if 1.0 <= v <= 1000: lidas.append(v)
                except: continue
            if lidas:
                st.session_state.velas.extend(lidas)
                conn.update(spreadsheet=URL_DB, data=pd.DataFrame({"velas": st.session_state.velas}))
                st.success(f"Lidas: {lidas}")
                st.rerun()

st.divider()
st.subheader("🔍 BUSCAR PADRÃO (ÚLTIMAS 10)")
if st.button("ANALISAR"):
    if len(st.session_state.velas) > 1:
        u = st.session_state.velas[-1]
        for i in range(len(st.session_state.velas)-1):
            if st.session_state.velas[i] == u and st.session_state.velas[i+1] >= 8:
                st.error(f"⚠️ Alerta: Após {u}x, veio {st.session_state.velas[i+1]}x")
    else: st.warning("Sem dados.")

st.divider()
st.subheader("📊 Contador")
total = len(st.session_state.velas)
st.header(f"{total} / 10.000")
st.info(f"Faltam {10000-total} velas.")

if st.button("🗑️ RESET"):
    if st.checkbox("Confirmar?"):
        conn.update(spreadsheet=URL_DB, data=pd.DataFrame(columns=["velas"]))
        st.session_state.velas = []
        st.rerun()

