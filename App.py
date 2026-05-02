import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np
import cv2

DB_FILE = "banco_velas_projeto.csv"
LIMITE = 10000

# =========================
# BANCO DE DADOS
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.velas = [float(v) for v in df['velas'].dropna() if float(v) > 0]
        except: st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'velas': st.session_state.velas[-LIMITE:]}).to_csv(DB_FILE, index=False)

# =========================
# OCR (CORREÇÃO DO ERRO TYPEERROR)
# =========================
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

def extrair_velas_print(img):
    img_np = np.array(img.convert('L'))
    _, img_bin = cv2.threshold(img_np, 150, 255, cv2.THRESH_BINARY)
    res = reader.readtext(img_bin)
    
    itens = []
    for (bbox, texto, conf) in res:
        if re.search(r'\d', texto):
            # CORREÇÃO: Pega o ponto médio do Y (altura) e X (lateral) corretamente
            y_centro = np.mean([p[1] for p in bbox])
            x_centro = np.mean([p[0] for p in bbox])
            itens.append({'y': y_centro, 'x': x_centro, 't': texto})
    
    # Ordena: Cima para Baixo, Esquerda para Direita
    itens.sort(key=lambda i: (i['y'] // 30, i['x']))
    
    velas_finais = []
    for i in itens:
        nums = re.findall(r"(\d+(?:\.\d+)?)", i['t'].replace(',', '.'))
        for n in nums:
            v = float(n)
            if 1.0 <= v < 10000.0 and v != 400.0:
                velas_finais.append(v)
    return velas_finais

# =========================
# INTERFACE (TEXTOS CORRIGIDOS)
# =========================
st.title("ATE 10.000 VELAS")

aba1, aba2 = st.tabs(["INSERIR MANUAL", "INSERIR POR PRINT"])

with aba1:
    manual = st.text_area("Exemplo: 1.25x, 4.10x, 5x", height=100)
with aba2:
    arquivo = st.file_uploader("Envie o print aqui", type=['png','jpg','jpeg'])

if st.button("🚀 ADICIONAR AO HISTÓRICO"):
    novas = []
    if arquivo:
        novas = extrair_velas_print(Image.open(arquivo))
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

# BUSCA DE PADRÃO
st.write("**BUSCA DE PADRÃO**")
col_b1, col_b2 = st.columns([0.8, 0.2])
with col_b1:
    seq = st.text_input("Sequência desejada...", label_visibility="collapsed")
with col_b2:
    if st.button("🔎"):
        if seq:
            padrao = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)", seq.replace(',', '.'))]
            h = st.session_state.velas
            for i in range(len(h) - len(padrao)):
                if h[i:i+len(padrao)] == padrao:
                    st.success(f"Achado! Próximas: {h[i+len(padrao):i+len(padrao)+5]}")

st.divider()

# HISTÓRICO
st.write(f"**HISTÓRICO (Total: {len(st.session_state.velas)})**")
if st.session_state.velas:
    df_hist = pd.DataFrame({"vela": reversed(st.session_state.velas)})
    st.dataframe(
        df_hist.style.map(lambda v: "color:#FF00FF" if v >= 8 else "color:#00FF00" if v >= 2 else "color:white").format("{:.2f}x"),
        use_container_width=True, height=300
    )

st.divider()

# ÚLTIMAS 20 E RESET
col_f1, col_f2 = st.columns([0.6, 0.4])

with col_f1:
    st.write("**ÚLTIMAS 20 ADICIONADAS**")
    if st.session_state.velas:
        ultimas = st.session_state.velas[-20:]
        fmt = [f"<b style='color:{('#FF00FF' if v>=8 else '#00FF00' if v>=2 else '#FFF')}'>{v:.2f}x</b>" for v in ultimas]
        st.markdown(" , ".join(fmt), unsafe_allow_html=True)

with col_f2:
    st.write("**REDEFINIR**")
    if st.button("APAGAR ÚLTIMAS 20"):
        st.session_state.velas = st.session_state.velas[:-20]
        salvar(); st.rerun()
    if st.button("ZERAR TUDO"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []; st.rerun()
