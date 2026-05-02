import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# ================================
# 1. BANCO DE DADOS (ANTI-LIXO)
# ================================
DB_FILE = "banco_velas_projeto.csv"

if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df_load = pd.read_csv(DB_FILE)
            st.session_state.velas = [
                float(v) for v in df_load['velas'].dropna().tolist()
                if isinstance(v, (int, float)) and v > 0
            ]
        except:
            st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    if st.session_state.velas:
        pd.DataFrame({'velas': st.session_state.velas}).to_csv(DB_FILE, index=False)

# ================================
# 2. OCR OTIMIZADO
# ================================
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

def preprocessar_imagem(img):
    img = img.convert('L')  # escala de cinza
    img = np.array(img)

    # aumenta contraste (remove fundo)
    img = np.where(img > 150, 255, 0).astype(np.uint8)

    return img

def extrair_velas(texto):
    # LIMPEZA PESADA (remove espaços fantasmas)
    texto = texto.replace(',', '.')
    texto = texto.replace(' ', '')
    texto = texto.replace('\n', '')
    texto = texto.replace('-', '')

    # REGEX MELHORADO
    encontrados = re.findall(r"\d+(?:\.\d+)?(?=[xX])", texto)

    velas = []
    for v in encontrados:
        try:
            val = float(v)

            # FILTRO INTELIGENTE
            if val < 1.0 or val > 1000:
                continue

            velas.append(val)

        except:
            continue

    return velas

# ================================
# 3. INTERFACE
# ================================
st.markdown("<h2 style='text-align: center;'>ATE 500 VELAS</h2>", unsafe_allow_html=True)

aba_manual, aba_print = st.tabs(["📥 MANUAL", "📸 PRINT"])

with aba_manual:
    manual_txt = st.text_area("Exemplo: 1.25x 4.10x", height=100)

with aba_print:
    arquivo = st.file_uploader("Suba o print aqui", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

# ================================
# 4. PROCESSAMENTO
# ================================
if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):

    texto_bruto = ""

    # OCR
    if arquivo:
        with st.spinner("Lendo imagem..."):
            img = preprocessar_imagem(Image.open(arquivo))
            res = reader.readtext(img, detail=0)
            texto_bruto += " ".join(res)

    # manual
    if manual_txt:
        texto_bruto += " " + manual_txt

    if texto_bruto:
        novas = extrair_velas(texto_bruto)

        # ANTI-DUPLICAÇÃO INTELIGENTE
        ultimas = st.session_state.velas[-20:]
        ponto = 0

        for i in range(len(novas)):
            for j in range(len(ultimas) - 1):
                if novas[i:i+2] == ultimas[j:j+2]:
                    ponto = i + 2

        final = novas[ponto:]

        if final:
            st.session_state.velas.extend(final)
            salvar()
            st.success(f"✅ {len(final)} velas adicionadas!")
            st.rerun()
        else:
            st.warning("Nenhuma vela nova detectada.")

st.divider()

# ================================
# 5. BUSCA DE PADRÃO
# ================================
st.subheader("🔍 BUSCA DE PADRAO")

col_in, col_bt = st.columns([0.85, 0.15])

with col_in:
    seq_alvo = st.text_input("Padrao de velas:", placeholder="Ex: 1.25 2.00")

with col_bt:
    if st.button("🔎"):
        if seq_alvo:
            try:
                padrao = [
                    float(x.replace('x', '').strip())
                    for x in seq_alvo.replace(',', ' ').split()
                    if x.strip()
                ]

                hist = st.session_state.velas
                achou = False

                for i in range(len(hist) - len(padrao)):
                    if hist[i:i+len(padrao)] == padrao:
                        achou = True
                        st.success("🎯 PADRÃO ENCONTRADO!")

                        futuro = hist[i+len(padrao):i+len(padrao)+15]

                        if futuro:
                            fmt = [
                                f"<b style='color:{'#FF00FF' if v >= 8 else '#00FF00' if v >= 2 else '#FFFFFF'};'>{v:.2f}x</b>"
                                for v in futuro
                            ]
                            st.markdown(" , ".join(fmt), unsafe_allow_html=True)

                if not achou:
                    st.error("Não encontrado.")

            except:
                st.error("Erro no padrão digitado.")

st.divider()

# ================================
# 6. HISTÓRICO
# ================================
st.subheader("📋 HISTORICO DE VELAS")

if st.session_state.velas:
    velas_exibir = [v for v in st.session_state.velas[::-1] if v > 0]

    df = pd.DataFrame({"Vela": velas_exibir})

    st.dataframe(
        df.style.map(
            lambda x: 'color: #FF00FF; font-weight: bold' if x >= 8 else 'color: white'
        ).format("{:.2f}x"),
        use_container_width=True,
        height=400
    )

st.divider()

# ================================
# 7. ÚLTIMAS 20
# ================================
st.subheader("📉 ULTIMAS 20 VELAS")

if st.session_state.velas:
    ultimas = [v for v in st.session_state.velas[-20:][::-1] if v > 0]

    resumo = [
        f"<b style='color:{'#FF00FF' if v >= 8 else '#00FF00' if v >= 2 else '#FFFFFF'};'>{v:.2f}x</b>"
        for v in ultimas
    ]

    st.markdown(" , ".join(resumo), unsafe_allow_html=True)

st.divider()

# ================================
# 8. RESET
# ================================
if st.checkbox("Liberar Reset"):

    c1, c2 = st.columns(2)

    with c1:
        if st.button("🗑️ APAGAR ÚLTIMAS 20"):
            st.session_state.velas = st.session_state.velas[:-20]
            salvar()
            st.rerun()

    with c2:
        if st.button("🔥 ZERAR TUDO"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            st.session_state.velas = []
            st.rerun()
