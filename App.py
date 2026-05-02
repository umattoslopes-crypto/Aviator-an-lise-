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
            st.session_state.velas = [float(v) for v in df['velas'].dropna() if float(v) > 0]
        except:
            st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'velas': st.session_state.velas[-MAX_VELAS:]}).to_csv(DB_FILE, index=False)

# =========================
# OCR E PROCESSAMENTO
# =========================
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

def preprocessar(img):
    img = img.convert('L')
    img_np = np.array(img)
    # Aumenta o contraste para capturar velas cinzas/claras
    img_bin = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return img_bin

def organizar_por_posicao(res):
    itens = []
    for (bbox, texto, conf) in res:
        # Pega o centro Y e o X da esquerda
        y_centro = (bbox[0][1] + bbox[2][1]) / 2
        x_esq = bbox[0][0]
        itens.append({'y': y_centro, 'x': x_esq, 'texto': texto})
    
    # Ordena por Y (linhas) e depois por X (da direita para esquerda, comum em jogos)
    itens.sort(key=lambda i: (i['y'] // 20, -i['x'])) 
    return [i['texto'] for i in itens]

def extrair_velas(lista_textos):
    velas = []
    for texto in lista_textos:
        texto = texto.lower().replace(',', '.')
        # Captura números decimais (ex: 1.00, 2, 1.5x)
        encontrados = re.findall(r"(\d+(?:\.\d+)?)\s*x?", texto)
        for item in encontrados:
            try:
                val = float(item)
                if val >= 1.0:
                    velas.append(val)
            except:
                continue
    return velas

# =========================
# INTERFACE
# =========================
st.title("📊 ANALISADOR DE VELAS")

aba1, aba2 = st.tabs(["📸 PRINT", "📥 MANUAL"])

with aba1:
    arquivo = st.file_uploader("Envie o print", type=['png','jpg','jpeg'])

with aba2:
    manual = st.text_area("Cole as velas (Ex: 1.25 4.10)")

if st.button("🚀 ADICIONAR", use_container_width=True):
    textos = []
    if arquivo:
        img = preprocessar(Image.open(arquivo))
        res = reader.readtext(img)
        textos = organizar_por_posicao(res)
    
    if manual:
        textos += manual.split()

    if textos:
        novas = extrair_velas(textos)
        if len(novas) > MAX_POR_ENVIO:
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
# BUSCA DE PADRÃO
# =========================
st.subheader("🔍 BUSCA DE PADRÃO")
seq = st.text_input("Ex: 1.25 2.00")
if st.button("🔎 BUSCAR"):
    if seq:
        try:
            padrao = [float(x.replace(',', '.')) for x in seq.split()]
            hist = st.session_state.velas
            achou = False
            for i in range(len(hist) - len(padrao)):
                if hist[i:i+len(padrao)] == padrao:
                    achou = True
                    futuro = hist[i+len(padrao):i+len(padrao)+5]
                    st.write(f"✅ Padrão encontrado! Próximas: **{futuro}**")
            if not achou: st.error("Não encontrado")
        except: st.error("Erro no formato")

st.divider()

# =========================
# HISTÓRICO VISUAL
# =========================
st.subheader("📉 ÚLTIMAS 20")
if st.session_state.velas:
    ultimas = st.session_state.velas[-20:]
    texto_formatado = []
    for v in ultimas:
        cor = "#FF00FF" if v >= 10 else "#00FF00" if v >= 2 else "#FFFFFF"
        texto_formatado.append(f"<b style='color:{cor}'>{v:.2f}x</b>")
    st.markdown(" , ".join(texto_formatado), unsafe_allow_html=True)

st.divider()

# =========================
# ÁREA DE RESET (RESTAURADA)
# =========================
st.subheader("⚙️ CONFIGURAÇÕES")
col_res1, col_res2 = st.columns(2)

with col_res1:
    if st.button("🗑️ Apagar últimas 20", use_container_width=True):
        st.session_state.velas = st.session_state.velas[:-20]
        salvar()
        st.rerun()

with col_res2:
    if st.button("🚨 Zerar Tudo", use_container_width=True):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()
