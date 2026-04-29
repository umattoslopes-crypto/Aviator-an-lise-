import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image
import os

# Configuração de Página
st.set_page_config(page_title="Analisador Pro", layout="centered")

# Banco de Dados Local
DB_FILE = "banco_de_velas.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            return [float(v) for v in df['velas'].tolist()]
        except: return []
    return []

def salvar_dados(lista):
    pd.DataFrame({"velas": lista}).to_csv(DB_FILE, index=False)

if 'velas' not in st.session_state:
    st.session_state.velas = carregar_dados()

@st.cache_resource
def get_reader():
    return easyocr.Reader(['en'])

st.title("📈 Analisador Pro: Histórico & Padrões")

# --- SEÇÃO 1: ADICIONAR DADOS ---
with st.expander("🚨 ADICIONAR NOVAS VELAS", expanded=True):
    metodo = st.tabs(["📝 Texto", "📷 Múltiplos Prints", "📂 Restaurar Backup"])
    
    with metodo[0]:
        entrada = st.text_area("Cole as velas aqui:", placeholder="Ex: 2.10, 1.50, 10.00...")
        if st.button("GRAVAR TEXTO", use_container_width=True):
            if entrada:
                novas = [float(v.strip()) for v in entrada.replace(",", " ").split() if v.strip()]
                st.session_state.velas.extend(novas)
                salvar_dados(st.session_state.velas)
                st.success(f"✅ {len(novas)} velas adicionadas!")
                st.rerun()

    with metodo[1]:
        fotos = st.file_uploader("Selecione os prints da galeria:", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if fotos and st.button("LER TODAS AS FOTOS", use_container_width=True):
            with st.spinner("🤖 IA lendo todos os prints..."):
                reader = get_reader()
                lidas_total = []
                for foto in fotos:
                    res = reader.readtext(np.array(Image.open(foto)))
                    for (_, t, _) in res:
                        val = t.replace('x','').replace(',','.').strip()
                        try:
                            num = float(val)
                            if 1.0 <= num <= 1000.0: lidas_total.append(num)
                        except: continue
                if lidas_total:
                    st.session_state.velas.extend(lidas_total)
                    salvar_dados(st.session_state.velas)
                    st.success(f"🚀 {len(lidas_total)} velas detectadas com sucesso!")
                    st.rerun()

    with metodo[2]:
        arquivo_backup = st.file_uploader("Suba seu arquivo .csv de backup:", type=['csv'])
        if arquivo_backup and st.button("RESTAURAR HISTÓRICO"):
            df_bkp = pd.read_csv(arquivo_backup)
            st.session_state.velas = df_bkp['velas'].tolist()
            salvar_dados(st.session_state.velas)
            st.success("📚 Histórico restaurado com sucesso!")
            st.rerun()

st.divider()

# --- SEÇÃO 2: BUSCA DE PADRÃO ---
st.subheader("🔍 BUSCAR PADRÃO (15 SUBSEQUENTES)")
if st.button("ANALISAR AGORA", use_container_width=True):
    if len(st.session_state.velas) > 1:
        ultima = st.session_state.velas[-1]
        encontrou = False
        st.write(f"Analisando sequências após a vela: **{ultima:.2f}x**")
        
        for i in range(len(st.session_state.velas) - 1):
            if st.session_state.velas[i] == ultima:
                seq = st.session_state.velas[i+1 : i+16]
                if any(v >= 8.0 for v in seq):
                    st.error(f"⚠️ **PADRÃO 8X ENCONTRADO!**")
                    cols = st.columns(5)
                    for idx, v in enumerate(seq):
                        txt = f"🔥 **{v:.2f}x**" if v >= 8.0 else f"{v:.2f}x"
                        cols[idx % 5].write(f"{idx+1}º: {txt}")
                    encontrou = True
                    st.divider()
        if not encontrou: st.info(f"Nenhum padrão de 8x nas próximas 15 velas.")
    else: st.warning("Adicione velas primeiro.")

st.divider()

# --- SEÇÃO 3: CONTADOR E EXIBIÇÃO ---
st.subheader("📊 Contador")
total = len(st.session_state.velas)
st.header(f"{total} / 10.000")

st.subheader("📋 Últimas Velas Salvas")
if total > 0:
    ultimas_20 = st.session_state.velas[-20:][::-1]
    exibicao = [f"🔥 **{v:.2f}x**" if v >= 8.0 else f"{v:.2f}x" for v in ultimas_20]
    st.write(" | ".join(exibicao))

st.divider()

# --- SEÇÃO 4: BACKUP (SEGURANÇA IMORTAL) ---
st.subheader("💾 Segurança do Histórico")
csv = pd.DataFrame({"velas": st.session_state.velas}).to_csv(index=False)
st.download_button("📥 BAIXAR BACKUP AGORA", csv, "historico_aviator.csv", "text/csv", use_container_width=True)

if st.button("🗑️ RESETAR TUDO"):
    if st.checkbox("Confirmo que quero apagar as velas"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()
