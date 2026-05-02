import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np
import cv2

# Configuração de Limites
DB_FILE = "banco_velas_projeto.csv"
LIMITE_HISTORICO = 10000 

# =========================
# BANCO DE DADOS (10.000 VELAS)
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # Carrega as últimas 10k do arquivo para a memória
            st.session_state.velas = [float(v) for v in df['velas'].dropna().tolist()][-LIMITE_HISTORICO:]
        except: st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    # Salva sempre garantindo o limite de 10.000
    df_save = pd.DataFrame({'velas': st.session_state.velas[-LIMITE_HISTORICO:]})
    df_save.to_csv(DB_FILE, index=False)

# =========================
# OCR E EXTRAÇÃO LIMPA
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
        if re.search(r'\d', texto): # Limpa vírgulas vazias/lixo
            y = sum([p for p in bbox]) / 4
            x = sum([p for p in bbox]) / 4
            itens.append({'y': y, 'x': x, 't': texto})
    
    # Ordem de leitura: Esquerda -> Direita, Linha -> Linha
    itens.sort(key=lambda i: (i['y'] // 30, i['x']))
    
    velas_extraidas = []
    for i in itens:
        nums = re.findall(r"(\d+(?:\.\d+)?)", i['t'].replace(',', '.'))
        for n in nums:
            v = float(n)
            if 1.0 <= v < 10000.0 and v != 400.0:
                velas_extraidas.append(v)
    return velas_extraidas

# =========================
# LAYOUT DO DESENHO
# =========================
st.title("ATE 10.000 VELAS")

# 1. ABAS DE INSERÇÃO
aba1, aba2 = st.tabs(["INGERIR MANUAL", "INGERIR ATRAVES PRINT"])
with aba1:
    manual = st.text_area("Ex: 1.25x 4.10x 5x", height=80)
with aba2:
    arquivo = st.file_uploader("Envie o print", type=['png','jpg','jpeg'])

if st.button("🚀 ADICIONAR VELAS"):
    novas = []
    if arquivo:
        novas = extrair_velas_print(Image.open(arquivo))
    if manual:
        nums = re.findall(r"(\d+(?:\.\d+)?)", manual.replace(',', '.'))
        novas += [float(n) for n in nums]
    
    if novas:
        st.session_state.velas += novas
        # Aplica o corte de 10k antes de salvar
        if len(st.session_state.velas) > LIMITE_HISTORICO:
            st.session_state.velas = st.session_state.velas[-LIMITE_HISTORICO:]
        salvar()
        st.success(f"Adicionadas {len(novas)} velas!")
        st.rerun()

st.divider()

# 2. BUSCA DE PADRÃO (Layout Desenho: Botão ao lado)
st.write("**BUSCA DE PADRAO**")
col_b1, col_b2 = st.columns([0.85, 0.15])
with col_b1:
    seq_input = st.text_input("Sequencia...", label_visibility="collapsed", placeholder="1.20 2.50")
with col_b2:
    btn_lupa = st.button("🔎")

if btn_lupa and seq_input:
    try:
        padrao = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)", seq_input.replace(',', '.'))]
        h = st.session_state.velas
        achou = False
        for i in range(len(h) - len(padrao)):
            if h[i:i+len(padrao)] == padrao:
                st.success(f"Achado! Próximas 5: {h[i+len(padrao):i+len(padrao)+5]}")
                achou = True
        if not achou: st.warning("Não encontrado nas 10k velas.")
    except: st.error("Formato inválido")

st.divider()

# 3. HISTÓRICO DE VELAS (Scrollable)
st.write(f"**HISTORICO DE VELAS (Total: {len(st.session_state.velas)})**")
if st.session_state.velas:
    # Mostra o histórico invertido (mais recente no topo)
    df_hist = pd.DataFrame({"vela": reversed(st.session_state.velas)})
    st.dataframe(
        df_hist.style.map(lambda v: "color:#FF00FF; font-weight:bold" if v >= 8 else "color:#00FF00" if v >= 2 else "color:white").format("{:.2f}x"),
        use_container_width=True,
        height=350 # Altura fixa para permitir o scroll de 10.000 itens
    )

st.divider()

# 4. ÚLTIMA 20 E RESET (Lado a Lado como no desenho)
col_f1, col_f2 = st.columns([0.6, 0.4])

with col_f1:
    st.write("**ULTIMA 20 VELA ADICIONADA**")
    if st.session_state.velas:
        ultimas = st.session_state.velas[-20:]
        html = [f"<b style='color:{('#FF00FF' if v>=8 else '#00FF00' if v>=2 else '#FFF')}'>{v:.2f}x</b>" for v in ultimas]
        st.markdown(" , ".join(html), unsafe_allow_html=True)

with col_f2:
    st.write("**RESETAR**")
    if st.button("ULTIMA 20 VELAS", use_container_width=True):
        st.session_state.velas = st.session_state.velas[:-20]
        salvar(); st.rerun()
    if st.button("TUDO", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []; st.rerun()
           
