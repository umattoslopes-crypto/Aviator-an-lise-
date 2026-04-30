import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import pytesseract  # Requer: pip install pytesseract

# --- CONFIGURAÇÕES DE PERSISTÊNCIA ---
DB_FILE = "historico_velas.csv"

if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.velas = pd.read_csv(DB_FILE)['velas'].tolist()
    else:
        st.session_state.velas = []

def salvar_dados():
    pd.DataFrame({'velas': st.session_state.velas}).to_csv(DB_FILE, index=False)

st.title("🤖 Analisador Pro - Leitor de Prints")

# --- LEITOR DE PRINTS (OCR) ---
st.subheader("📸 Carregar Print das Velas")
arquivo_img = st.file_uploader("Arraste o print aqui", type=['png', 'jpg', 'jpeg'])

texto_extraido = ""
if arquivo_img is not None:
    img = Image.open(arquivo_img)
    st.image(img, caption="Print carregado", width=300)
    
    # Processa o OCR
    with st.spinner("Lendo números do print..."):
        # Configuração para focar em números
        config = r'--oem 3 --psm 6' 
        texto_extraido = pytesseract.image_to_string(img, config=config)
        st.text_area("Texto identificado (ajuste se necessário):", texto_extraido, key="ocr_text")

# --- PROCESSAMENTO E DESDUPLICAÇÃO ---
if st.button("📥 VALIDAR E ADICIONAR AO HISTÓRICO"):
    # Usa o texto do OCR ou o que foi digitado manualmente
    fonte_dados = st.session_state.ocr_text if "ocr_text" in st.session_state else ""
    
    if fonte_dados:
        # Extrai números (ex: 9.34)
        novas_extraidas = [float(v) for v in re.findall(r"\d+\.\d+|\d+", fonte_dados.replace(',', '.'))]
        
        if novas_extraidas:
            # LÓGICA DE NÃO REPETIR (Sincronização)
            ultimas_banco = st.session_state.velas[-15:] # Compara com as últimas 15
            ponto_corte = 0
            
            # Procura a última sequência conhecida para saber onde começar a colar as novas
            for i in range(len(novas_extraidas)):
                fatia = novas_extraidas[i:i+3] # Compara trios para evitar erro
                for j in range(len(ultimas_banco)-2):
                    if fatia == ultimas_banco[j:j+3]:
                        ponto_corte = i + (len(ultimas_banco) - j)

            velas_inéditas = novas_extraidas[ponto_corte:]

            if velas_inéditas:
                st.session_state.velas.extend(velas_inéditas)
                st.session_state.velas = st.session_state.velas[-10000:]
                salvar_dados()
                st.success(f"✅ +{len(velas_inéditas)} velas novas adicionadas!")
                st.rerun()
            else:
                st.warning("⚠️ Nenhuma vela nova detectada (todas já existem no banco).")

st.divider()

# --- BUSCA MANUAL ---
st.subheader("🔍 Localizar Sequência")
seq_input = st.text_input("Digite a sequência (ex: 1.50, 2.00)")
if st.button("🔍 BUSCAR"):
    if seq_input:
        padrao = [float(x.strip()) for x in seq_input.replace(',', ' ').split()]
        n = len(padrao)
        posicoes = [i+1 for i in range(len(st.session_state.velas)-n+1) if st.session_state.velas[i:i+n] == padrao]
        if posicoes: st.success(f"Encontrado em: {posicoes}")
        else: st.error("Não encontrado.")

st.divider()

# --- VISUALIZAÇÃO COLORIDA (8x EM ROSA) ---
total = len(st.session_state.velas)
st.header(f"📊 {total} Velas no Banco")

if total > 0:
    resumo = []
    for v in st.session_state.velas[-10:][::-1]:
        cor = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#FFFFFF"
        resumo.append(f"<b style='color: {cor}; font-size: 1.2em;'>{v:.2f}x</b>")
    st.markdown(" | ".join(resumo), unsafe_allow_html=True)

with st.expander("👁️ VER TODO O BANCO"):
    if total > 0:
        df_v = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
        def style_8x(val):
            return 'color: #FF00FF; font-weight: bold' if val >= 8.0 else 'color: white'
        st.dataframe(df_v.style.applymap(style_8x).format("{:.2f}x"), use_container_width=True)

st.divider()

# --- RESET ---
if st.checkbox("Zerar Banco de Dados?"):
    if st.button("🗑️ APAGAR TUDO"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()

