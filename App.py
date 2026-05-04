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
# BANCO DE DADOS (LIMPEZA DEFINITIVA)
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # Carrega e limpa qualquer valor nulo ou erro anterior
            st.session_state.velas = [float(v) for v in df['vela'].dropna() if float(v) > 0]
        except: st.session_state.velas = []
    else: st.session_state.velas = []

def salvar():
    pd.DataFrame({'vela': st.session_state.velas[-LIMITE:]}).to_csv(DB_FILE, index=False)

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

# =========================
# OCR (AJUSTADO PARA O BIG BASS)
# =========================
def extrair_velas_print(img):
    reader = load_reader()
    img_np = np.array(img.convert('L'))
    h, w = img_np.shape
    corte = img_np[int(h*0.52):int(h*0.88), int(w*0.08):int(w*0.78)]
    _, bin_img = cv2.threshold(corte, 165, 255, cv2.THRESH_BINARY)
    
    res = reader.readtext(bin_img)
    itens = []
    for (bbox, texto, conf) in res:
        t = texto.lower().replace(',', '.').strip()
        # Captura apenas o que tem número e 'x'
        num_match = re.search(r"(\d+(?:\.\d+)?)", t)
        if num_match:
            val = float(num_match.group(1))
            # Correção do 1.16x se o ponto sumir
            if val > 100 and '.' not in t: val = float(str(val) + "." + str(val)[1:])
            
            y = np.mean([p[1] for p in bbox])
            x = np.mean([p[0] for p in bbox])
            itens.append({'x': x, 'y': y, 'v': val})

    # Ordena da esquerda para a direita, linha por linha
    itens.sort(key=lambda i: (i['y'] // 30, i['x']))
    return [i['v'] for i in itens]

# =========================
# INTERFACE (LAYOUT DO SEU DESENHO)
# =========================
st.title("ATE 10.000 VELAS")

aba1, aba2 = st.tabs(["INSERIR MANUAL", "INSERIR POR PRINT"])

with aba1:
    # MUDANÇA AQUI: Instrução clara para não haver erro humano
    manual = st.text_area("Cole as velas exatamente como transcrevi (Ex: 1.16x 9.64x 5.00x)", height=150)

with aba2:
    arquivo = st.file_uploader("Envie o print aqui", type=['png','jpg','jpeg'])

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    novas = []
    if arquivo:
        with st.spinner("Lendo print..."):
            novas = extrair_velas_print(Image.open(arquivo))
    
    if manual:
        # AQUI ESTÁ A FIDELIDADE: Ele captura cada número decimal individualmente
        # Não importa se tem espaço, vírgula ou 'x', ele pega o valor real
        m_nums = re.findall(r"(\d+(?:\.\d+)?)", manual.replace(',', '.'))
        novas += [float(n) for n in m_nums]

    if novas:
        # Adiciona ao banco garantindo que são números válidos
        st.session_state.velas += novas
        if len(st.session_state.velas) > LIMITE:
            st.session_state.velas = st.session_state.velas[-LIMITE:]
        salvar()
        st.success(f"{len(novas)} velas adicionadas fielmente!")
        st.rerun()

st.divider()

# BUSCA DE PADRÃO
st.write("**BUSCA DE PADRÃO**")
col_b1, col_b2 = st.columns([0.8, 0.2])
with col_b1:
    seq = st.text_input("Digite a sequência...", label_visibility="collapsed")
with col_b2:
    if st.button("🔎"):
        if seq:
            padrao = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)", seq.replace(',', '.'))]
            h = st.session_state.velas
            achou = False
            for i in range(len(h) - len(padrao)):
                if h[i:i+len(padrao)] == padrao:
                    st.success(f"Achado! Próxima: **{h[i+len(padrao)]:.2f}x**")
                    achou = True
            if not achou: st.warning("Padrão não encontrado.")

st.divider()

# HISTÓRICO (SEM LINHAS BRANCAS)
st.write(f"**HISTÓRICO (Total: {len(st.session_state.velas)})**")
if st.session_state.velas:
    # Mostra do mais novo para o mais velho
    df_h = pd.DataFrame({"vela": reversed(st.session_state.velas)})
    st.dataframe(
        df_h.style.map(lambda v: "color:#FF00FF; font-weight:bold" if v >= 8 else "color:#00FF00" if v >= 2 else "color:white").format("{:.2f}x"),
        use_container_width=True, height=350
    )

st.divider()

# ÚLTIMAS 20 (SEM VÍRGULAS VAZIAS) E RESET
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
