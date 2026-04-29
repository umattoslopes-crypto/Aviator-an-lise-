import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image
import os

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Analisador Pro", layout="centered")

# Nome do arquivo que guarda os dados
DB_FILE = "banco_de_velas.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE)['velas'].tolist()
        except: return []
    return []

def salvar_dados(lista):
    pd.DataFrame({"velas": lista}).to_csv(DB_FILE, index=False)

if 'velas' not in st.session_state:
    st.session_state.velas = carregar_dados()

@st.cache_resource
def get_reader():
    return easyocr.Reader(['en'])

# --- TÍTULO E LAYOUT ---
st.title("📈 Analisador Pro: Histórico & Padrões")

# --- SEÇÃO DE ADICIONAR (EXPANDER) ---
with st.expander("🚨 ADICIONAR NOVAS VELAS", expanded=True):
    aba1, aba2 = st.tabs(["📝 Texto", "📷 Print"])
    
    with aba1:
        entrada = st.text_area("Cole as velas aqui:", placeholder="Ex: 2.10, 1.50...")
        if st.button("GRAVAR NO HISTÓRICO", use_container_width=True):
            if entrada:
                novas = [float(v.strip()) for v in entrada.replace(",", " ").split() if v.strip()]
                st.session_state.velas.extend(novas)
                salvar_dados(st.session_state.velas)
                st.success("✅ Gravado com sucesso!")
                st.rerun()

    with aba2:
        foto = st.file_uploader("Suba o print das velas", type=['png', 'jpg', 'jpeg'])
        if foto and st.button("LER IMAGEM E SALVAR", use_container_width=True):
            with st.spinner("🤖 Robô lendo print..."):
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

# --- BUSCA DE PADRÃO E ALERTAS ---
st.subheader("🔍 BUSCAR PADRÃO (ÚLTIMAS 10)")
if st.button("ANALISAR AGORA", use_container_width=True):
    if len(st.session_state.velas) > 1:
        ultima = st.session_state.velas[-1]
        encontrou = False
        st.write(f"Analisando histórico para a vela: **{ultima}x**")
        
        for i in range(len(st.session_state.velas) - 1):
            if st.session_state.velas[i] == ultima:
                proxima = st.session_state.velas[i+1]
                if proxima >= 8.0:
                    st.error(f"⚠️ **ALERTA DE PADRÃO!** Após {ultima}x, o histórico registrou uma vela de **{proxima}x**!")
                    encontrou = True
        
        if not encontrou:
            st.info(f"Nenhum padrão de 8x encontrado para {ultima}x no banco atual.")
    else:
        st.warning("Adicione velas para poder analisar.")

st.divider()

# --- CONTADOR E VISUALIZAÇÃO ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("📊 Contador")
    total = len(st.session_state.velas)
    st.header(f"{total} / 10.000")
    if total < 10000:
        st.caption(f"Faltam {10000 - total} velas.")

with col2:
    st.subheader("📋 Histórico")
    # Mostra as últimas 5 velas de forma simples e rápida
    if total > 0:
        st.write(st.session_state.velas[-5:][::-1])
    else:
        st.write("Vazio")

# --- TABELA COMPLETA PARA CONFERÊNCIA ---
if total > 0:
    with st.expander("👁️ VER TODAS AS VELAS SALVAS"):
        df_view = pd.DataFrame({"Vela": st.session_state.velas})
        st.dataframe(df_view.iloc[::-1], use_container_width=True) # Mais recentes no topo

st.divider()

# --- BACKUP E SEGURANÇA ---
csv = pd.DataFrame({"velas": st.session_state.velas}).to_csv(index=False)
st.download_button("💾 BAIXAR BACKUP (Não perca seus dados!)", csv, "meu_banco_velas.csv", "text/csv", use_container_width=True)

if st.button("🗑️ RESETAR BANCO DE DADOS"):
    if st.checkbox("Sim, quero apagar todas as velas salvas"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()
