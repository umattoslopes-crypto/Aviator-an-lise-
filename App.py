import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# --- PERSISTÊNCIA DE DADOS ---
DB_FILE = "historico_velas.csv"

if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.velas = pd.read_csv(DB_FILE)['velas'].tolist()
    else:
        st.session_state.velas = []

def salvar_dados():
    pd.DataFrame({'velas': st.session_state.velas}).to_csv(DB_FILE, index=False)

# Inicializa o leitor EasyOCR (apenas uma vez para não travar)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

reader = load_ocr()

st.title("🤖 Analisador de Crash Pro")

# --- LEITOR DE PRINTS ---
st.subheader("📸 Carregar Print")
arquivo_img = st.file_uploader("Suba o print das velas aqui", type=['png', 'jpg', 'jpeg'])

if arquivo_img:
    img = Image.open(arquivo_img)
    st.image(img, width=250)
    
    if st.button("📥 PROCESSAR PRINT E ADICIONAR"):
        with st.spinner("Lendo print com EasyOCR..."):
            # Converte imagem para formato que o EasyOCR entende
            img_np = np.array(img)
            resultado = reader.readtext(img_np)
            
            # Extrai apenas os números
            texto_completo = " ".join([res[1] for res in resultado])
            novas_extraidas = [float(v) for v in re.findall(r"\d+\.\d+|\d+", texto_completo.replace(',', '.'))]

            if novas_extraidas:
                # LÓGICA DE NÃO REPETIÇÃO (Sincronização)
                # Compara o novo print com as últimas 15 velas do banco
                ultimas_banco = st.session_state.velas[-15:]
                ponto_corte = 0
                
                # Procura onde a sequência nova começa a ser inédita
                for i in range(len(novas_extraidas)):
                    fatia = novas_extraidas[i:i+3] # Compara trios
                    if any(fatia == ultimas_banco[j:j+3] for j in range(len(ultimas_banco)-2)):
                        ponto_corte = i + 3
                
                velas_reais = novas_extraidas[ponto_corte:]

                if velas_reais:
                    st.session_state.velas.extend(velas_reais)
                    st.session_state.velas = st.session_state.velas[-10000:]
                    salvar_dados()
                    st.success(f"✅ Adicionadas {len(velas_reais)} velas inéditas!")
                    st.rerun()
                else:
                    st.warning("⚠️ Todas as velas desse print já estão no banco.")

st.divider()

# --- BUSCA MANUAL ---
st.subheader("🔍 Localizar Padrão Manual")
seq_input = st.text_input("Sequência alvo (ex: 1.50, 2.00)", placeholder="Separe por vírgula")
if st.button("🔍 BUSCAR NO HISTÓRICO"):
    if seq_input:
        try:
            padrao = [float(x.strip()) for x in seq_input.replace(',', ' ').split()]
            n = len(padrao)
            posicoes = [i+1 for i in range(len(st.session_state.velas)-n+1) if st.session_state.velas[i:i+n] == padrao]
            if posicoes: st.success(f"Padrão encontrado nas posições: {posicoes}")
            else: st.error("Sequência não encontrada.")
        except: st.error("Formato de números inválido.")

st.divider()

# --- HISTÓRICO VISUAL ---
total = len(st.session_state.velas)
st.header(f"📊 Total: {total} / 10.000")

if total > 0:
    resumo_html = []
    for v in st.session_state.velas[-12:][::-1]:
        # Rosa Choque para >= 8x
        cor = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#BBBBBB"
        resumo_html.append(f"<b style='color: {cor}; font-size: 1.1em;'>{v:.2f}x</b>")
    st.markdown(" | ".join(resumo_html), unsafe_allow_html=True)

with st.expander("👁️ VER TODO O BANCO"):
    if total > 0:
        df_v = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
        
        def style_8x(val):
            return 'color: #FF00FF; font-weight: bold' if val >= 8.0 else 'color: white'
        
        st.dataframe(df_v.style.applymap(style_8x).format("{:.2f}x"), use_container_width=True, height=400)

st.divider()

# --- RESET ---
if st.checkbox("Confirmar limpeza total?"):
    if st.button("🗑️ ZERAR HISTÓRICO AGORA"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()
