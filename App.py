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
MAX_POR_ENVIO = 500

# =========================
# BANCO
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.velas = [
                float(v) for v in df['velas'].dropna() if float(v) > 0
            ]
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

def preprocessar(img):
    img = img.convert('L')
    img = np.array(img)
    img = np.where(img > 140, 255, 0).astype(np.uint8)
    return img

# =========================
# ORGANIZAÇÃO POR LINHA (PRECISO)
# =========================
def organizar_por_posicao(res):
    linhas = []

    for (bbox, texto, conf) in res:
        texto = texto.strip()
        if 'x' not in texto.lower():
            continue

        x = bbox[0][0]
        y = bbox[0][1]

        colocado = False
        for linha in linhas:
            if abs(linha['y'] - y) < 22:  # tolerância vertical ajustada
                linha['itens'].append((x, texto))
                colocado = True
                break

        if not colocado:
            linhas.append({'y': y, 'itens': [(x, texto)]})

    # baixo → cima
    linhas.sort(key=lambda l: -l['y'])

    resultado = []
    for linha in linhas:
        # direita → esquerda
        linha['itens'].sort(key=lambda i: -i[0])
        for _, texto in linha['itens']:
            resultado.append(texto)

    return resultado

# =========================
# EXTRAÇÃO (SEM PERDER VALORES)
# =========================
def extrair_velas(lista_textos):
    velas = []

    for texto in lista_textos:
        texto = texto.lower().replace(',', '.').strip()

        # pega número mesmo com sujeira
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
st.title("📊 ANALISADOR DE VELAS")

aba1, aba2 = st.tabs(["📥 MANUAL", "📸 PRINT"])

with aba1:
    manual = st.text_area("Cole até 500 velas: Ex: 1.25x 4.10x")

with aba2:
    arquivo = st.file_uploader("Envie o print", type=['png','jpg','jpeg'])

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

        # 🔥 LIMITE DE 500
        if len(novas) > MAX_POR_ENVIO:
            st.warning(f"{len(novas)} velas detectadas. Limitado a 500 por envio.")
            novas = novas[:MAX_POR_ENVIO]

        adicionadas = 0

        for v in novas:
            if isinstance(v, (int, float)) and v > 0:
                st.session_state.velas.append(v)
                adicionadas += 1

        # limite histórico
        if len(st.session_state.velas) > MAX_VELAS:
            st.session_state.velas = st.session_state.velas[-MAX_VELAS:]

        salvar()
        st.success(f"{adicionadas} velas adicionadas!")
        st.rerun()

st.divider()

# =========================
# BUSCA
# =========================
st.subheader("🔍 BUSCA DE PADRÃO")

seq = st.text_input("Ex: 1.25 2.00 3.50")

if st.button("🔎 BUSCAR"):
    if seq:
        try:
            padrao = [float(x.replace(',', '.')) for x in seq.split()]
            hist = st.session_state.velas

            achou = False

            for i in range(len(hist) - len(padrao)):
                if hist[i:i+len(padrao)] == padrao:
                    achou = True
                    st.success("Padrão encontrado!")

                    futuro = hist[i+len(padrao):i+len(padrao)+10]
                    if futuro:
                        st.write([f"{v:.2f}x" for v in futuro])

            if not achou:
                st.error("Não encontrado")

        except:
            st.error("Erro no padrão")

st.divider()

# =========================
# HISTÓRICO COLORIDO
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
