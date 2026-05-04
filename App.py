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
# OCR E SINCRONIZAÇÃO
# =========================
def extrair_velas_print(img):
    reader = load_reader()
    img_np = np.array(img.convert('L'))
    h, w = img_np.shape
    # Foco na grade de velas
    corte = img_np[int(h*0.52):int(h*0.88), int(w*0.08):int(w*0.78)]
    _, bin_img = cv2.threshold(corte, 160, 255, cv2.THRESH_BINARY)
    
    res = reader.readtext(bin_img)
    itens = []
    for (bbox, texto, conf) in res:
        t = texto.lower().replace(',', '.').replace(' ', '').strip()
        nums = re.findall(r"(\d+(?:\.\d+)?)", t)
        for n in nums:
            try:
                v = float(n)
                if v > 100 and '.' not in n: v = float(n + "." + n[1:])
                if 1.0 <= v <= 5000:
                    y = np.mean([p for p in bbox])
                    x = np.mean([p for p in bbox])
                    itens.append({'x': x, 'y': y, 'v': v})
            except: continue
    
    # Ordena para seguir o fluxo do jogo: Direita para Esquerda, Cima para Baixo
    itens.sort(key=lambda i: (i['y'] // 30, i['x']), reverse=True)
    return [i['v'] for i in itens]

# =========================
# INTERFACE COM SINCRONISMO
# =========================
st.title("SCANNER DE CICLOS SINCRONIZADO")

aba1, aba2 = st.tabs(["INSERIR MANUAL", "INSERIR POR PRINT"])

with aba2:
    arquivo = st.file_uploader("Suba seus prints em ordem", type=['png','jpg','jpeg'])

if st.button("🚀 ADICIONAR E SINCRONIZAR"):
    if arquivo:
        velas_do_print = extrair_velas_print(Image.open(arquivo))
        
        if velas_do_print:
            # --- LÓGICA DE SINCRONIZAÇÃO ---
            if len(st.session_state.velas) >= 4:
                # Pegamos as últimas 4 velas do banco para servir de "âncora"
                ancora = st.session_state.velas[-4:]
                
                # Procuramos essa sequência exata no print
                index_sinc = -1
                for i in range(len(velas_do_print) - 3):
                    if velas_do_print[i:i+4] == ancora:
                        index_sinc = i + 4 # O ponto de partida é após a âncora
                        break
                
                if index_sinc != -1:
                    novas = velas_do_print[index_sinc:]
                    st.session_state.velas += novas
                    st.success(f"Sincronizado! {len(novas)} novas velas adicionadas.")
                else:
                    # Se não achou a âncora, adiciona tudo (pode ser um print de outro horário)
                    st.session_state.velas += velas_do_print
                    st.warning("Sequência nova detectada. Adicionado sem sincronia.")
            else:
                # Se o banco for pequeno, adiciona tudo
                st.session_state.velas += velas_do_print
                st.success("Primeiras velas adicionadas!")
            
            salvar()
            st.rerun()

# =========================
# BUSCA E HISTÓRICO
# =========================
st.divider()
st.write("**HISTÓRICO COMPLETO (Sincronizado)**")
if st.session_state.velas:
    df_h = pd.DataFrame({"vela": reversed(st.session_state.velas)})
    st.dataframe(df_h.style.map(lambda v: "color:#FF00FF" if v>=10 else "color:#00FF00" if v>=2 else "color:white").format("{:.2f}x"), use_container_width=True, height=350)

if st.button("ZERAR TUDO"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.session_state.velas = []; st.rerun()
