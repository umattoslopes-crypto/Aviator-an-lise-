import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# ================================
# BANCO DE DADOS (10.000 VELAS)
# ================================
DB_FILE = "banco_velas_projeto.csv"

if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df_load = pd.read_csv(DB_FILE)
            st.session_state.velas = [float(v) for v in df_load['velas'].dropna().tolist() if float(v) > 0][-10000:]
        except: st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    if st.session_state.velas:
        pd.DataFrame({'velas': st.session_state.velas[-10000:]}).to_csv(DB_FILE, index=False)

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

def preprocessar(img):
    img = img.convert('L')
    img = np.array(img)
    img = np.where(img > 150, 255, 0).astype(np.uint8)
    return img

def organizar_posicao_invertida(res):
    itens = []
    for (bbox, texto, conf) in res:
        if 'x' in texto.lower():
            # Coordenadas do polígono (y, x)
            y = bbox[0][1]
            x = bbox[0][0]
            itens.append((y, x, texto))
    # Ordena de baixo para cima (Y desc) e direita para esquerda (X desc)
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
# INTERFACE PRINCIPAL
# ================================
st.markdown("<h2 style='text-align: center;'>HISTÓRICO 10.000 VELAS</h2>", unsafe_allow_html=True)

aba1, aba2 = st.tabs(["📥 MANUAL", "📸 PRINT"])

with aba1:
    manual = st.text_area("Ex: 1.25x 4.10x", height=100)

with aba2:
    arquivo = st.file_uploader("", type=['png','jpg','jpeg'], label_visibility="collapsed")

if st.button("🚀 ADICIONAR", use_container_width=True):
    texto_total = ""
    if arquivo:
        with st.spinner("Processando leitura reversa..."):
            img = preprocessar(Image.open(arquivo))
            res = reader.readtext(img)
            texto_total += organizar_posicao_invertida(res)
    if manual:
        texto_total += " " + manual

    if texto_total:
        novas = extrair_velas(texto_total)
        # Sincronização inteligente (Anti-duplicação)
        ultimas_ref = st.session_state.velas[-30:]
        final = [v for v in novas if v not in ultimas_ref]

        if final:
            st.session_state.velas.extend(final)
            st.session_state.velas = st.session_state.velas[-10000:]
            salvar()
            st.success(f"✅ {len(final)} velas inéditas adicionadas!")
            st.rerun()
        else:
            st.warning("Nenhuma vela nova detectada.")

st.divider()

# ================================
# VISUALIZAÇÃO DO BANCO (SIMPLIFICADA PARA EVITAR ERRO)
# ================================
st.subheader(f"📋 BANCO ({len(st.session_state.velas)}/10.000)")

if st.session_state.velas:
    # Exibimos a tabela sem o estilo map que causa erro em algumas versões do Streamlit
    df_banco = pd.DataFrame({"Vela": [f"{v:.2f}x" for v in st.session_state.velas[::-1]]})
    st.dataframe(df_banco, use_container_width=True, height=400)

st.divider()

# ================================
# ÚLTIMAS 20 (RODAPÉ COLORIDO)
# ================================
st.subheader("📉 ÚLTIMAS 20 ADICIONADAS")
if st.session_state.velas:
    exibir_20 = st.session_state.velas[-20:][::-1]
    chips = []
    for v in exibir_20:
        cor = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#FFFFFF"
        chips.append(f"<b style='color:{cor}; font-size:1.1em;'>{v:.2f}x</b>")
    st.markdown(" , ".join(chips), unsafe_allow_html=True)

# RESET NA BARRA LATERAL
if st.sidebar.checkbox("⚙️ Configurações"):
    if st.sidebar.button("🗑️ Reset últimas 20"):
        st.session_state.velas = st.session_state.velas[:-20]
        salvar(); st.rerun()
    if st.sidebar.button("🔥 Zerar Tudo"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []; st.rerun()
