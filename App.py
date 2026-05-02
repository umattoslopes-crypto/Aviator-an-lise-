import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np
import cv2

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
            st.session_state.velas = [float(v) for v in df['velas'].dropna() if float(v) > 0]
        except:
            st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'velas': st.session_state.velas[-MAX_VELAS:]}).to_csv(DB_FILE, index=False)

# =========================
# OCR
# =========================
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

# =========================
# 🔥 DETECÇÃO DE CÉLULAS
# =========================
def extrair_celulas(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # binarização forte
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # detectar linhas horizontais
    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (50,1))
    detect_h = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_h)

    # detectar linhas verticais
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1,50))
    detect_v = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_v)

    grid = cv2.add(detect_h, detect_v)

    # encontrar contornos (células)
    contours, _ = cv2.findContours(grid, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    caixas = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        # filtro de tamanho (ajuste fino)
        if 30 < w < 200 and 20 < h < 100:
            caixas.append((x, y, w, h))

    # ordenação fiel ao print
    caixas.sort(key=lambda b: (-b[1], -b[0]))

    return caixas

# =========================
# OCR EM CADA CÉLULA
# =========================
def ler_celulas(img, caixas):
    velas = []

    for (x, y, w, h) in caixas:
        crop = img[y:y+h, x:x+w]

        texto = reader.readtext(crop, detail=0)
        texto = " ".join(texto).lower().replace(',', '.')

        match = re.search(r"\d+(?:\.\d+)?x", texto)

        if match:
            try:
                val = float(match.group().replace('x', ''))
                if val > 0:
                    velas.append(val)
            except:
                continue

    return velas

# =========================
# INTERFACE
# =========================
st.title("📊 ANALISADOR PROFISSIONAL DE VELAS")

aba1, aba2 = st.tabs(["📥 MANUAL", "📸 PRINT"])

with aba1:
    manual = st.text_area("Cole até 500 velas")

with aba2:
    arquivo = st.file_uploader("Envie o print", type=['png','jpg','jpeg'])

# =========================
# PROCESSAMENTO
# =========================
if st.button("🚀 ADICIONAR", use_container_width=True):

    novas = []

    if arquivo:
        img_pil = Image.open(arquivo)
        img = np.array(img_pil)

        caixas = extrair_celulas(img)
        novas = ler_celulas(img, caixas)

    if manual:
        manual_vals = re.findall(r"\d+(?:\.\d+)?", manual.replace(',', '.'))
        novas += [float(v) for v in manual_vals]

    # limite 500
    if len(novas) > MAX_POR_ENVIO:
        st.warning(f"{len(novas)} velas detectadas. Limitado a 500.")
        novas = novas[:MAX_POR_ENVIO]

    adicionadas = 0

    for v in novas:
        if v > 0:
            st.session_state.velas.append(v)
            adicionadas += 1

    if len(st.session_state.velas) > MAX_VELAS:
        st.session_state.velas = st.session_state.velas[-MAX_VELAS:]

    salvar()
    st.success(f"{adicionadas} velas adicionadas!")
    st.rerun()

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

    st.dataframe(
        df.style.map(cor).format("{:.2f}x"),
        use_container_width=True,
        height=400
    )

st.divider()

# =========================
# ÚLTIMAS 20
# =========================
st.subheader("📉 ÚLTIMAS 20")

if st.session_state.velas:
    ultimas = st.session_state.velas[-20:]

    texto = []
    for v in ultimas:
        cor = "#FF00FF" if v >= 8 else "#00FF00" if v >= 2 else "#FFFFFF"
        texto.append(f"<b style='color:{cor}'>{v:.2f}x</b>")

    st.markdown(" , ".join(texto), unsafe_allow_html=True)

st.divider()

# =========================
# BUSCA
# =========================
st.subheader("🔍 BUSCA DE PADRÃO")

seq = st.text_input("Ex: 1.25 2.00")

if st.button("🔎 BUSCAR"):
    if seq:
        try:
            padrao = [float(x) for x in seq.split()]
            hist = st.session_state.velas

            for i in range(len(hist) - len(padrao)):
                if hist[i:i+len(padrao)] == padrao:
                    st.success("Encontrado!")
                    st.write(hist[i+len(padrao):i+len(padrao)+10])
                    break
            else:
                st.error("Não encontrado")

        except:
            st.error("Erro no padrão")

st.divider()

# =========================
# RESET
# =========================
if st.checkbox("Reset"):

    if st.button("Apagar últimas 20"):
        st.session_state.velas = st.session_state.velas[:-20]
        salvar()
        st.rerun()

    if st.button("Zerar tudo"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()
