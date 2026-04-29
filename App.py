  import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image
import os

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Analisador Pro", layout="centered")
DB_FILE = "banco_de_velas.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        try: return pd.read_csv(DB_FILE)['velas'].tolist()
        except: return []
    return []

def salvar_dados(lista):
    pd.DataFrame({"velas": lista}).to_csv(DB_FILE, index=False)

if 'velas' not in st.session_state:
    st.session_state.velas = carregar_dados()

@st.cache_resource
def get_reader():
    return easyocr.Reader(['en'])

# --- TÍTULO ---
st.title("📈 Analisador Pro: Histórico & Padrões")

# --- ADICIONAR VELAS ---
with st.expander("🚨 ADICIONAR NOVAS VELAS", expanded=True):
    aba1, aba2 = st.tabs(["📝 Texto", "📷 Print"])
    with aba1:
        entrada = st.text_area("Cole as velas aqui:", placeholder="Ex: 2.10, 1.50...")
        if st.button("GRAVAR NO HISTÓRICO", use_container_width=True):
            if entrada:
                novas = [float(v.strip()) for v in entrada.replace(",", " ").split() if v.strip()]
                st.session_state.velas.extend(novas)
                salvar_dados(st.session_state.velas)
                st.success("✅ Gravado!")
                st.rerun()
    with aba2:
        foto = st.file_uploader("Suba o print", type=['png', 'jpg', 'jpeg'])
        if foto and st.button("LER IMAGEM E SALVAR", use_container_width=True):
            with st.spinner("🤖 Lendo print..."):
                res = get_reader().readtext(np.array(Image.open(foto)))
                lidas = [float(t.replace('x','').replace(',','.').strip()) for (_, t, _) in res if t.replace('x','').replace(',','.').strip().replace('.','').isdigit()]
                if lidas:
                    st.session_state.velas.extend(lidas)
                    salvar_dados(st.session_state.velas)
                    st.success(f"🚀 {len(lidas)} velas detectadas!")
                    st.rerun()

st.divider()

# --- BUSCA DE PADRÃO (15 SUBSEQUENTES) ---
st.subheader("🔍 BUSCAR PADRÃO")
if st.button("ANALISAR SEQUÊNCIA", use_container_width=True):
    if len(st.session_state.velas) > 1:
        ultima = st.session_state.velas[-1]
        encontrou = False
        st.write(f"Analisando histórico após a vela: **{ultima}x**")
        
        for i in range(len(st.session_state.velas) - 1):
            if st.session_state.velas[i] == ultima:
                # Pega as 15 velas seguintes
                sequencia = st.session_state.velas[i+1 : i+16]
                if any(v >= 8.0 for v in sequencia):
                    st.error(f"⚠️ **PADRÃO 8X DETECTADO!**")
                    # Exibe a sequência com destaque
                    cols = st.columns(5)
                    for idx, v in enumerate(sequencia):
                        txt = f"**{v:.2f}x**" if v >= 8.0 else f"{v:.2f}x"
                        cols[idx % 5].write(f"{idx+1}º: {txt}")
                    encontrou = True
                    st.divider()
        
        if not encontrou:
            st.info(f"Nenhum padrão de 8x nas próximas 15 velas após {ultima}x.")
    else:
        st.warning("Adicione velas para analisar.")

st.divider()

# --- CONTADOR E HISTÓRICO COM FIDELIDADE ---
st.subheader("📊 Contador")
total = len(st.session_state.velas)
st.header(f"{total} / 10.000")

st.subheader("📋 Últimas Velas Salvas")
if total > 0:
    # Formatação com 'x' e destaque para >= 8x
    ultimas_20 = st.session_state.velas[-20:][::-1]
    exibicao = []
    for v in ultimas_20:
        if v >= 8.0:
            exibicao.append(f"🔥 **{v:.2f}x**")
        else:
            exibicao.append(f"{v:.2f}x")
    
    st.write(" | ".join(exibicao))

with st.expander("👁️ VER HISTÓRICO COMPLETO"):
    df_view = pd.DataFrame({"Vela": [f"{v:.2f}x" for v in st.session_state.velas]})
    st.dataframe(df_view.iloc[::-1], use_container_width=True)

st.divider()

# --- BACKUP E RESET ---
csv = pd.DataFrame({"velas": st.session_state.velas}).to_csv(index=False)
st.download_button("💾 BAIXAR BACKUP", csv, "banco_aviator.csv", "text/csv", use_container_width=True)

if st.button("🗑️ RESETAR BANCO"):
    if st.checkbox("Confirmar exclusão total?"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()
      
