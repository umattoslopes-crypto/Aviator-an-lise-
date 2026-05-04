import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import numpy as np
import cv2

# =========================
# CONFIGURAÇÕES E BANCO
# =========================
try:
    import easyocr
    OCR_OK = True
except:
    OCR_OK = False

DB_FILE = "banco_velas_projeto.csv"
LIMITE = 10000

if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.velas = [float(v) for v in df['vela'].dropna() if float(v) > 0]
        except:
            st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'vela': st.session_state.velas[-LIMITE:]}).to_csv(DB_FILE, index=False)

@st.cache_resource
def load_reader():
    if not OCR_OK: return None
    try:
        return easyocr.Reader(['en'], gpu=False, verbose=False)
    except: return None

reader = load_reader()

# =========================
# FUNÇÃO DE LEITURA (OCR)
# =========================
def extrair_velas_print(img):
    try:
        img_np = np.array(img.convert('RGB'))
        h, w = img_np.shape[:2]

        # Corte da área das velas (Big Bass Crash)
        corte = img_np[int(h*0.52):int(h*0.88), int(w*0.08):int(w*0.78)]
        
        gray = cv2.cvtColor(corte, cv2.COLOR_RGB2GRAY)
        # Ajuste de contraste para o ponto decimal (.) não sumir
        gray = cv2.convertScaleAbs(gray, alpha=1.6, beta=15)
        _, bin_img = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        if reader is None: return []

        resultados = reader.readtext(bin_img, detail=1)
        itens = []

        for (bbox, texto, conf) in resultados:
            t = texto.lower().replace(',', '.').replace(' ', '').strip()
            # Captura números. Se vier sem ponto (ex: 116), corrigimos para 1.16
            nums = re.findall(r"(\d+(?:\.\d+)?)", t)
            for n in nums:
                try:
                    valor = float(n)
                    if valor > 100 and '.' not in n:
                        valor = float(n[0] + "." + n[1:])
                    
                    if 1.0 <= valor <= 5000:
                        y = np.mean([p[1] for p in bbox])
                        x = np.mean([p[0] for p in bbox])
                        itens.append({'x': x, 'y': y, 'v': valor})
                except: pass

        # Agrupamento por linhas (tolerância de 25 pixels)
        linhas = []
        for item in sorted(itens, key=lambda i: i['y']):
            colocado = False
            for linha in linhas:
                if abs(linha[0]['y'] - item['y']) < 25:
                    linha.append(item)
                    colocado = True
                    break
            if not colocado: linhas.append([item])

        # Ordem: Debaixo p/ Cima e Direita p/ Esquerda
        linhas.sort(key=lambda l: l[0]['y'], reverse=True)
        velas_finais = []
        for linha in linhas:
            linha.sort(key=lambda i: i['x'], reverse=True)
            for item in linha:
                velas_finais.append(item['v'])
        return velas_finais
    except: return []

# =========================
# INTERFACE (LAYOUT DO DESENHO)
# =========================
st.set_page_config(page_title="Analisador de Velas", layout="centered")
st.title("ATE 10.000 VELAS")

# 1. ABAS DE INSERÇÃO
aba1, aba2 = st.tabs(["INSERIR MANUAL", "INSERIR POR PRINT"])

with aba1:
    manual = st.text_area("Exemplo: 1.16x 10.71x 5x", height=100)

with aba2:
    arquivo = st.file_uploader("Envie o print dos resultados", type=['png','jpg','jpeg'])

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    novas = []
    if arquivo:
        with st.spinner("Lendo print..."):
            novas = extrair_velas_print(Image.open(arquivo))
    if manual:
        # Pega números do manual também
        m_nums = re.findall(r"(\d+(?:\.\d+)?)", manual.replace(',', '.'))
        novas += [float(n) for n in m_nums]

    if novas:
        st.session_state.velas += novas
        if len(st.session_state.velas) > LIMITE:
            st.session_state.velas = st.session_state.velas[-LIMITE:]
        salvar()
        st.success(f"{len(novas)} velas adicionadas!")
        st.rerun()

st.divider()

# 2. BUSCA DE PADRÃO (Botão ao lado do Input)
st.write("**BUSCA DE PADRÃO**")
col_b1, col_b2 = st.columns([0.8, 0.2])
with col_b1:
    seq = st.text_input("Sequência...", label_visibility="collapsed", placeholder="Ex: 1.20 2.50")
with col_b2:
    if st.button("🔎"):
        if seq:
            padrao = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)", seq.replace(',', '.'))]
            h = st.session_state.velas
            achou = False
            for i in range(len(h) - len(padrao) + 1):
                if h[i:i+len(padrao)] == padrao:
                    st.success(f"Achado! Próximas: {h[i+len(padrao):i+len(padrao)+5]}")
                    achou = True
            if not achou: st.warning("Padrão não encontrado.")

st.divider()

# 3. HISTÓRICO DE VELAS (Tabela central)
st.write(f"**HISTÓRICO DE VELAS (Total: {len(st.session_state.velas)})**")
if st.session_state.velas:
    df_h = pd.DataFrame({"vela": reversed(st.session_state.velas)})
    st.dataframe(
        df_h.style.map(lambda v: "color:#FF00FF; font-weight:bold" if v >= 8 else "color:#00FF00" if v >= 2 else "color:white").format("{:.2f}x"),
        use_container_width=True, height=350
    )

st.divider()

# 4. ÚLTIMAS 20 E REDEFINIR (Lado a Lado como no desenho)
col_f1, col_f2 = st.columns([0.6, 0.4])

with col_f1:
    st.write("**ULTIMA 20 VELA ADICIONADA**")
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
