import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import pytesseract

# --- CONFIGURAÇÕES DE PERSISTÊNCIA ---
DB_FILE = "historico_velas.csv"

if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.velas = pd.read_csv(DB_FILE)['velas'].tolist()
    else:
        st.session_state.velas = []

def salvar_dados():
    pd.DataFrame({'velas': st.session_state.velas}).to_csv(DB_FILE, index=False)

st.title("🤖 Analisador de Velas Pro")

# --- LEITOR DE PRINTS ---
st.subheader("📸 Carregar Print das Velas")
arquivo_img = st.file_uploader("Arraste o print aqui", type=['png', 'jpg', 'jpeg'])

if arquivo_img:
    img = Image.open(arquivo_img)
    st.image(img, caption="Print carregado", width=250)
    
    with st.spinner("Lendo números do print..."):
        # Extração de texto via OCR
        texto_ocr = pytesseract.image_to_string(img, config=r'--oem 3 --psm 6')
        # Limpeza básica: troca vírgula por ponto e extrai números
        novas_extraidas = [float(v) for v in re.findall(r"\d+\.\d+|\d+", texto_ocr.replace(',', '.'))]

        if st.button("📥 ADICIONAR NOVAS VELAS (SEM REPETIR)"):
            if novas_extraidas:
                # LÓGICA DE SINCRONIZAÇÃO (NÃO DUPLICAR)
                # Compara as últimas velas do banco com as novas
                ultimas_banco = st.session_state.velas[-10:]
                ponto_corte = 0
                
                # Procura se o início do print novo já existe no fim do banco
                for i in range(len(novas_extraidas)):
                    fatia = novas_extraidas[i:i+3] # Compara sequências de 3
                    if any(fatia == ultimas_banco[j:j+3] for j in range(len(ultimas_banco)-2)):
                        ponto_corte = i + 3 # Avança o corte para depois da repetição
                
                velas_reais = novas_extraidas[ponto_corte:]

                if velas_reais:
                    st.session_state.velas.extend(velas_reais)
                    st.session_state.velas = st.session_state.velas[-10000:]
                    salvar_dados()
                    st.success(f"Adicionadas {len(velas_reais)} velas inéditas!")
                    st.rerun()
                else:
                    st.warning("Todas as velas deste print já estão registradas.")

st.divider()

# --- BUSCA MANUAL ---
st.subheader("🔍 Localizar Sequência Manual")
seq_input = st.text_input("Digite a sequência (ex: 1.50, 2.00)")
if st.button("🔍 BUSCAR"):
    if seq_input:
        padrao = [float(x.strip()) for x in seq_input.replace(',', ' ').split()]
        n = len(padrao)
        posicoes = [i+1 for i in range(len(st.session_state.velas)-n+1) if st.session_state.velas[i:i+n] == padrao]
        if posicoes: st.success(f"Padrão encontrado nas posições: {posicoes}")
        else: st.error("Sequência não encontrada.")

st.divider()

# --- VISUALIZAÇÃO ---
total = len(st.session_state.velas)
st.header(f"📊 Histórico: {total} / 10.000")

if total > 0:
    # Lista rápida colorida
    resumo_html = []
    for v in st.session_state.velas[-12:][::-1]:
        cor = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#BBBBBB"
        resumo_html.append(f"<b style='color: {cor}; font-size: 1.1em;'>{v:.2f}x</b>")
    st.markdown(" | ".join(resumo_html), unsafe_allow_html=True)

with st.expander("👁️ VER TODO O BANCO"):
    if total > 0:
        df_v = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
        
        # Estilização da Tabela (Rosa para >= 8x)
        def style_8x(val):
            return 'color: #FF00FF; font-weight: bold' if val >= 8.0 else 'color: white'
        
        st.dataframe(df_v.style.applymap(style_8x).format("{:.2f}x"), use_container_width=True, height=400)

st.divider()

# --- RESET ---
if st.checkbox("Zerar histórico permanentemente?"):
    if st.button("🗑️ APAGAR TUDO"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()
