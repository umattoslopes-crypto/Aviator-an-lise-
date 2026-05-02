import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# --- 1. BANCO DE DADOS (PERSISTENTE) ---
DB_FILE = "banco_dados_fiel.csv"

if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df_load = pd.read_csv(DB_FILE)
            st.session_state.velas = [float(v) for v in df_load['velas'].dropna().tolist()]
        except: st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    if st.session_state.velas:
        pd.DataFrame({'velas': st.session_state.velas}).to_csv(DB_FILE, index=False)

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

# --- LAYOUT FIEL AO SEU DESENHO ---
st.markdown("<h2 style='text-align: center;'>ATE 500 VELAS</h2>", unsafe_allow_html=True)

aba_manual, aba_print = st.tabs(["📥 MANUAL", "📸 PRINT"])

with aba_manual:
    manual_txt = st.text_area("Exemplo: 1.25x 4.10x 5.00x", height=100)

with aba_print:
    arquivo = st.file_uploader("Suba o print aqui", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    texto_bruto = ""
    if arquivo:
        with st.spinner("Lendo..."):
            res = reader.readtext(np.array(Image.open(arquivo)), detail=0)
            texto_bruto = " ".join(res)
    if manual_txt:
        texto_bruto += " " + manual_txt

    if texto_bruto:
        # A REGRA: Captura apenas números que tenham 'x' ou 'X' grudados (ex: 2.50x)
        encontrados = re.findall(r"(\d+\.\d+|\d+)[xX]", texto_bruto.replace(',', '.'))
        novas = [float(v) for v in encontrados]
        
        if novas:
            # Sincronização (Anti-duplicação)
            ultimas = st.session_state.velas[-15:]
            ponto = 0
            for i in range(len(novas)):
                if novas[i:i+2] in [ultimas[j:j+2] for j in range(len(ultimas)-1)]:
                    ponto = i + 2
            
            final = novas[ponto:]
            if final:
                st.session_state.velas.extend(final)
                salvar()
                st.success(f"✅ {len(final)} velas adicionadas!")
                st.rerun()

st.divider()

# --- 2. BUSCA DE PADRÃO ---
st.subheader("🔍 BUSCA DE PADRAO")
col_in, col_bt = st.columns([0.85, 0.15])
with col_in:
    seq_alvo = st.text_input("Padrao de 10 velas:", placeholder="Ex: 1.25 2.00...")
with col_bt:
    if st.button("🔎"):
        if seq_alvo:
            # Limpa o input para buscar apenas os números
            padrao = [float(x.strip()) for x in seq_alvo.replace(',', ' ').replace('x', '').replace('X', '').split() if x.strip()]
            hist = st.session_state.velas
            achou = False
            for i in range(len(hist) - len(padrao)):
                if hist[i : i + len(padrao)] == padrao:
                    achou = True
                    st.success(f"🎯 ENCONTRADO!")
                    futuro = hist[i + len(padrao) : i + len(padrao) + 15]
                    if futuro:
                        st.warning("⚠️ PRÓXIMAS 15 VELAS:")
                        fmt = [f"<b style='color:{'#FF00FF' if v >= 8.0 else '#00FF00' if v >= 2.0 else '#FFFFFF'};'>{v:.2f}x</b>" for v in futuro]
                        st.markdown(" , ".join(fmt), unsafe_allow_html=True)
            if not achou: st.error("Não encontrado.")

st.divider()

# --- 3. HISTÓRICO (SEM LINHAS VAZIAS) ---
st.subheader("📋 HISTORICO DE VELAS")
if st.session_state.velas:
    # Exibe apenas valores reais (ordem inversa)
    df = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
    st.dataframe(
        df.style.map(lambda x: 'color: #FF00FF; font-weight: bold' if x >= 8.0 else 'color: white').format("{:.2f}x"),
        use_container_width=True, height=400
    )

st.divider()

# --- 4. RODAPÉ: ÚLTIMAS 20 (COMPACTADO) ---
st.subheader("📉 ULTIMA 20 VELA ADICIONADA")
if st.session_state.velas:
    resumo = [f"<b style='color:{'#FF00FF' if v >= 8.0 else '#00FF00' if v >= 2.0 else '#FFFFFF'};'>{v:.2f}x</b>" for v in st.session_state.velas[-20:][::-1]]
    st.markdown(" , ".join(resumo), unsafe_allow_html=True)

# RESET
st.divider()
if st.checkbox("Liberar Reset"):
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ APAGAR ÚLTIMAS 20"):
            st.session_state.velas = st.session_state.velas[:-20]
            salvar()
            st.rerun()
    with c2:
        if st.button("🔥 ZERAR TUDO"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.velas = []
            st.rerun()
