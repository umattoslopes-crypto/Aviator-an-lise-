import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import numpy as np
import cv2
import easyocr

# =========================
# CONFIGURAÇÕES E BANCO
# =========================
DB_FILE = "banco_velas_projeto.csv"
LIMITE = 10000

if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # Carrega e limpa linhas vazias
            st.session_state.velas = [float(v) for v in df['vela'].dropna() if float(v) > 0]
        except: st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'vela': st.session_state.velas[-LIMITE:]}).to_csv(DB_FILE, index=False)

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

# ==========================================
# FÓRMULA DE LEITURA: "X" + ORDEM ESPECÍFICA
# ==========================================
def extrair_velas_print(img):
    reader = load_reader()
    img_np = np.array(img.convert('L'))
    h, w = img_np.shape
    
    # Corte da grade de velas (Big Bass Crash)
    corte = img_np[int(h*0.52):int(h*0.88), int(w*0.08):int(w*0.78)]
    # Binarização para destacar o branco dos números
    _, bin_img = cv2.threshold(corte, 165, 255, cv2.THRESH_BINARY)
    
    res = reader.readtext(bin_img)
    itens = []
    
    for (bbox, texto, conf) in res:
        t = texto.lower().replace(',', '.').strip()
        
        # 1. SÓ OLHA PARA OS NÚMEROS COM "X" NO FINAL
        if 'x' in t:
            num_match = re.search(r"(\d+(?:\.\d+)?)", t)
            if num_match:
                try:
                    val = float(num_match.group(1))
                    # Correção automática do ponto (ex: 116 vira 1.16)
                    if val > 100 and '.' not in t:
                        val = float(str(val)[0] + "." + str(val)[1:])
                    
                    if 1.0 <= val <= 5000:
                        # Coordenadas para ordenação
                        y_centro = np.mean([p[1] for p in bbox])
                        x_centro = np.mean([p[0] for p in bbox])
                        itens.append({'y': y_centro, 'x': x_centro, 'v': val})
                except: continue

    # 2. AGRUPAR POR LINHAS (Tolerância de 25px)
    linhas_temp = []
    for item in sorted(itens, key=lambda i: i['y']):
        colocado = False
        for linha in linhas_temp:
            if abs(linha[0]['y'] - item['y']) < 25:
                linha.append(item)
                colocado = True
                break
        if not colocado:
            linhas_temp.append([item])

    # 3. ORDEM: DE BAIXO PARA CIMA (Y Inverso)
    linhas_temp.sort(key=lambda l: l[0]['y'], reverse=True)
    
    velas_ordenadas = []
    for linha in linhas_temp:
        # 4. ORDEM: DA DIREITA PARA A ESQUERDA (X Inverso)
        linha.sort(key=lambda i: i['x'], reverse=True)
        for item in linha:
            velas_ordenadas.append(item['v'])
            
    return velas_ordenadas

# =========================
# INTERFACE (LAYOUT DO DESENHO)
# =========================
st.set_page_config(page_title="Scanner de Velas", layout="centered")
st.title("PROJETO 10.000 VELAS")

aba1, aba2 = st.tabs(["INSERIR MANUAL", "INSERIR POR PRINT"])

with aba1:
    manual = st.text_area("Ex: 1.16x 10.71x 5x", height=100)

with aba2:
    arquivo = st.file_uploader("Suba seus prints aqui", type=['png','jpg','jpeg'])

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    novas = []
    if arquivo:
        with st.spinner("Decifrando grade..."):
            novas = extrair_velas_print(Image.open(arquivo))
    if manual:
        m_nums = re.findall(r"(\d+(?:\.\d+)?)", manual.replace(',', '.'))
        novas += [float(n) for n in m_nums]

    if novas:
        # Adiciona ao banco
        st.session_state.velas += novas
        # Mantém o limite de 10k
        if len(st.session_state.velas) > LIMITE:
            st.session_state.velas = st.session_state.velas[-LIMITE:]
        salvar()
        st.success(f"✅ {len(novas)} velas adicionadas com sucesso!")
        st.rerun()

st.divider()

# =========================
# BUSCA DE PADRÃO
# =========================
st.write("**BUSCA DE PADRÃO**")
col_b1, col_b2 = st.columns([0.8, 0.2])
with col_b1:
    seq = st.text_input("Digite a sequência...", label_visibility="collapsed", placeholder="Ex: 1.16 1.09")
with col_b2:
    btn_busca = st.button("🔎")

if btn_busca and seq:
    padrao = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)", seq.replace(',', '.'))]
    h = st.session_state.velas
    achado = False
    for i in range(len(h) - len(padrao)):
        if h[i:i+len(padrao)] == padrao:
            st.success(f"Padrão encontrado! Próxima vela: **{h[i+len(padrao)]:.2f}x**")
            achado = True
    if not achado: st.warning("Sequência não encontrada no histórico.")

st.divider()

# =========================
# HISTÓRICO (TABELA COLORIDA)
# =========================
st.write(f"**HISTÓRICO COMPLETO (Total: {len(st.session_state.velas)})**")
if st.session_state.velas:
    # Mostra do mais novo para o mais velho
    df_h = pd.DataFrame({"vela": reversed(st.session_state.velas)})
    st.dataframe(
        df_h.style.map(lambda v: "color:#FF00FF; font-weight:bold" if v >= 8 else "color:#00FF00" if v >= 2 else "color:white").format("{:.2f}x"),
        use_container_width=True, height=350
    )

st.divider()

# =========================
# ÚLTIMAS 20 E REDEFINIR
# =========================
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
