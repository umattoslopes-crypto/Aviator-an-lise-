import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import numpy as np
import cv2

# tenta importar OCR sem quebrar o app
try:
    import easyocr
    OCR_OK = True
except:
    OCR_OK = False

DB_FILE = "banco_velas_projeto.csv"
LIMITE = 10000

st.title("ATE 10.000 VELAS")

# =========================
# BANCO DE DADOS
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.velas = [float(v) for v in df['vela'].dropna() if float(v) > 0]
        except:
            st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'vela': st.session_state.velas[-LIMITE:]}).to_csv(DB_FILE, index=False)

# =========================
# OCR (seguro)
# =========================
@st.cache_resource
def load_reader():
    if not OCR_OK:
        return None
    try:
        return easyocr.Reader(['en'], gpu=False, verbose=False)
    except:
        return None

reader = load_reader()

# =========================
# EXTRAÇÃO (VERSÃO ESTÁVEL)
# =========================
def extrair_velas_print(img):
    try:
        img_np = np.array(img.convert('RGB'))
        h, w = img_np.shape[:2]

        # corte seguro (ajustável)
        top = int(h * 0.52)
        bottom = int(h * 0.88)
        left = int(w * 0.08)
        right = int(w * 0.78)

        img_np = img_np[top:bottom, left:right]

        # mostra área capturada
        st.image(img_np, caption="Área capturada")

        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        gray = cv2.convertScaleAbs(gray, alpha=1.6, beta=10)

        _, bin_img = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY_INV)

        if reader is None:
            st.warning("OCR não carregou")
            return []

        resultados = reader.readtext(
            bin_img,
            detail=1,
            paragraph=False,
            allowlist='0123456789.x'
        )

        itens = []

        for (bbox, texto, conf) in resultados:
            t = texto.lower().replace(',', '.').strip()

            if 'x' not in t:
                continue

            match = re.findall(r"\d+\.\d+x", t)

            if match:
                y = np.mean([p[1] for p in bbox])
                x = np.mean([p[0] for p in bbox])

                try:
                    valor = float(match[0].replace('x',''))

                    if 1.0 <= valor <= 200:
                        itens.append({'x': x, 'y': y, 'v': valor})
                except:
                    pass

        # agrupar linhas
        linhas = []
        tol = 25

        for item in sorted(itens, key=lambda i: i['y']):
            colocado = False
            for linha in linhas:
                if abs(linha[0]['y'] - item['y']) < tol:
                    linha.append(item)
                    colocado = True
                    break
            if not colocado:
                linhas.append([item])

        # ordenar
        linhas.sort(key=lambda l: l[0]['y'])

        velas = []
        for linha in linhas:
            linha.sort(key=lambda i: -i['x'])
            for item in linha:
                velas.append(item['v'])

        return velas

    except Exception as e:
        st.error(f"Erro na leitura: {e}")
        return []

# =========================
# INTERFACE
# =========================
aba1, aba2 = st.tabs(["INSERIR MANUAL", "INSERIR POR PRINT"])

with aba1:
    manual = st.text_area("Exemplo: 1.16x 10.71x", height=100)

with aba2:
    arquivo = st.file_uploader("Envie o print", type=['png','jpg','jpeg'])

if st.button("🚀 ADICIONAR", use_container_width=True):
    novas = []

    if arquivo:
        with st.spinner("Lendo print..."):
            novas = extrair_velas_print(Image.open(arquivo))

            if not novas:
                st.warning("Nenhuma vela detectada")

    if manual:
        nums = re.findall(r"(\d+(?:\.\d+)?)", manual.replace(',', '.'))
        novas += [float(n) for n in nums]

    if novas:
        st.session_state.velas += novas
        if len(st.session_state.velas) > LIMITE:
            st.session_state.velas = st.session_state.velas[-LIMITE:]
        salvar()
        st.success(f"{len(novas)} velas adicionadas!")
        st.rerun()

st.divider()

# =========================
# HISTÓRICO
# =========================
st.write(f"Histórico: {len(st.session_state.velas)}")

if st.session_state.velas:
    df = pd.DataFrame({"vela": st.session_state.velas[::-1]})
    st.dataframe(df)

st.divider()

# =========================
# RESET
# =========================
if st.button("ZERAR"):
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    st.session_state.velas = []
    st.rerun()
