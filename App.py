import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import easyocr
import numpy as np
from PIL import Image

st.set_page_config(page_title="Analisador Pro", page_icon="📈")

# --- CONEXÃO COM GOOGLE SHEETS ---
URL_BANCO_DADOS = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"

conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_do_banco():
    try:
        df = conn.read(spreadsheet=URL_BANCO_DADOS)
        return [float(x) for x in df['velas'].tolist() if str(x).replace('.','').isdigit()]
    except:
        return []

if 'velas' not in st.session_state:
    st.session_state.velas = carregar_do_banco()

@st.cache_resource
def carregar_leitor():
    return easyocr.Reader(['en'])

def ler_velas_da_imagem(imagem):
    reader = carregar_leitor()
    img_array = np.array(Image.open(imagem))
    resultado = reader.readtext(img_array)
    detectadas = []
    for (bbox, texto, prob) in resultado:
        texto_limpo = texto.replace('x', '').replace(',', '.').strip()
        try:
            valor = float(texto_limpo)
            if 1.0 <= valor <= 1000.0: detectadas.append(valor)
        except: continue
    return detectadas

st.title("📈 Analisador Pro: Histórico & Padrões")

with st.expander("🚨 ADICIONAR NOVAS VELAS", expanded=True):
    metodo = st.radio("Como deseja adicionar?", ["Texto/Digitar", "Ler por Foto (Print)"], horizontal=True)
    
    if metodo == "Texto/Digitar":
        entrada = st.text_area("Cole até 500 velas aqui:", placeholder="Ex: 2.76, 1.05...")
        if st.button("GRAVAR NO HISTÓRICO"):
            if entrada:
                novas = [float(v.strip()) for v in entrada.replace(",", " ").split() if v.strip()]
                st.session_state.velas.extend(novas)
                conn.update(spreadsheet=URL_BANCO_DADOS, data=pd.DataFrame({"velas": st.session_state.velas}))
                st.success("Salvo na nuvem!")
                st.rerun()
    else:
        arquivo_img = st.file_uploader("Envie o print das velas", type=['png', 'jpg', 'jpeg'])
        if arquivo_img:
            if st.button("LER FOTO E SALVAR"):
                with st.spinner("Lendo números..."):
                    velas_lidas = ler_velas_da_imagem(arquivo_img)
                    if velas_lidas:
                        st.session_state.velas.extend(velas_lidas)
                        conn.update(spreadsheet=URL_BANCO_DADOS, data=pd.DataFrame({"velas": st.session_state.velas}))
                        st.success(f"Lidas e salvas {len(velas_lidas)} velas!")
                        st.rerun()

st.divider()
st.subheader("🔍 BUSCAR PADRÃO (ÚLTIMAS 10)")
busca_input = st.text_input("Velas para análise:", placeholder="Ex: 1.50, 2.00...")
if st.button("BUSCAR"):
    if len(st.session_state.velas) > 10:
        st.info("Analisando histórico...")
    else:
        st.warning("Histórico insuficiente.")

st.divider()
st.subheader("📊 Contador")
st.write("Velas Acumuladas")
total = len(st.session_state.velas)
st.header(f"{total} / 10.000")
if total < 10000:
    st.info(f"Faltam {10000 - total} velas.")

st.divider()
if st.button("🗑️ RESETAR BANCO DE DADOS"):
    if st.checkbox("Confirmar reset total?"):
        conn.update(spreadsheet=URL_BANCO_DADOS, data=pd.DataFrame(columns=["velas"]))
        st.session_state.velas = []
        st.rerun()
