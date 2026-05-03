import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import numpy as np
import cv2

# OCR seguro
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
# OCR
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
# EXTRAÇÃO DE VELAS
# =========================
def extrair_velas_print(img):
    try:
        img_np = np.array(img.convert('RGB'))
        h, w = img_np.shape[:2]

        # corte da área dos resultados
        img_np = img_np[int(h*0.52):int(h*0.88), int(w*0.08):int(w*0.78)]

        st.image(img_np, caption="Área capturada")

        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        gray = cv2.convertScaleAbs(gray, alpha=1.6, beta=10)
        _, bin_img = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY_INV)

        if reader is None:
            st.warning("OCR não disponível")
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

        # agrupar por linhas
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

        # ordem correta: topo → baixo, direita → esquerda
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
    arquivo = st.file_uploader("Envie o print dos resultados", type=['png','jpg','jpeg'])

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
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
# BUSCA DE PADRÃO
# =========================
st.write("**BUSCA DE PADRÃO**")

col_b1, col_b2 = st.columns([0.8, 0.2])

with col_b1:
    seq = st.text_input("Sequência...", label_visibility="collapsed")

with col_b2:
    if st.button("🔎"):
        if seq:
            padrao = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)", seq.replace(',', '.'))]
            h = st.session_state.velas

            def comparar(a, b, tol=0.01):
                return all(abs(x - y) <= tol for x, y in zip(a, b))

            achou = False

            for i in range(len(h) - len(padrao) + 1):
                if comparar(h[i:i+len(padrao)], padrao):
                    st.success(f"Achado! Próximas: {h[i+len(padrao):i+len(padrao)+5]}")
                    achou = True

            if not achou:
                st.warning("Nenhum padrão encontrado")

st.divider()

# =========================
# HISTÓRICO
# =========================
st.write(f"**HISTÓRICO (Total: {len(st.session_state.velas)})**")

if st.session_state.velas:
    df_hist = pd.DataFrame({"vela": st.session_state.velas[::-1]})

    st.dataframe(
        df_hist.style.map(
            lambda v: "color:#FF00FF; font-weight:bold" if v >= 8 else
                      "color:#00FF00" if v >= 2 else
                      "color:white"
        ).format("{:.2f}x"),
        use_container_width=True,
        height=350
    )

st.divider()

# =========================
# ÚLTIMAS 20
# =========================
col_f1, col_f2 = st.columns([0.6, 0.4])

with col_f1:
    st.write("**ÚLTIMAS 20 ADICIONADAS**")
    if st.session_state.velas:
        ultimas = st.session_state.velas[-20:]
        fmt = [f"<b style='color:{('#FF00FF' if v>=8 else '#00FF00' if v>=2 else '#FFF')}'>{v:.2f}x</b>" for v in ultimas]
        st.markdown(" , ".join(fmt), unsafe_allow_html=True)

with col_f2:
    st.write("**REDEFINIR**")

    if st.button("APAGAR ÚLTIMAS 20", use_container_width=True):
        st.session_state.velas = st.session_state.velas[:-20]
        salvar()
        st.rerun()

    if st.button("ZERAR TUDO", use_container_width=True):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()
