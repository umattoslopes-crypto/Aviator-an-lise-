import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# --- 1. PERSISTÊNCIA DOS DADOS ---
DB_FILE = "banco_velas_projeto.csv"

if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            st.session_state.velas = pd.read_csv(DB_FILE)['velas'].tolist()
        except: st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'velas': st.session_state.velas}).to_csv(DB_FILE, index=False)

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

# --- LAYOUT FIEL AO DESENHO ---
st.markdown("<h2 style='text-align: center;'>ATE 500 VELAS</h2>", unsafe_allow_html=True)

aba_manual, aba_print = st.tabs(["📥 INSERIR MANUAL", "📸 INSERIR ATRAVÉS PRINT"])

with aba_manual:
    manual_txt = st.text_area("Exemplo: 1.05 4.10 5.00", placeholder="Digite as velas aqui...", height=100)

with aba_print:
    arquivo = st.file_uploader("Anexe o print aqui", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    texto_bruto = ""
    if arquivo:
        with st.spinner("Lendo print..."):
            img = Image.open(arquivo)
            res = reader.readtext(np.array(img), detail=0)
            texto_bruto = " ".join(res)
    if manual_txt:
        texto_bruto += " " + manual_txt

    if texto_bruto:
        # Extração TOTAL: Pega todos os números (1.01, 1.10, etc.)
        # Apenas ignora IDs gigantes (>1000) e os horários do topo (22.18, 0.08, etc)
        nums = [float(v) for v in re.findall(r"(\d+[\.\d]*)", texto_bruto.replace(',', '.'))]
        novas = []
        for v in nums:
            if v > 1000.0 or v in [22.18, 0.08, 0.09, 0.10, 0.14]:
                continue
            novas.append(v)
        
        if novas:
            # Sincronização (Anti-duplicação)
            ultimas = st.session_state.velas[-15:]
            ponto = 0
            for i in range(len(novas)):
                if novas[i:i+2] in [ultimas[j:j+2] for j in range(len(ultimas)-1)]:
                    ponto = i + 2
            
            final = novas[ponto:]
            if final:
                st.session_state.velas.extend(final)
                salvar()
                st.success(f"{len(final)} velas adicionadas!")
                st.rerun()

st.divider()

# --- 2. BUSCA DE PADRÃO ---
st.subheader("🔍 BUSCA DE PADRAO")
col_in, col_bt = st.columns([0.85, 0.15])
with col_in:
    seq_alvo = st.text_input("Insira o padrão de 10 velas:", placeholder="Ex: 1.05 2.00 1.10...")
with col_bt:
    buscar = st.button("🔎")

if buscar and seq_alvo:
    try:
        # Busca sem vírgulas atrapalhando
        padrao = [float(x.strip()) for x in seq_alvo.replace(',', ' ').split()]
        n = len(padrao)
        hist = st.session_state.velas
        achou = False
        for i in range(len(hist) - n):
            if hist[i : i + n] == padrao:
                achou = True
                st.success(f"✅ PADRÃO ENCONTRADO! (Posição {i+1})")
                proximas = hist[i + n : i + n + 15]
                if proximas:
                    st.warning("⚠️ ALERTA: PRÓXIMAS 15 VELAS")
                    fmt = [f"<b style='color:{'#FF00FF' if v >= 8.0 else '#00FF00' if v >= 2.0 else '#FFFFFF'};'>{v:.2f}x</b>" for v in proximas]
                    st.markdown(" ".join(fmt), unsafe_allow_html=True) # Sem vírgulas na antecipação
        if not achou: st.error("Padrão não localizado.")
    except: st.error("Formato inválido.")

st.divider()

# --- 3. HISTÓRICO DE VELAS (FIEL) ---
st.subheader("📋 HISTORICO DE VELAS")
if st.session_state.velas:
    df = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
    def colorir(val):
        return 'color: #FF00FF; font-weight: bold' if val >= 8.0 else 'color: white'
    st.dataframe(df.style.map(colorir).format("{:.2f}x"), use_container_width=True, height=400)

st.divider()

# --- 4. ULTIMA 20 VELA ADICIONADA (SEM VÍRGULAS NO MEIO) ---
st.subheader("📉 ULTIMAS 20 VELAS ADICIONADAS")
if st.session_state.velas:
    ultimas_20 = st.session_state.velas[-20:][::-1]
    resumo = []
    for v in ultimas_20:
        cor = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#FFFFFF"
        resumo.append(f"<b style='color:{cor};'>{v:.2f}x</b>")
    
    # Exibe apenas com espaços, sem vírgulas para não confundir a leitura
    st.markdown(" &nbsp; ".join(resumo), unsafe_allow_html=True)

# Reset discreto
if st.sidebar.button("🗑️ LIMPAR BANCO"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.session_state.velas = []
    st.rerun()
