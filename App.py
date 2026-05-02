import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# =========================
# CONFIG
# =========================
DB_FILE = "banco_velas_projeto.csv"
MAX_VELAS = 10000

# =========================
# BANCO DE DADOS (SEGURO)
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.velas = [
                float(v) for v in df['velas'].dropna()
                if float(v) > 0
            ]
        except:
            st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    df = pd.DataFrame({'velas': st.session_state.velas[-MAX_VELAS:]})
    df.to_csv(DB_FILE, index=False)

# =========================
# OCR
# =========================
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

def preprocessar(img):
    img = img.convert('L')
    img = np.array(img)
    img = np.where(img > 150, 255, 0).astype(np.uint8)
    return img

# =========================
# ORGANIZAÇÃO POR POSIÇÃO
# =========================
def organizar_por_posicao(res):
    linhas = []

    for (bbox, texto, conf) in res:
        texto = texto.strip().lower()

        if 'x' not in texto:
            continue

        x = bbox[0][0]
        y = bbox[0][1]

        colocado = False

        for linha in linhas:
            if abs(linha['y'] - y) < 25:
                linha['itens'].append((x, texto))
                colocado = True
                break

        if not colocado:
            linhas.append({'y': y, 'itens': [(x, texto)]})

    # 🔥 BAIXO → CIMA
    linhas.sort(key=lambda l: -l['y'])

    resultado = []

    for linha in linhas:
        # 🔥 DIREITA → ESQUERDA
        linha['itens'].sort(key=lambda i: -i[0])

        for _, texto in linha['itens']:
            resultado.append(texto)

    return resultado

# =========================
# EXTRAÇÃO INTELIGENTE
# =========================
def extrair_velas(lista_textos):
    velas = []

    for texto in lista_textos:
        texto = texto.replace(',', '.').strip()

        match = re.search(r"\d+\.\d+x", texto)

        if match:
            try:
                val = float(match.group().replace('x', ''))

                if 1.0 <= val <= 1000:
                    velas.append(val)

            except:
                continue

    return velas

# =========================
# INTERFACE
# =========================
st.title("📊 ANALISADOR DE VELAS")

aba1, aba2 = st.tabs(["📥 MANUAL", "📸 PRINT"])

with aba1:
    manual = st.text_area("Ex: 1.25x 4.10x")

with aba2:
    arquivo = st.file_uploader("", type=['png','jpg','jpeg'])

# =========================
# PROCESSAMENTO
# =========================
if st.button("🚀 ADICIONAR", use_container_width=True):

    textos = []

    if arquivo:
        img = preprocessar(Image.open(arquivo))
        res = reader.readtext(img, detail=1)
        textos = organizar_por_posicao(res)

    if manual:
        textos += manual.split()

    if textos:
        novas = extrair_velas(textos)

        # adiciona sem lixo
        for v in novas:
            if isinstance(v, (int, float)) and v > 0:
                st.session_state.velas.append(v)

        # limite de 10k
        if len(st.session_state.velas) > MAX_VELAS:
            st.session_state.velas = st.session_state.velas[-MAX_VELAS:]

        salvar()
        st.success(f"{len(novas)} velas adicionadas!")
        st.rerun()

st.divider()

# =========================
# HISTÓRICO COLORIDO
# =========================
st.subheader("📋 HISTÓRICO")

if st.session_state.velas:
    df = pd.DataFrame({"Vela": st.session_state.velas})

    def cor(val):
        if val >= 8:
            return "color:#FF00FF; font-weight:bold"
        elif val >= 2:
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
# ÚLTIMAS 20 (PERFEITO)
# =========================
st.subheader("📉 ÚLTIMAS 20")

if st.session_state.velas:
    ultimas = [v for v in st.session_state.velas[-20:] if v > 0]

    texto = []
    for v in ultimas:
        cor = "#FF00FF" if v >= 8 else "#00FF00" if v >= 2 else "#FFFFFF"
        texto.append(f"<b style='color:{cor}'>{v:.2f}x</b>")

    st.markdown(" , ".join(texto), unsafe_allow_html=True)

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
