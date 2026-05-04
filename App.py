import streamlit as st
import pandas as pd
import os, re, cv2
from PIL import Image
import numpy as np
import easyocr

DB_FILE = "banco_velas_projeto.csv"
LIMITE = 10000

# Inicialização do Banco
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.velas = [float(v) for v in df['vela'].dropna() if float(v) > 0]
        except: st.session_state.velas = []
    else: st.session_state.velas = []

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

def extrair_velas_print(img):
    reader = load_reader()
    img_np = np.array(img.convert('RGB'))
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    # Suaviza e destaca números
    gray = cv2.detailEnhance(gray, sigma_s=10, sigma_r=0.15)
    _, bin_img = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)
    
    res = reader.readtext(bin_img, detail=1, low_text=0.3)
    itens = []
    
    for (bbox, texto, conf) in res:
        t = texto.lower().replace(',', '.').strip()
        if re.search(r'\d', t):
            # Corrige erro de TypeError usando np.mean
            y_centro = np.mean([p[1] for p in bbox])
            x_centro = np.mean([p[0] for p in bbox])
            # Foca na área central do print (onde ficam as velas)
            if y_centro > 400 and x_centro < 850:
                itens.append({'y': y_centro, 'x': x_centro, 't': t})
    
    # Ordena: Cima p/ Baixo e Esquerda p/ Direita
    itens.sort(key=lambda i: (i['y'] // 30, i['x']))
    
    velas_finais = []
    for i in itens:
        num = re.findall(r"(\d+(?:\.\d+)?)", i['t'])
        if num:
            v = float(num[0])
            if 1.0 <= v < 10000.0 and v != 500.0:
                velas_finais.append(v)
    return velas_finais

# Interface (Ajustada conforme seu desenho)
st.title("ATE 10.000 VELAS")
aba1, aba2 = st.tabs(["MANUAL", "PRINT"])
with aba1: manual = st.text_area("Ex: 1.16x 5x", height=80)
with aba2: arquivo = st.file_uploader("Envie o print", type=['png','jpg','jpeg'])

if st.button("🚀 ADICIONAR"):
    novas = []
    if arquivo: novas = extrair_velas_print(Image.open(arquivo))
    if manual: novas += [float(n) for n in re.findall(r"(\d+(?:\.\d+)?)", manual.replace(',','.'))]
    if novas:
        st.session_state.velas = (st.session_state.velas + novas)[-LIMITE:]
        pd.DataFrame({'vela': st.session_state.velas}).to_csv(DB_FILE, index=False)
        st.success(f"{len(novas)} adicionadas!")
        st.rerun()

# Histórico e Botões (conforme desenho)
if st.session_state.velas:
    st.dataframe(pd.DataFrame({"vela": reversed(st.session_state.velas)}).style.map(
        lambda v: "color:#FF00FF; font-weight:bold" if v>=8 else "color:#00FF00" if v>=2 else "color:white"
    ).format("{:.2f}x"), use_container_width=True, height=300)
    
col1, col2 = st.columns([0.6, 0.4])
with col1:
    st.write("**ÚLTIMAS 20**")
    st.markdown(" , ".join([f"<b style='color:{('#FF00FF' if v>=8 else '#00FF00' if v>=2 else '#FFF')}'>{v:.2f}x</b>" for v in st.session_state.velas[-20:]]), unsafe_allow_html=True)
with col2:
    if st.button("ZERAR TUDO"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []; st.rerun()
