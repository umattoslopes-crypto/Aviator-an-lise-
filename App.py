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
# BANCO DE DADOS
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # Garante que carregue apenas números válidos e limpos
            st.session_state.velas = [float(v) for v in df['velas'].dropna() if float(v) > 0]
        except: st.session_state.velas = []
    else: st.session_state.velas = []

def salvar():
    pd.DataFrame({'velas': st.session_state.velas[-MAX_VELAS:]}).to_csv(DB_FILE, index=False)

# =========================
# OCR AJUSTADO
# =========================
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

def preprocessar(img):
    # Aumentar o contraste ajuda a remover o brilho das cores verde/vermelho 
    # e focar no número branco
    img_np = np.array(img.convert('L'))
    # Deixa o fundo preto e o texto bem branco
    _, img_bin = cv2.threshold(img_np, 160, 255, cv2.THRESH_BINARY)
    return img_bin

def organizar_por_posicao(res):
    itens = []
    for (bbox, texto, conf) in res:
        # Pega a posição vertical (y) e horizontal (x)
        y_topo = bbox[0][1]
        x_esq = bbox[0][0]
        itens.append({'y': y_topo, 'x': x_esq, 'texto': texto})
    
    # Ordena por linha e depois por coluna (esquerda para direita)
    itens.sort(key=lambda i: (i['y'] // 30, i['x']))
    return [i['texto'] for i in itens]

def extrair_velas(lista_textos):
    velas_limpas = []
    for texto in lista_textos:
        # Limpeza agressiva: mantém apenas números, pontos e o 'x'
        t = texto.lower().replace(',', '.')
        # Busca o padrão de número (ex: 1.10x ou 5x)
        match = re.search(r"(\d+(?:\.\d+)?)\s*x", t)
        
        if match:
            try:
                val = float(match.group(1))
                # Filtro para ignorar sujeira do OCR (como o 400 ou 4s)
                if 1.0 <= val < 10000.0 and val != 400.0:
                    velas_limpas.append(val)
            except: continue
    return velas_limpas

# =========================
# INTERFACE (LAYOUT ORIGINAL)
# =========================
st.title("📊 ANALISADOR DE VELAS")

aba1, aba2 = st.tabs(["📸 PRINT", "📥 MANUAL"])

with aba1:
    arquivo = st.file_uploader("Envie o print", type=['png','jpg','jpeg'])

with aba2:
    manual = st.text_area("Cole as velas (Ex: 1.10x 2.50x)")

if st.button("🚀 ADICIONAR", use_container_width=True):
    textos_brutos = []
    if arquivo:
        img_p = preprocessar(Image.open(arquivo))
        res = reader.readtext(img_p)
        textos_brutos = organizar_por_posicao(res)
    
    if manual:
        textos_brutos += manual.split()

    if textos_brutos:
        novas = extrair_velas(textos_brutos)
        if novas:
            for v in novas:
                st.session_state.velas.append(v)
            salvar()
            st.success(f"{len(novas)} velas adicionadas sem erros!")
            st.rerun()
        else:
            st.error("Não foi possível ler as velas. Tente outro print.")

st.divider()

# =========================
# HISTÓRICO E ÚLTIMAS 20
# =========================
if st.session_state.velas:
    st.subheader("📋 HISTÓRICO")
    df = pd.DataFrame({"vela": st.session_state.velas})
    
    # Estilização das cores na tabela
    def estilo_vela(v):
        if v >= 8: return "color: #FF00FF; font-weight: bold"
        elif v >= 2: return "color: #00FF00"
        else: return "color: white"

    st.dataframe(
        df.style.map(estilo_vela).format("{:.2f}x"),
        use_container_width=True, height=300
    )

    st.subheader("📉 ÚLTIMAS 20")
    # Pega exatamente as últimas 20 e remove qualquer valor nulo/vazio
    ultimas = [v for v in st.session_state.velas[-20:] if v > 0]
    
    html_velas = []
    for v in ultimas:
        cor = "#FF00FF" if v >= 8 else "#00FF00" if v >= 2 else "#FFFFFF"
        html_velas.append(f"<b style='color:{cor}'>{v:.2f}x</b>")
    
    # O join sem espaços extras resolve o problema das vírgulas perdidas
    st.markdown(" , ".join(html_velas), unsafe_allow_html=True)

st.divider()

# =========================
# RESET
# =========================
if st.checkbox("Reset"):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Apagar últimas 20"):
            st.session_state.velas = st.session_state.velas[:-20]
            salvar(); st.rerun()
    with col2:
        if st.button("Zerar tudo"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.velas = []; st.rerun()
