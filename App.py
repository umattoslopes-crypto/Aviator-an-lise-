import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image
import os

st.set_page_config(page_title="Analisador Pro", layout="centered")
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

st.title("📈 Analisador Pro: Busca de Padrão (10/15)")

# --- ADICIONAR DADOS ---
with st.expander("🚨 ADICIONAR NOVAS VELAS", expanded=True):
    aba1, aba2, aba3 = st.tabs(["📝 Texto", "📷 Prints", "📂 Backup"])
    with aba1:
        entrada = st.text_area("Cole as velas:")
        if st.button("GRAVAR TEXTO", use_container_width=True):
            if entrada:
                novas = [float(v.strip()) for v in entrada.replace(",", " ").split() if v.strip()]
                st.session_state.velas.extend(novas)
                salvar_dados(st.session_state.velas)
                st.rerun()
    with aba2:
        fotos = st.file_uploader("Suba os prints:", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if fotos and st.button("LER E SINCRONIZAR", use_container_width=True):
            reader = get_reader()
            lidas = []
            for foto in fotos:
                res = reader.readtext(np.array(Image.open(foto)))
                for (_, t, _) in res:
                    val = t.replace('x','').replace(',','.').strip()
                    if val.replace('.','').isdigit(): lidas.append(float(val))
            if lidas:
                ultimas = st.session_state.velas[-15:]
                ponto_corte = 0
                for i in range(len(lidas)):
                    if lidas[i] in ultimas: ponto_corte = i + 1
                    else: break
                st.session_state.velas.extend(lidas[ponto_corte:])
                salvar_dados(st.session_state.velas)
                st.rerun()

st.divider()

# --- LÓGICA DE BUSCA (10 PADRÃO / 15 PROJEÇÃO) ---
st.subheader("🔍 BUSCAR PADRÃO (10 VELAS)")
if st.button("ANALISAR SEQUÊNCIA COMPLETA", use_container_width=True):
    if len(st.session_state.velas) >= 25:
        padrao_atual = st.session_state.velas[-10:] # As 10 últimas
        st.write(f"Buscando repetição para a sequência: **{' | '.join([f'{v}x' for v in padrao_atual])}**")
        
        encontrou = False
        # Percorre o banco procurando as 10 velas iguais (exceto a posição atual)
        for i in range(len(st.session_state.velas) - 25):
            if st.session_state.velas[i:i+10] == padrao_atual:
                encontrou = True
                st.error(f"⚠️ **PADRÃO ENCONTRADO NO PASSADO!**")
                st.write(f"Naquela ocasião, as **15 velas seguintes** foram:")
                
                proximas_15 = st.session_state.velas[i+10 : i+25]
                cols = st.columns(5)
                for idx, v in enumerate(proximas_15):
                    # Destaque para velas >= 8x
                    if v >= 8.0:
                        cols[idx % 5].write(f"{idx+1}º: 🔥 **{v:.2f}x**")
                    else:
                        cols[idx % 5].write(f"{idx+1}º: {v:.2f}x")
                st.divider()
        
        if not encontrou:
            st.info("Nenhuma sequência de 10 velas idêntica encontrada no histórico.")
    else:
        st.warning("Necessário ao menos 25 velas no histórico para esta análise.")

st.divider()

# --- CONTADOR E VISUALIZAÇÃO ---
st.subheader("📊 Histórico (Tudo com x)")
total = len(st.session_state.velas)
st.metric("Total Acumulado", f"{total} / 10.000")

with st.expander("👁️ VER TODO O BANCO"):
    df_view = pd.DataFrame({"Vela": [f"{v:.2f}x" for v in st.session_state.velas]})
    st.dataframe(df_view.iloc[::-1], use_container_width=True)

# --- RESET ---
if st.button("🗑️ ZERAR TUDO"):
    if st.checkbox("Confirmar reset definitivo?"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()


