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

# ==========================================
# A LÓGICA QUE VOCÊ PEDIU: "X" NO FINAL + ORDEM
# ==========================================
def extrair_velas_print(img):
    reader = load_reader()
    img_np = np.array(img.convert('L'))
    h, w = img_np.shape
    # Foco na grade de velas
    corte = img_np[int(h*0.52):int(h*0.88), int(w*0.08):int(w*0.78)]
    _, bin_img = cv2.threshold(corte, 165, 255, cv2.THRESH_BINARY)
    
    res = reader.readtext(bin_img)
    itens = []
    for (bbox, texto, conf) in res:
        t = texto.lower().replace(',', '.').strip()
        
        # 1. SÓ OLHA PARA OS NÚMEROS COM "X" NO FINAL
        if 'x' in t:
            num_match = re.search(r"(\d+(?:\.\d+)?)", t)
            if num_match:
                val = float(num_match.group(1))
                # Correção do ponto (ex: 116 vira 1.16)
                if val > 100 and '.' not in t: val = float(str(val)[:1] + "." + str(val)[1:])
                
                # Posição para ordenar
                y_centro = np.mean([p[1] for p in bbox])
                x_centro = np.mean([p[0] for p in bbox])
                itens.append({'y': y_centro, 'x': x_centro, 'v': val})

    # 2. TRANSCREVE DE BAIXO PARA CIMA (Y descrescente)
    # 3. DA DIREITA PARA A ESQUERDA (X decrescente)
    itens.sort(key=lambda i: i['y'], reverse=True) # Baixo para cima
    
    velas_ordenadas = []
    # Agrupa por linhas para garantir a ordem horizontal correta
    linhas_temp = []
    for item in itens:
        colocado = False
        for linha in linhas_temp:
            if abs(linha[0]['y'] - item['y']) < 25:
                linha.append(item)
                colocado = True
                break
        if not colocado: linhas_temp.append([item])
    
    for linha in linhas_temp:
        linha.sort(key=lambda i: i['x'], reverse=True) # Direita para Esquerda
        for item in linha:
            velas_ordenadas.append(item['v'])
            
    return velas_ordenadas

# =========================
# INTERFACE (SEU DESENHO)
# =========================
st.title("PROJETO 10.000 VELAS")

aba1, aba2 = st.tabs(["INSERIR MANUAL", "INSERIR POR PRINT"])

with aba2:
    arquivo = st.file_uploader("Envie o print", type=['png','jpg','jpeg'])

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    if arquivo:
        novas = extrair_velas_print(Image.open(arquivo))
        if novas:
            # Sincroniza para não repetir velas que já estão no banco
            for v in novas:
                if not st.session_state.velas or v != st.session_state.velas[-1]:
                    st.session_state.velas.append(v)
            salvar()
            st.success(f"{len(novas)} velas adicionadas na ordem correta!")
            st.rerun()

st.divider()

# BUSCA, HISTÓRICO E RESET (IGUAIS AO SEU ORIGINAL)
st.write("**HISTÓRICO COMPLETO**")
if st.session_state.velas:
    df_h = pd.DataFrame({"vela": reversed(st.session_state.velas)})
    st.dataframe(df_h.style.map(lambda v: "color:#FF00FF" if v>=10 else "color:#00FF00" if v>=2 else "color:white").format("{:.2f}x"), use_container_width=True, height=350)

col_f1, col_f2 = st.columns([0.6, 0.4])
with col_f2:
    if st.button("APAGAR ÚLTIMAS 20"):
        st.session_state.velas = st.session_state.velas[:-20]; salvar(); st.rerun()
    if st.button("ZERAR TUDO"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []; st.rerun()
