import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

DB_FILE = "banco_velas_projeto.csv"
MAX_VELAS = 10000
MAX_POR_ENVIO = 500

# =========================
# BANCO
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.velas = [float(v) for v in df['velas'].dropna()]
        except:
            st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'velas': st.session_state.velas[-MAX_VELAS:]}).to_csv(DB_FILE, index=False)

# =========================
# OCR (SEGURO)
# =========================
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

def ler_ocr_seguro(img):
    try:
        res = reader.readtext(np.array(img), detail=0)
        return " ".join(res)
    except:
        return ""

# =========================
# EXTRAÇÃO PERFEITA
# =========================
def extrair_velas(texto):
    texto = texto.lower().replace(',', '.')

    # pega TODOS os números com x
    encontrados = re.findall(r"\d+(?:\.\d+)?x", texto)

    velas = []
    for e in encontrados:
        try:
            val = float(e.replace('x',''))
            if val > 0:
                velas.append(val)
        except:
            continue

    return velas

# =========================
# INTERFACE
# =========================
st.title("📊 ANALISADOR DE VELAS (SEM ERRO)")

aba1, aba2 = st.tabs(["📥 COLAR DADOS", "📸 PRINT"])

with aba1:
    manual = st.text_area("Cole aqui (até 500 velas)\nEx: 1.25x 2.30x 5.00x")

with aba2:
    arquivo = st.file_uploader("Envie o print", type=['png','jpg','jpeg'])

# =========================
# PROCESSAMENTO
# =========================
if st.button("🚀 ADICIONAR", use_container_width=True):

    texto_total = ""

    # OCR (seguro)
    if arquivo:
        img = Image.open(arquivo)
        texto_total += ler_ocr_seguro(img)

    # manual (prioritário)
    if manual:
        texto_total += " " + manual

    if texto_total.strip():

        novas = extrair_velas(texto_total)

        # limite
        if len(novas) > MAX_POR_ENVIO:
            st.warning(f"{len(novas)} velas detectadas. Limitado a 500.")
            novas = novas[:MAX_POR_ENVIO]

        adicionadas = 0

        for v in novas:
            st.session_state.velas.append(v)
            adicionadas += 1

        if len(st.session_state.velas) > MAX_VELAS:
            st.session_state.velas = st.session_state.velas[-MAX_VELAS:]

        salvar()
        st.success(f"{adicionadas} velas adicionadas!")
        st.rerun()

st.divider()

# =========================
# BUSCA
# =========================
st.subheader("🔍 BUSCA")

seq = st.text_input("Ex: 1.25 2.00")

if st.button("Buscar"):
    if seq:
        padrao = [float(x) for x in seq.split()]
        hist = st.session_state.velas

        for i in range(len(hist)-len(padrao)):
            if hist[i:i+len(padrao)] == padrao:
                st.success("Encontrado!")
                st.write(hist[i+len(padrao):i+len(padrao)+10])
                break
        else:
            st.error("Não encontrado")

st.divider()

# =========================
# HISTÓRICO
# =========================
st.subheader("📋 HISTÓRICO")

if st.session_state.velas:
    df = pd.DataFrame({"Vela": st.session_state.velas})

    def cor(v):
        if v >= 8:
            return "color:#FF00FF; font-weight:bold"
        elif v >= 2:
            return "color:#00FF00"
        else:
            return "color:white"

    st.dataframe(df.style.map(cor).format("{:.2f}x"), height=400)

st.divider()

# =========================
# ÚLTIMAS 20
# =========================
st.subheader("📉 ÚLTIMAS 20")

if st.session_state.velas:
    ultimas = st.session_state.velas[-20:]

    texto = []
    for v in ultimas:
        cor = "#FF00FF" if v >= 8 else "#00FF00" if v >= 2 else "#FFF"
        texto.append(f"<b style='color:{cor}'>{v:.2f}x</b>")

    st.markdown(" , ".join(texto), unsafe_allow_html=True)
