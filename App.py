import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# --- 1. PERSISTÊNCIA TOTAL (GRAVA E NÃO APAGA) ---
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

# --- LAYOUT FIEL AO SEU DESENHO ---
st.markdown("<h2 style='text-align: center;'>ATE 500 VELAS</h2>", unsafe_allow_html=True)

# Moldura de entrada com as abas conforme o desenho
aba_manual, aba_print = st.tabs(["INSERIR MANUAL", "INSERIR ATRAVÉS PRINT"])

with aba_manual:
    manual_txt = st.text_area("Digite ou cole as velas:", placeholder="Ex: 1.25x 4.10x 9.34x", height=100)

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
        # Extração SEM FILTROS: Pega todos os números que encontrar
        novas = [float(v) for v in re.findall(r"(\d+[\.\d]*)", texto_bruto.replace(',', '.'))]
        
        if novas:
            # Sincronização (Anti-duplicação básica)
            ultimas_banco = st.session_state.velas[-10:]
            ponto_corte = 0
            for i in range(len(novas)):
                if novas[i:i+2] in [ultimas_banco[j:j+2] for j in range(len(ultimas_banco)-1)]:
                    ponto_corte = i + 2
            
            velas_finais = novas[ponto_corte:]
            if velas_finais:
                st.session_state.velas.extend(velas_finais)
                salvar()
                st.success(f"Adicionadas {len(velas_finais)} velas.")
                st.rerun()

st.divider()

# --- SEÇÃO: BUSCA DE PADRÃO ---
st.markdown("### BUSCA DE PADRAO")
col_input, col_botao = st.columns([0.85, 0.15])

with col_input:
    seq_alvo = st.text_input("Insira o padrão de 10 velas", placeholder="Ex: 1.25, 2.00, 1.10...", label_visibility="collapsed")

with col_botao:
    buscar = st.button("🔎") # Botão redondo/ícone lateral

if buscar and seq_alvo:
    try:
        padrao = [float(x.strip()) for x in seq_alvo.replace(',', ' ').split()]
        n = len(padrao)
        hist = st.session_state.velas
        achou = False
        
        for i in range(len(hist) - n):
            if hist[i : i + n] == padrao:
                achou = True
                st.success(f"✅ PADRÃO ENCONTRADO! (Posição {i+1})")
                
                # ALERTA DE ANTECIPAÇÃO: MOSTRA AS 15 VELAS SEGUINTES
                proximas = hist[i + n : i + n + 15]
                if proximas:
                    st.warning("⚠️ ALERTA: PRÓXIMAS 15 VELAS")
                    fmt = [f"<b style='color:{'#FF00FF' if v >= 8.0 else '#00FF00' if v >= 2.0 else '#FFFFFF'}; font-size:1.1em;'>{v:.2f}x</b>" for v in proximas]
                    st.markdown(" , ".join(fmt), unsafe_allow_html=True)
        if not achou:
            st.error("Padrão não localizado.")
    except:
        st.error("Formato inválido.")

st.divider()

# --- SEÇÃO: HISTÓRICO DE VELAS (BANCO COMPLETO) ---
st.markdown("### HISTORICO DE VELAS")
if st.session_state.velas:
    df = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
    
    def colorir_8x(val):
        # Apenas velas acima de 8x ficam em ROSA CHOQUE
        return 'color: #FF00FF; font-weight: bold' if val >= 8.0 else 'color: white'

    st.dataframe(
        df.style.map(colorir_8x).format("{:.2f}x"), 
        use_container_width=True, 
        height=400
    )

st.divider()

# --- SEÇÃO: ULTIMAS 20 VELAS ADICIONADAS ---
st.markdown("### ULTIMA 20 VELA ADICIONADA")
if st.session_state.velas:
    ultimas_20 = st.session_state.velas[-20:][::-1]
    resumo_html = []
    for v in ultimas_20:
        # Cores: Rosa (8x), Verde (2x), Branco (resto)
        cor = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#FFFFFF"
        resumo_html.append(f"<span style='color:{cor}; font-weight:bold; font-size:1.1em;'>{v:.2f}x</span>")
    
    st.markdown(" , ".join(resumo_html), unsafe_allow_html=True)

# Opção de apagar no menu lateral
if st.sidebar.checkbox("Zerar Banco"):
    if st.sidebar.button("CONFIRMAR RESET"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()
