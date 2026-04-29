import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image
import os

# 1. CONFIGURAÇÃO E BANCO DE DADOS LOCAL
st.set_page_config(page_title="Analisador Pro", layout="centered")
DB_FILE = "banco_de_velas.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)['velas'].tolist()
    return []

def salvar_dados(lista):
    pd.DataFrame({"velas": lista}).to_csv(DB_FILE, index=False)

if 'velas' not in st.session_state:
    st.session_state.velas = carregar_dados()

@st.cache_resource
def get_reader():
    return easyocr.Reader(['en'])

# 2. INTERFACE (MANTENDO SEU LAYOUT)
st.title("📈 Analisador Pro: Histórico & Padrões")

with st.expander("🚨 ADICIONAR NOVAS VELAS", expanded=True):
    aba1, aba2 = st.tabs(["📝 Texto", "📷 Print"])
    
    with aba1:
        entrada = st.text_area("Cole as velas aqui:", placeholder="Ex: 2.10, 1.50...")
        if st.button("GRAVAR TEXTO", use_container_width=True):
            if entrada:
                novas = [float(v.strip()) for v in entrada.replace(",", " ").split() if v.strip()]
                st.session_state.velas.extend(novas)
                salvar_dados(st.session_state.velas)
                st.success("✅ Salvo no banco!")
                st.rerun()

    with aba2:
        foto = st.file_uploader("Suba o print", type=['png', 'jpg', 'jpeg'])
        if foto and st.button("LER IMAGEM E SALVAR", use_container_width=True):
            with st.spinner("🤖 Lendo print..."):
                res = get_reader().readtext(np.array(Image.open(foto)))
                lidas = []
                for (_, t, _) in res:
                    try:
                        v = float(t.replace('x','').replace(',','.').strip())
                        if 1.0 <= v <= 1000: lidas.append(v)
                    except: continue
                if lidas:
                    st.session_state.velas.extend(lidas)
                    salvar_dados(st.session_state.velas)
                    st.success(f"🚀 {len(lidas)} velas detectadas e salvas!")
                    st.rerun()

st.divider()

# 3. BUSCA DE PADRÃO (ALERTA 8X)
st.subheader("🔍 BUSCAR PADRÃO")
if st.button("ANALISAR AGORA", use_container_width=True):
    if len(st.session_state.velas) > 1:
        ultima = st.session_state.velas[-1]
        achou = False
        for i in range(len(st.session_state.velas) - 1):
            if st.session_state.velas[i] == ultima and st.session_state.velas[i+1] >= 8.0:
                st.error(f"⚠️ ALERTA: Após {ultima}x, já veio {st.session_state.velas[i+1]}x!")
                achou = True
        if not achou: st.info(f"Sem padrões de 8x para {ultima}x.")

st.divider()

# 4. CONTADOR
st.subheader("📊 Contador")
st.write("Velas Acumuladas")
total = len(st.session_state.velas)
st.header(f"{total} / 10.000")

# 5. BACKUP SEGURO (Botão extra para você nunca perder nada)
csv = pd.DataFrame({"velas": st.session_state.velas}).to_csv(index=False)
st.download_button("💾 BAIXAR BACKUP (Caso o app reinicie)", csv, "velas_backup.csv", "text/csv", use_container_width=True)

if st.button("🗑️ RESETAR BANCO"):
    if st.checkbox("Confirmar exclusão?"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()

