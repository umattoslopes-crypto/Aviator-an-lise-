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
# OCR (OTIMIZADO)
# =========================
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

def preprocessar(img):
    img = img.convert('L')
    img_np = np.array(img)
    # Melhora o contraste para capturar o "x" e números claros
    _, img_bin = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img_bin

# =========================
# ORGANIZAÇÃO (DA ESQUERDA PARA DIREITA)
# =========================
def organizar_por_posicao(res):
    itens = []
    for (bbox, texto, conf) in res:
        y_topo = bbox[0][1]
        x_esq = bbox[0][0]
        itens.append({'y': y_topo, 'x': x_esq, 'texto': texto})

    # Agrupa por linha e ordena horizontalmente (ajuste o 25 se as linhas forem muito juntas)
    itens.sort(key=lambda i: (i['y'] // 25, i['x']))
    return [i['texto'] for i in itens]

# =========================
# EXTRAÇÃO (FOCADA NO "X")
# =========================
def extrair_velas(lista_textos):
    velas = []
    for texto in lista_textos:
        # Normaliza o texto
        t = texto.lower().replace(',', '.').strip()
        
        # Procura apenas números seguidos obrigatoriamente de 'x'
        # Ex: 1.16x, 5x, 1.24x
        encontrados = re.findall(r"(\d+(?:\.\d+)?)\s*x", t)
        
        for item in encontrados:
            try:
                val = float(item)
                if val >= 1.0:
                    velas.append(val)
            except:
                continue
    return velas

# =========================
# INTERFACE ORIGINAL
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
    textos_detectados = []

    if arquivo:
        img = preprocessar(Image.open(arquivo))
        res = reader.readtext(img)
        textos_detectados = organizar_por_posicao(res)

    if manual:
        textos_detectados += manual.split()

    if textos_detectados:
        novas = extrair_velas(textos_detectados)

        if len(novas) > MAX_POR_ENVIO:
            st.warning(f"Limitado a {MAX_POR_ENVIO} velas.")
            novas = novas[:MAX_POR_ENVIO]

        for v in novas:
            st.session_state.velas.append(v)

        if len(st.session_state.velas) > MAX_VELAS:
            st.session_state.velas = st.session_state.velas[-MAX_VELAS:]

        salvar()
        st.success(f"{len(novas)} velas adicionadas!")
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
# HISTÓRICO
# =========================
st.subheader("📋 HISTÓRICO")
if st.session_state.velas:
    df = pd.DataFrame({"Vela": st.session_state.velas})

    def cor(v):
        if v >= 8: return "color:#FF00FF; font-weight:bold"
        elif v >= 2: return "color:#00FF00"
        else: return "color:white"

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
    fmt = [f"<b style='color:{('#FF00FF' if v>=8 else '#00FF00' if v>=2 else '#FFF')}'>{v:.2f}x</b>" for v in ultimas]
    st.markdown(" , ".join(fmt), unsafe_allow_html=True)

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
