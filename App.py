import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import numpy as np
import cv2
import easyocr

DB_FILE = "banco_velas_projeto.csv"
LIMITE = 10000

# =========================
# BANCO DE DADOS (ABERTO)
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # Carrega tudo que for número maior que 0
            st.session_state.velas = [float(v) for v in df['vela'].dropna() if float(v) > 0]
        except: st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'vela': st.session_state.velas[-LIMITE:]}).to_csv(DB_FILE, index=False)

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

# =========================
# OCR - FORÇA BRUTA PARA VELAS BAIXAS
# =========================
def extrair_velas_print(img):
    reader = load_reader()
    img_np = np.array(img.convert('L'))
    h, w = img_np.shape
    # Corte da área das velas
    corte = img_np[int(h*0.50):int(h*0.90), int(w*0.05):int(w*0.85)]
    # Binarização agressiva para destacar o número 1
    _, bin_img = cv2.threshold(corte, 150, 255, cv2.THRESH_BINARY)
    
    res = reader.readtext(bin_img)
    itens = []
    for (bbox, texto, conf) in res:
        # Limpa tudo, deixa só o que parece número
        t = texto.lower().replace(',', '.').strip()
        nums = re.findall(r"(\d+(?:\.\d+)?)", t)
        
        for n in nums:
            try:
                v = float(n)
                # CORREÇÃO: Se leu '116' ou '105' (sem ponto), força o 1.xx
                if 100 <= v <= 199 and '.' not in n:
                    v = v / 100.0
                
                # ACEITA TUDO A PARTIR DE 1.00
                if v >= 1.0:
                    y = np.mean([p for p in bbox])
                    x = np.mean([p for p in bbox])
                    itens.append({'y': y, 'x': x, 'v': v})
            except: continue

    # Ordena: Baixo -> Cima, Direita -> Esquerda
    itens.sort(key=lambda i: (i['y'] // 30, i['x']), reverse=True)
    return [i['v'] for i in itens]

# =========================
# INTERFACE
# =========================
st.title("ATE 10.000 VELAS")

aba1, aba2 = st.tabs(["INSERIR MANUAL", "INSERIR POR PRINT"])

with aba1:
    manual = st.text_area("Cole aqui (Ex: 1x, 1.16, 1.09, 9.64)", height=150)

with aba2:
    arquivo = st.file_uploader("Envie o print", type=['png','jpg','jpeg'])

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    novas = []
    if arquivo:
        with st.spinner("Lendo tudo..."):
            novas = extrair_velas_print(Image.open(arquivo))
    
    if manual:
        # Pega qualquer número colado, sem restrição
        m_nums = re.findall(r"(\d+(?:\.\d+)?)", manual.replace(',', '.'))
        for n in m_nums:
            v = float(n)
            # Se colou '116', vira '1.16'
            if 100 <= v <= 199 and '.' not in n: v = v / 100.0
            if v >= 1.0: novas.append(v)

    if novas:
        st.session_state.velas += novas
        salvar()
        st.success(f"{len(novas)} velas adicionadas!")
        st.rerun()

st.divider()

# BUSCA, HISTÓRICO E RESET
if st.session_state.velas:
    st.write(f"**HISTÓRICO (Total: {len(st.session_state.velas)})**")
    df_h = pd.DataFrame({"vela": reversed(st.session_state.velas)})
    st.dataframe(
        df_h.style.map(lambda v: "color:#FF00FF" if v >= 8 else "color:#00FF00" if v >= 2 else "color:white").format("{:.2f}x,"),
        use_container_width=True, height=350
    )

    col_f1, col_f2 = st.columns([0.6, 0.4])
    with col_f1:
        st.write("**ÚLTIMAS 20**")
        ultimas = st.session_state.velas[-20:]
        fmt = [f"<b style='color:{('#FF00FF' if v>=8 else '#00FF00' if v>=2 else '#FFF')}'>{v:.2f}x,</b>" for v in ultimas]
        st.markdown(" ".join(fmt), unsafe_allow_html=True)
    with col_f2:
        if st.button("APAGAR ÚLTIMAS 20"):
            st.session_state.velas = st.session_state.velas[:-20]; salvar(); st.rerun()
        if st.button("ZERAR TUDO"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.velas = []; st.rerun()
