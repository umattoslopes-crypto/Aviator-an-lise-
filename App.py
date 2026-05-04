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
# A FÓRMULA DE LEITURA (PRECISÃO TOTAL)
# =========================
def extrair_velas_print(img):
    reader = load_reader()
    img_np = np.array(img.convert('RGB'))
    h, w = img_np.shape[:2]
    
    # 1. Corte cirúrgico da grade (ajustado para o seu print)
    area = img_np[int(h*0.52):int(h*0.88), int(w*0.08):int(w*0.78)]
    
    # 2. A FÓRMULA: Converte para Cinza e aplica Threshold alto (180)
    # Isso apaga os botões verdes/vermelhos e deixa só o número branco visível
    gray = cv2.cvtColor(area, cv2.COLOR_RGB2GRAY)
    _, bin_img = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    
    # 3. Leitura do texto na imagem limpa
    res = reader.readtext(bin_img)
    
    itens = []
    for (bbox, texto, conf) in res:
        # Limpeza do texto (Troca vírgula por ponto, remove o 'x')
        t = texto.lower().replace(',', '.').replace('x', '').strip()
        
        # Só aceita se for número
        if re.search(r'\d', t):
            try:
                val = float(t)
                # Correção lógica: se leu 116 (inteiro), volta para 1.16
                if val > 100 and '.' not in t:
                    val = float(t[0] + "." + t[1:])
                
                if 1.0 <= val <= 5000:
                    # Pega a posição para ordenar a grade
                    y_centro = np.mean([p[1] for p in bbox])
                    x_centro = np.mean([p[0] for p in bbox])
                    itens.append({'y': y_centro, 'x': x_centro, 'v': val})
            except: continue

    # 4. ORDENAÇÃO: Linha por linha, da Esquerda para a Direita
    itens.sort(key=lambda i: (i['y'] // 30, i['x']))
    
    return [i['v'] for i in itens]

# =========================
# INTERFACE (SEU LAYOUT)
# =========================
st.title("PROJETO 10.000 VELAS")

aba1, aba2 = st.tabs(["INSERIR MANUAL", "INSERIR POR PRINT"])

with aba1:
    manual = st.text_area("Ex: 1.16x, 9.64x", height=100)
with aba2:
    arquivo = st.file_uploader("Envie o print aqui", type=['png','jpg','jpeg'])

if st.button("🚀 ADICIONAR E SINCRONIZAR", use_container_width=True):
    novas_lidas = []
    if arquivo:
        with st.spinner("Lendo grade de velas..."):
            novas_lidas = extrair_velas_print(Image.open(arquivo))
    
    if manual:
        novas_lidas += [float(n) for n in re.findall(r"(\d+(?:\.\d+)?)", manual.replace(',', '.'))]

    if novas_lidas:
        # Lógica para não duplicar se o print tiver velas que já estão no banco
        for v in novas_lidas:
            if not st.session_state.velas or v != st.session_state.velas[-1]:
                st.session_state.velas.append(v)
        
        salvar()
        st.success(f"✅ {len(novas_lidas)} velas processadas com sucesso!")
        st.rerun()

st.divider()

# BUSCA DE PADRÃO (Sua lógica de busca)
st.write("**BUSCA DE PADRÃO**")
col_b1, col_b2 = st.columns([0.8, 0.2])
with col_b1:
    seq = st.text_input("Digite o padrão...", label_visibility="collapsed")
with col_b2:
    if st.button("🔎"):
        if seq:
            padrao = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)", seq.replace(',', '.'))]
            h = st.session_state.velas
            for i in range(len(h) - len(padrao)):
                if h[i:i+len(padrao)] == padrao:
                    st.write(f"📍 Achado! Próxima: **{h[i+len(padrao)]:.2f}x**")

st.divider()

# HISTÓRICO E ÚLTIMAS 20
st.write(f"**HISTÓRICO (Total: {len(st.session_state.velas)})**")
if st.session_state.velas:
    df_hist = pd.DataFrame({"vela": reversed(st.session_state.velas)})
    st.dataframe(df_hist.style.map(lambda v: "color:#FF00FF" if v>=10 else "color:#00FF00" if v>=2 else "color:white").format("{:.2f}x"), use_container_width=True, height=300)

col_f1, col_f2 = st.columns([0.6, 0.4])
with col_f1:
    st.write("**ÚLTIMAS 20**")
    if st.session_state.velas:
        ultimas = st.session_state.velas[-20:]
        txt = [f"<b style='color:{('#FF00FF' if v>=10 else '#00FF00' if v>=2 else '#FFF')}'>{v:.2f}x</b>" for v in ultimas]
        st.markdown(" , ".join(txt), unsafe_allow_html=True)
with col_f2:
    if st.button("APAGAR ÚLTIMAS 20"):
        st.session_state.velas = st.session_state.velas[:-20]; salvar(); st.rerun()
    if st.button("ZERAR TUDO"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []; st.rerun()
