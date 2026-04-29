import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import easyocr
import numpy as np
from PIL import Image

# 1. CONFIGURAÇÕES TÉCNICAS E CONEXÃO
st.set_page_config(page_title="Analisador Pro", layout="centered")

# COLE O LINK DA SUA PLANILHA GOOGLE (EDITOR) ABAIXO:
URL_DB = "COLE_O_LINK_DA_SUA_PLANILHA_AQUI"

conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        df = conn.read(spreadsheet=URL_DB)
        return [float(x) for x in df['velas'].tolist() if str(x).replace('.','').isdigit()]
    except: return []

if 'velas' not in st.session_state:
    st.session_state.velas = carregar_dados()

@st.cache_resource
def carregar_ocr():
    return easyocr.Reader(['en'], gpu=False)

# 2. INTERFACE VISUAL (LAYOUT ORIGINAL)
st.title("📈 Analisador Pro: Histórico & Padrões")

with st.expander("🚨 ADICIONAR NOVAS VELAS", expanded=True):
    metodo = st.tabs(["📝 Digitar Texto", "📷 Enviar Print"])
    
    with metodo[0]:
        entrada = st.text_area("Cole as velas aqui:", placeholder="Ex: 2.10, 1.50, 10.00...", label_visibility="collapsed")
        if st.button("GRAVAR NO HISTÓRICO", use_container_width=True):
            if entrada:
                novas = [float(v.strip()) for v in entrada.replace(",", " ").split() if v.strip()]
                st.session_state.velas.extend(novas)
                conn.update(spreadsheet=URL_DB, data=pd.DataFrame({"velas": st.session_state.velas}))
                st.success(f"✅ {len(novas)} velas salvas na nuvem!")
                st.rerun()

    with metodo[1]:
        arquivo_img = st.file_uploader("Suba o print das velas", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
        if arquivo_img:
            if st.button("LER IMAGEM E SALVAR", use_container_width=True):
                with st.spinner("🤖 IA lendo velas do print..."):
                    reader = carregar_ocr()
                    resultado = reader.readtext(np.array(Image.open(arquivo_img)))
                    velas_lidas = []
                    for (_, texto, _) in resultado:
                        try:
                            v = float(texto.replace('x','').replace(',','.').strip())
                            if 1.0 <= v <= 1000.0: velas_lidas.append(v)
                        except: continue
                    if velas_lidas:
                        st.session_state.velas.extend(velas_lidas)
                        conn.update(spreadsheet=URL_DB, data=pd.DataFrame({"velas": st.session_state.velas}))
                        st.success(f"🚀 {len(velas_lidas)} velas detectadas e salvas!")
                        st.rerun()
                    else: st.error("❌ Nenhuma vela encontrada na imagem.")

st.divider()

# 3. BUSCA DE PADRÃO (ALERTA 8X)
st.subheader("🔍 BUSCAR PADRÃO (ÚLTIMAS 10)")
if st.button("ANALISAR AGORA", use_container_width=True):
    if len(st.session_state.velas) > 1:
        ultima = st.session_state.velas[-1]
        encontrou = False
        for i in range(len(st.session_state.velas) - 1):
            if st.session_state.velas[i] == ultima and st.session_state.velas[i+1] >= 8.0:
                st.error(f"⚠️ PADRÃO ENCONTRADO! Após {ultima}x, o histórico mostra {st.session_state.velas[i+1]}x!")
                encontrou = True
        if not encontrou: st.info(f"Nenhum padrão de 8x após {ultima}x no histórico atual.")
    else: st.warning("Adicione mais velas para analisar.")

st.divider()

# 4. CONTADOR (CONFORME SEUS PRINTS)
st.subheader("📊 Contador")
st.write("Velas Acumuladas")
total = len(st.session_state.velas)
st.header(f"{total} / 10.000")
if total < 10000:
    st.info(f"Faltam {10000 - total} velas para completar o banco.")

st.divider()

# 5. RESET E SEGURANÇA
if st.button("🗑️ RESETAR BANCO DE DADOS", type="secondary"):
    if st.checkbox("Confirmo que desejo apagar TUDO do Google Sheets"):
        conn.update(spreadsheet=URL_DB, data=pd.DataFrame(columns=["velas"]))
        st.session_state.velas = []
        st.rerun()

