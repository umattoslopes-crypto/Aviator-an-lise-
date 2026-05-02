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
            # Carrega e remove qualquer linha vazia ou erro anterior
            st.session_state.velas = [float(v) for v in df['vela'].dropna() if float(v) > 0]
        except: st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'vela': st.session_state.velas[-LIMITE:]}).to_csv(DB_FILE, index=False)

# =========================
# OCR - AJUSTE PARA O PONTO DECIMAL
# =========================
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

def extrair_velas_print(img):
    # Converte para escala de cinza
    img_np = np.array(img.convert('L'))
    
    # Ajuste: Threshold menos agressivo para não apagar o ponto decimal (.)
    # Se o ponto sumir, 1.16 vira 116 ou 16.
    img_bin = cv2.threshold(img_np, 170, 255, cv2.THRESH_BINARY)[1]
    
    res = reader.readtext(img_bin)
    
    itens = []
    for (bbox, texto, conf) in res:
        # Troca vírgula por ponto ANTES de filtrar
        t_limpo = texto.lower().replace(',', '.').strip()
        
        # Só aceita se tiver número
        if re.search(r'\d', t_limpo):
            y_centro = np.mean([p[1] for p in bbox])
            x_centro = np.mean([p[0] for p in bbox])
            
            # Filtro para focar na grade de resultados
            if y_centro > 380 and x_centro < 850:
                itens.append({'y': y_centro, 'x': x_centro, 't': t_limpo})
    
    # Ordena: Cima para Baixo, Esquerda para Direita
    itens.sort(key=lambda i: (i['y'] // 35, i['x']))
    
    velas_finais = []
    for i in itens:
        # Regex melhorado para capturar o ponto decimal obrigatoriamente se ele existir
        # Isso evita que 1.16 seja lido como 16
        num_match = re.findall(r"(\d+(?:\.\d+)?)", i['t'])
        for n in num_match:
            try:
                v = float(n)
                if 1.0 <= v < 10000.0:
                    velas_finais.append(v)
            except: continue
            
    return velas_finais

# =========================
# INTERFACE (LAYOUT DO DESENHO)
# =========================
st.title("ATE 10.000 VELAS")

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
    if manual:
        # Também limpa o manual para garantir que vírgulas virem pontos
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
    seq = st.text_input("Sequência...", label_visibility="collapsed")
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
    # Mostra do mais novo para o mais velho (Linha 0 é a última que saiu)
    df_hist = pd.DataFrame({"vela": reversed(st.session_state.velas)})
    st.dataframe(
        df_hist.style.map(lambda v: "color:#FF00FF; font-weight:bold" if v >= 8 else "color:#00FF00" if v >= 2 else "color:white").format("{:.2f}x"),
        use_container_width=True, height=350
    )

st.divider()

# ÚLTIMAS 20 E REDEFINIR
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
        salvar(); st.rerun()
    if st.button("ZERAR TUDO", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []; st.rerun()
