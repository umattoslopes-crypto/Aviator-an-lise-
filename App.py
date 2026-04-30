import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# --- CONFIGURAÇÕES DE PERSISTÊNCIA (GRAVA E NÃO APAGA) ---
DB_FILE = "historico_velas.csv"

if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.velas = pd.read_csv(DB_FILE)['velas'].tolist()
    else:
        st.session_state.velas = []

def salvar_dados():
    pd.DataFrame({'velas': st.session_state.velas}).to_csv(DB_FILE, index=False)

# Inicializa o leitor EasyOCR
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

reader = load_ocr()

st.title("🤖 Analisador Pro - Crash")

# --- ÁREA DE ENTRADA: PRINT E MANUAL ---
st.subheader("📥 Inserir Novas Velas")

tab1, tab2 = st.tabs(["📸 Carregar Print", "⌨️ Entrada Manual"])

with tab1:
    arquivo_img = st.file_uploader("Suba o print aqui", type=['png', 'jpg', 'jpeg'])
    texto_para_processar = ""
    if arquivo_img:
        img = Image.open(arquivo_img)
        st.image(img, width=200)
        if st.button("🔍 LER PRINT"):
            with st.spinner("Extraindo números..."):
                img_np = np.array(img)
                resultado = reader.readtext(img_np)
                texto_para_processar = " ".join([res[1] for res in resultado])

with tab2:
    input_manual = st.text_area("Cole as velas aqui (até 500):", placeholder="Ex: 1.50 2.10 9.34...")
    if input_manual:
        texto_para_processar = input_manual

# --- LÓGICA DE PROCESSAMENTO (DESDUPLICAÇÃO) ---
if st.button("📥 ADICIONAR AO HISTÓRICO (COM FILTRO)"):
    if texto_para_processar:
        # Extrai números e trata vírgula como ponto
        novas_extraidas = [float(v) for v in re.findall(r"\d+\.\d+|\d+", texto_para_processar.replace(',', '.'))]
        
        if novas_extraidas:
            # Sincronização: evita repetir a última vela do print anterior
            ultimas_banco = st.session_state.velas[-15:]
            ponto_corte = 0
            for i in range(len(novas_extraidas)):
                fatia = novas_extraidas[i:i+2] # Compara pares de velas
                if any(fatia == ultimas_banco[j:j+2] for j in range(len(ultimas_banco)-1)):
                    ponto_corte = i + 2
            
            velas_finais = novas_extraidas[ponto_corte:]

            if velas_finais:
                st.session_state.velas.extend(velas_finais)
                st.session_state.velas = st.session_state.velas[-10000:]
                salvar_dados()
                st.success(f"✅ +{len(velas_finais)} velas inéditas adicionadas!")
                st.rerun()
            else:
                st.warning("⚠️ Nenhuma vela nova detectada.")

st.divider()

# --- BUSCA MANUAL ---
st.subheader("🔍 Localizar Sequência")
seq_input = st.text_input("Sequência alvo (ex: 1.50, 2.00)")
if st.button("🔍 BUSCAR"):
    if seq_input:
        try:
            padrao = [float(x.strip()) for x in seq_input.replace(',', ' ').split()]
            n = len(padrao)
            posicoes = [i+1 for i in range(len(st.session_state.velas)-n+1) if st.session_state.velas[i:i+n] == padrao]
            if posicoes: st.success(f"Padrão encontrado nas posições: {posicoes}")
            else: st.error("Não encontrado.")
        except: st.error("Formato inválido.")

st.divider()

# --- HISTÓRICO COM "X" E CORES ---
total = len(st.session_state.velas)
st.header(f"📊 {total} / 10.000 Velas")

if total > 0:
    # Lista rápida colorida com X
    resumo_html = []
    for v in st.session_state.velas[-12:][::-1]:
        cor = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#FFFFFF"
        resumo_html.append(f"<b style='color: {cor}; font-size: 1.1em;'>{v:.2f}x</b>")
    st.markdown(" | ".join(resumo_html), unsafe_allow_html=True)

with st.expander("👁️ VER TODO O BANCO"):
    if total > 0:
        # DataFrame com X forçado e estilização rosa para >= 8x
        df_v = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
        
        def style_8x(val):
            return 'color: #FF00FF; font-weight: bold' if val >= 8.0 else 'color: white'
        
        # O .format("{:.2f}x") garante o x no final de todos os valores da tabela
        st.dataframe(df_v.style.applymap(style_8x).format("{:.2f}x"), use_container_width=True, height=400)

st.divider()

# --- RESET ---
if st.checkbox("Zerar histórico?"):
    if st.button("🗑️ APAGAR TUDO"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()
