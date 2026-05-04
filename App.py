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
# BANCO DE DADOS
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.velas = [float(v) for v in df['vela'].dropna() if float(v) > 0]
        except: st.session_state.velas = []
    else: st.session_state.velas = []

def salvar():
    pd.DataFrame({'vela': st.session_state.velas[-LIMITE:]}).to_csv(DB_FILE, index=False)

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

# =========================
# OCR LEVE (PARA NÃO DAR ERRO)
# =========================
def extrair_velas_print(img):
    reader = load_reader()
    # Converte para cinza sem filtros pesados que travam o app
    img_np = np.array(img.convert('L'))
    
    # Corte simples da área (evita processar a imagem toda)
    h, w = img_np.shape
    corte = img_np[int(h*0.52):int(h*0.88), int(w*0.08):int(w*0.78)]
    
    # Threshold simples e rápido
    _, bin_img = cv2.threshold(corte, 160, 255, cv2.THRESH_BINARY)
    
    res = reader.readtext(bin_img)
    itens = []
    for (bbox, texto, conf) in res:
        # Troca vírgula por ponto e limpa o texto
        t = texto.lower().replace(',', '.').replace(' ', '').strip()
        
        # Busca apenas os números
        nums = re.findall(r"(\d+(?:\.\d+)?)", t)
        for n in nums:
            try:
                v = float(n)
                # PROTEÇÃO PARA O 1.16x: Se leu 116 (inteiro alto), corrige a posição do ponto
                if v > 100 and '.' not in n:
                    v = float(n[0] + "." + n[1:])
                
                if 1.0 <= v <= 5000:
                    y = np.mean([p[1] for p in bbox])
                    x = np.mean([p[0] for p in bbox])
                    itens.append({'x': x, 'y': y, 'v': v})
            except: continue

    # Ordena da esquerda para a direita, linha por linha
    itens.sort(key=lambda i: (i['y'] // 30, i['x']))
    return [i['v'] for i in itens]

# =========================
# INTERFACE (LAYOUT DO SEU DESENHO)
# =========================
st.title("ANÁLISE DE VELAS")

aba1, aba2 = st.tabs(["INSERIR MANUAL", "INSERIR POR PRINT"])

with aba1:
    manual = st.text_area("Ex: 1.16x 10.71x 5x", height=100)
with aba2:
    arquivo = st.file_uploader("Envie o print", type=['png','jpg','jpeg'])

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    novas = []
    if arquivo:
        with st.spinner("Lendo..."):
            novas = extrair_velas_print(Image.open(arquivo))
    if manual:
        # Captura números do manual também
        novas += [float(n) for n in re.findall(r"(\d+(?:\.\d+)?)", manual.replace(',', '.'))]
    
    if novas:
        st.session_state.velas += novas
        salvar(); st.success(f"{len(novas)} velas detectadas!"); st.rerun()

st.divider()

# BUSCA DE PADRÃO
st.write("**BUSCA DE PADRÃO**")
col_b1, col_b2 = st.columns([0.8, 0.2])
with col_b1: seq = st.text_input("Sequência...", label_visibility="collapsed")
with col_b2:
    if st.button("🔎"):
        if seq:
            p = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)", seq.replace(',', '.'))]
            h = st.session_state.velas
            for i in range(len(h) - len(p) + 1):
                if h[i:i+len(p)] == p: st.success(f"Achado! Próximas: {h[i+len(p):i+len(p)+5]}")

# HISTÓRICO
st.write(f"**HISTÓRICO (Total: {len(st.session_state.velas)})**")
if st.session_state.velas:
    df_h = pd.DataFrame({"vela": reversed(st.session_state.velas)})
    st.dataframe(df_h.style.map(lambda v: "color:#FF00FF; font-weight:bold" if v>=8 else "color:#00FF00" if v>=2 else "color:white").format("{:.2f}x"), use_container_width=True, height=300)

# ÚLTIMAS 20 E RESET
st.divider()
col_f1, col_f2 = st.columns([0.6, 0.4])
with col_f1:
    st.write("**ÚLTIMAS 20**")
    if st.session_state.velas:
        ultimas = st.session_state.velas[-20:]
        txt = [f"<b style='color:{('#FF00FF' if v>=8 else '#00FF00' if v>=2 else '#FFF')}'>{v:.2f}x</b>" for v in ultimas]
        st.markdown(" , ".join(txt), unsafe_allow_html=True)
with col_f2:
    st.write("**REDEFINIR**")
    if st.button("APAGAR ÚLTIMAS 20"):
        st.session_state.velas = st.session_state.velas[:-20]
        salvar(); st.rerun()
    if st.button("ZERAR TUDO"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []; st.rerun()
