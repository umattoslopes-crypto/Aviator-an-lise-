import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# ================================
# BANCO DE DADOS
# ================================
DB_FILE = "banco_velas_projeto.csv"

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
    if st.session_state.velas:
        pd.DataFrame({'velas': st.session_state.velas}).to_csv(DB_FILE, index=False)

# ================================
# OCR
# ================================
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

def preprocessar(img):
    img = img.convert('L')
    img = np.array(img)

    # contraste forte
    img = np.where(img > 150, 255, 0).astype(np.uint8)

    return img

def organizar_por_posicao(res):
    itens = []

    for (bbox, texto, conf) in res:
        if 'x' in texto.lower():  # FILTRO CRUCIAL
            x = bbox[0][0]
            y = bbox[0][1]
            itens.append((y, x, texto))

    # ordena corretamente (resolve bagunça do OCR)
    itens.sort(key=lambda i: (i[0], i[1]))

    return " ".join([i[2] for i in itens])

def extrair_velas(texto):
    texto = texto.lower()
    texto = texto.replace(',', '.')
    texto = texto.replace(' ', '')

    encontrados = re.findall(r"\d+\.\d+x", texto)

    velas = []
    for v in encontrados:
        try:
            val = float(v.replace('x', ''))

            if 1.0 <= val <= 1000:
                velas.append(val)

        except:
            continue

    return velas

# ================================
# INTERFACE
# ================================
st.markdown("<h2 style='text-align: center;'>ATE 500 VELAS</h2>", unsafe_allow_html=True)

aba1, aba2 = st.tabs(["📥 MANUAL", "📸 PRINT"])

with aba1:
    manual = st.text_area("Ex: 1.25x 4.10x")

with aba2:
    arquivo = st.file_uploader("", type=['png','jpg','jpeg'])

# ================================
# PROCESSAMENTO
# ================================
if st.button("🚀 ADICIONAR", use_container_width=True):

    texto = ""

    if arquivo:
        with st.spinner("Lendo imagem..."):
            img = preprocessar(Image.open(arquivo))

            res = reader.readtext(img, detail=1)

            texto += organizar_por_posicao(res)

    if manual:
        texto += " " + manual

    if texto:
        novas = extrair_velas(texto)

        # remove duplicadas recentes
        ultimas = st.session_state.velas[-20:]

        final = []
        for v in novas:
            if v not in ultimas:
                final.append(v)

        if final:
            st.session_state.velas.extend(final)
            salvar()
            st.success(f"{len(final)} velas adicionadas!")
            st.rerun()
        else:
            st.warning("Nada novo detectado")

st.divider()

# ================================
# HISTÓRICO
# ================================
st.subheader("📋 HISTORICO")

if st.session_state.velas:
    velas = [v for v in st.session_state.velas if v > 0]

    df = pd.DataFrame({"Vela": velas[::-1]})

    st.dataframe(
        df.style.format("{:.2f}x"),
        use_container_width=True
    )

st.divider()

# ================================
# ÚLTIMAS 20 (SEM BURACO)
# ================================
st.subheader("📉 ULTIMAS 20")

if st.session_state.velas:
    ultimas = [v for v in st.session_state.velas[-20:][::-1] if v > 0]

    if ultimas:
        texto = [
            f"<b style='color:{'#FF00FF' if v >= 8 else '#00FF00' if v >= 2 else '#FFFFFF'}'>{v:.2f}x</b>"
            for v in ultimas
        ]

        st.markdown(" , ".join(texto), unsafe_allow_html=True)
    else:
        st.write("Sem dados")

st.divider()

# ================================
# RESET
# ================================
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
