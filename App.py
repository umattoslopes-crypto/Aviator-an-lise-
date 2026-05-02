import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# ================================
# BANCO DE DADOS (LIMITE 10.000)
# ================================
DB_FILE = "banco_velas_projeto.csv"

if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.velas = [float(v) for v in df['velas'].dropna() if float(v) > 0][-10000:]
        except: st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    if st.session_state.velas:
        pd.DataFrame({'velas': st.session_state.velas[-10000:]}).to_csv(DB_FILE, index=False)

# ================================
# OCR - LEITURA INVERTIDA (BAIXO -> CIMA | DIREITA -> ESQUERDA)
# ================================
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

def preprocessar(img):
    img = img.convert('L')
    img = np.array(img)
    img = np.where(img > 150, 255, 0).astype(np.uint8)
    return img

def organizar_por_posicao_invertida(res):
    itens = []
    for (bbox, texto, conf) in res:
        if 'x' in texto.lower():
            # Pega as coordenadas do topo (y) e esquerda (x)
            y, x = bbox[0][1], bbox[0][0]
            itens.append((y, x, texto))

    # ORDENAÇÃO: Inverte Y (baixo para cima) e dps X (direita para esquerda)
    itens.sort(key=lambda i: (i[0], i[1]), reverse=True)
    return " ".join([i[2] for i in itens])

def extrair_velas(texto):
    texto = texto.lower().replace(',', '.').replace(' ', '')
    encontrados = re.findall(r"\d+\.\d+x|\d+x", texto)
    
    velas = []
    for v in encontrados:
        try:
            val = float(v.replace('x', ''))
            if 1.0 <= val <= 10000: velas.append(val)
        except: continue
    return velas

# ================================
# INTERFACE
# ================================
st.markdown("<h2 style='text-align: center;'>HISTÓRICO 10.000 VELAS</h2>", unsafe_allow_html=True)

aba1, aba2 = st.tabs(["📥 MANUAL", "📸 PRINT"])

with aba1:
    manual = st.text_area("Ex: 1.25x 4.10x")

with aba2:
    arquivo = st.file_uploader("", type=['png','jpg','jpeg'])

# ================================
# PROCESSAMENTO
# ================================
if st.button("🚀 ADICIONAR", use_container_width=True):
    texto = ""
    if arquivo:
        with st.spinner("Processando leitura invertida..."):
            img = preprocessar(Image.open(arquivo))
            res = reader.readtext(img, detail=1)
            texto += organizar_por_posicao_invertida(res)

    if manual:
        texto += " " + manual

    if texto:
        novas = extrair_velas(texto)
        
        # Filtro de duplicidade (compara com o final do banco)
        ultimas_ref = st.session_state.velas[-30:]
        final = [v for v in novas if v not in ultimas_ref]

        if final:
            st.session_state.velas.extend(final)
            st.session_state.velas = st.session_state.velas[-10000:]
            salvar()
            st.success(f"{len(final)} velas adicionadas!")
            st.rerun()

st.divider()

# ================================
# VISUALIZAÇÃO: HISTÓRICO COMPLETO
# ================================
st.subheader(f"📋 BANCO ({len(st.session_state.velas)}/10.000)")

if st.session_state.velas:
    df = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
    
    def colorir_8x(val):
        v = float(val.replace('x', ''))
        return 'color: #FF00FF; font-weight: bold' if v >= 8.0 else 'color: white'

    st.dataframe(
        df.style.format("{:.2f}x").applymap(colorir_8x),
        use_container_width=True, height=400
    )

st.divider()

# ================================
# ÚLTIMAS 20 (CORRIGIDO: SEGUE A ORDEM DO BANCO)
# ================================
st.subheader("📉 ÚLTIMAS 20 VELAS")
if st.session_state.velas:
    # Pegamos as 20 mais recentes (final da lista) e mostramos da mais nova para a mais velha
    exibir = st.session_state.velas[-20:][::-1]
    
    texto_resumo = [
        f"<b style='color:{'#FF00FF' if v >= 8 else '#00FF00' if v >= 2 else '#FFFFFF'}'>{v:.2f}x</b>"
        for v in exibir
    ]
    st.markdown(" , ".join(texto_resumo), unsafe_allow_html=True)

# RESET
st.divider()
if st.checkbox("⚙️ Configurações"):
    if st.button("Apagar últimas 20"):
        st.session_state.velas = st.session_state.velas[:-20]
        salvar(); st.rerun()
    if st.button("Zerar tudo"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []; st.rerun()
