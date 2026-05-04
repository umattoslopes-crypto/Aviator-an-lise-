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
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'vela': st.session_state.velas[-LIMITE:]}).to_csv(DB_FILE, index=False)

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

# =========================
# OCR COM FOCO NO PONTO DECIMAL
# =========================
def extrair_velas_print(img):
    reader = load_reader()
    img_np = np.array(img.convert('RGB'))
    h, w = img_np.shape[:2]
    
    # Corte da área das velas
    area = img_np[int(h*0.52):int(h*0.88), int(w*0.08):int(w*0.78)]
    
    # --- MELHORIA PARA O PONTO DECIMAL ---
    # 1. Aumenta a imagem em 2x (ajuda a IA a ver o ponto)
    area = cv2.resize(area, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # 2. Converte para cinza e aumenta a nitidez (Unsharp Mask)
    gray = cv2.cvtColor(area, cv2.COLOR_RGB2GRAY)
    gaussian = cv2.GaussianBlur(gray, (0, 0), 3)
    gray = cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0)
    
    # 3. Binarização suave para não apagar o ponto
    _, bin_img = cv2.threshold(gray, 165, 255, cv2.THRESH_BINARY)

    res = reader.readtext(bin_img)
    itens = []
    for (bbox, texto, conf) in res:
        t = texto.lower().replace(',', '.').replace(' ', '').strip()
        
        # Busca números decimais
        nums = re.findall(r"(\d+(?:\.\d+)?)", t)
        for n in nums:
            try:
                val = float(n)
                
                # RECONSTRUÇÃO LÓGICA: Se o ponto sumiu (ex: 116), nós forçamos o ponto.
                # Como velas > 100 são raras, se ler 116 num lugar de vela baixa, corrigimos.
                if val > 100 and '.' not in n:
                    # Transforma 116 em 1.16 ou 964 em 9.64
                    val = float(n[0] + "." + n[1:])
                
                if 1.0 <= val <= 5000:
                    y = np.mean([p[1] for p in bbox])
                    x = np.mean([p[0] for p in bbox])
                    itens.append({'x': x, 'y': y, 'v': val})
            except: continue

    # Ordena da esquerda para a direita, linha por linha
    itens.sort(key=lambda i: (i['y'] // 50, i['x']))
    return [i['v'] for i in itens]

# =========================
# INTERFACE (LAYOUT DO DESENHO)
# =========================
st.title("ATE 10.000 VELAS")

aba1, aba2 = st.tabs(["INSERIR MANUAL", "INSERIR POR PRINT"])

with aba1:
    manual = st.text_area("Ex: 1.16x, 10.71x", height=100)
with aba2:
    arquivo = st.file_uploader("Envie o print aqui", type=['png','jpg','jpeg'])

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    novas = []
    if arquivo:
        with st.spinner("Refinando imagem..."):
            novas = extrair_velas_print(Image.open(arquivo))
    if manual:
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
    st.dataframe(
        df_h.style.map(lambda v: "color:#FF00FF; font-weight:bold" if v>=8 else "color:#00FF00" if v>=2 else "color:white").format("{:.2f}x"),
        use_container_width=True, height=350
    )

st.divider()

# ÚLTIMAS 20 E REDEFINIR
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
