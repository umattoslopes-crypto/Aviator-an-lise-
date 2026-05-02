import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# --- 1. PERSISTÊNCIA DOS DADOS ---
DB_FILE = "banco_velas_final.csv"

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

# --- LAYOUT FIEL AO DESENHO (ORDEM DO PAPEL) ---

st.markdown("<h2 style='text-align: center;'>ATE 500 VELAS</h2>", unsafe_allow_html=True)

# MOLDURA DE ENTRADA
aba_manual, aba_print = st.tabs(["📥 INSERIR MANUAL", "📸 INSERIR ATRAVÉS PRINT"])

with aba_manual:
    manual_txt = st.text_area("Exemplo: 1.25x 4.10x 5x", placeholder="Digite as velas aqui...", height=100)

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
        # Extração Blindada: Só pega números e ignora letras/sujeira
        brutos = re.findall(r"\d+\.\d+|\d+", texto_bruto.replace(',', '.'))
        novas = []
        for v in brutos:
            try:
                val = float(v)
                # Filtro Anti-Lixo: Ignora IDs e horários do celular (0.22, 22.18, etc)
                if val > 1000.0 or val in [22.18, 0.22, 0.08, 0.10, 0.14]:
                    continue
                novas.append(val)
            except: continue
        
        if novas:
            # Sincronização (Não duplicar velas entre prints)
            ultimas = st.session_state.velas[-15:]
            ponto = 0
            for i in range(len(novas)):
                if novas[i:i+2] in [ultimas[j:j+2] for j in range(len(ultimas)-1)]:
                    ponto = i + 2
            
            final = novas[ponto:]
            if final:
                st.session_state.velas.extend(final)
                salvar()
                st.success(f"✅ {len(final)} velas adicionadas!")
                st.rerun()

st.divider()

# --- 2. BUSCA DE PADRÃO ---
st.subheader("🔍 BUSCA DE PADRAO")
col_in, col_bt = st.columns([0.85, 0.15])
with col_in:
    seq_alvo = st.text_input("Padrao de 10 velas:", placeholder="Ex: 1.25 2.00 1.10...", label_visibility="collapsed")
with col_bt:
    buscar = st.button("🔎")

if buscar and seq_alvo:
    try:
        padrao = [float(x.strip()) for x in seq_alvo.replace(',', ' ').split() if x.strip()]
        hist = st.session_state.velas
        achou = False
        for i in range(len(hist) - len(padrao)):
            if hist[i : i + len(padrao)] == padrao:
                achou = True
                st.success(f"🎯 PADRÃO ENCONTRADO! (Posição {i+1})")
                # Alerta das 15 seguintes
                proximas = hist[i + len(padrao) : i + len(padrao) + 15]
                if proximas:
                    st.warning("⚠️ ALERTA: PRÓXIMAS 15 VELAS")
                    fmt = [f"<b style='color:{'#FF00FF' if v >= 8.0 else '#00FF00' if v >= 2.0 else '#FFFFFF'};'>{v:.2f}x</b>" for v in proximas]
                    st.markdown(" &nbsp; ".join(fmt), unsafe_allow_html=True)
        if not achou: st.error("Não encontrado.")
    except: st.error("Erro no formato das velas.")

st.divider()

# --- 3. HISTÓRICO DE VELAS ---
st.subheader("📋 HISTORICO DE VELAS")
if st.session_state.velas:
    df = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
    st.dataframe(
        df.style.map(lambda x: 'color: #FF00FF; font-weight: bold' if x >= 8.0 else 'color: white').format("{:.2f}x"),
        use_container_width=True, height=350
    )

st.divider()

# --- 4. ÚLTIMA 20 VELA ADICIONADA ---
st.subheader("📉 ULTIMA 20 VELA ADICIONADA")
if st.session_state.velas:
    ultimas_20 = st.session_state.velas[-20:][::-1]
    resumo = [f"<b style='color:{'#FF00FF' if v >= 8.0 else '#00FF00' if v >= 2.0 else '#FFFFFF'};'>{v:.2f}x</b>" for v in ultimas_20]
    st.markdown(" &nbsp; ".join(resumo), unsafe_allow_html=True)

st.divider()

# --- 5. SEÇÃO DE RESET (CONFORME O PAPEL) ---
st.subheader("⚙️ RESETAR")
col_r1, col_r2 = st.columns(2)

with col_r1:
    if st.button("🗑️ RESETAR ÚLTIMA 20 VELAS", use_container_width=True):
        if len(st.session_state.velas) >= 20:
            st.session_state.velas = st.session_state.velas[:-20]
            salvar()
            st.warning("Últimas 20 velas removidas.")
            st.rerun()

with col_r2:
    confirmar = st.checkbox("Confirmar: APAGAR TUDO")
    if st.button("🔥 RESETAR TUDO", use_container_width=True):
        if confirmar:
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.velas = []
            st.success("Banco de dados zerado.")
            st.rerun()
