import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import easyocr
import numpy as np
from PIL import Image

# Configuração Visual
st.set_page_config(page_title="Analisador Pro", layout="centered")

# --- CONEXÃO IMORTAL (GOOGLE SHEETS) ---
# Cole o link da sua planilha abaixo (deve estar como Editor)
URL_DB = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"

conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        df = conn.read(spreadsheet=URL_DB)
        return [float(x) for x in df['velas'].tolist() if str(x).replace('.','').isdigit()]
    except: return []

if 'velas' not in st.session_state:
    st.session_state.velas = carregar_dados()

@st.cache_resource
def get_reader():
    return easyocr.Reader(['en'])

# --- INTERFACE ---
st.title("📈 Analisador Pro: Histórico & Padrões")

with st.expander("🚨 ADICIONAR NOVAS VELAS", expanded=True):
    metodo = st.tabs(["📝 Texto", "📷 Vários Prints"])
    
    with metodo[0]:
        entrada = st.text_area("Cole as velas aqui:", placeholder="Ex: 2.10, 1.50...")
        if st.button("GRAVAR TEXTO", use_container_width=True):
            if entrada:
                novas = [float(v.strip()) for v in entrada.replace(",", " ").split() if v.strip()]
                st.session_state.velas.extend(novas)
                conn.update(spreadsheet=URL_DB, data=pd.DataFrame({"velas": st.session_state.velas}))
                st.success("✅ Salvo na Nuvem!")
                st.rerun()

    with metodo[1]:
        fotos = st.file_uploader("Selecione um ou mais prints:", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if fotos and st.button("LER TODAS AS FOTOS E SALVAR", use_container_width=True):
            with st.spinner("🤖 IA lendo todos os prints..."):
                reader = get_reader()
                velas_totais_lidas = []
                for foto in fotos:
                    res = reader.readtext(np.array(Image.open(foto)))
                    for (_, t, _) in res:
                        val = t.replace('x','').replace(',','.').strip()
                        if val.replace('.','').isdigit():
                            velas_totais_lidas.append(float(val))
                
                if velas_totais_lidas:
                    st.session_state.velas.extend(velas_totais_lidas)
                    conn.update(spreadsheet=URL_DB, data=pd.DataFrame({"velas": st.session_state.velas}))
                    st.success(f"🚀 {len(velas_totais_lidas)} velas detectadas em {len(fotos)} fotos!")
                    st.rerun()

st.divider()

# --- BUSCA DE PADRÃO (15 SUBSEQUENTES) ---
st.subheader("🔍 BUSCAR PADRÃO")
if st.button("ANALISAR SEQUÊNCIA (15 VELAS)", use_container_width=True):
    if len(st.session_state.velas) > 1:
        ultima = st.session_state.velas[-1]
        encontrou = False
        st.write(f"Buscando histórico para: **{ultima:.2f}x**")
        
        for i in range(len(st.session_state.velas) - 1):
            if st.session_state.velas[i] == ultima:
                sequencia = st.session_state.velas[i+1 : i+16]
                if any(v >= 8.0 for v in sequencia):
                    st.error(f"⚠️ **PADRÃO 8X ENCONTRADO!**")
                    cols = st.columns(5)
                    for idx, v in enumerate(sequencia):
                        txt = f"🔥 **{v:.2f}x**" if v >= 8.0 else f"{v:.2f}x"
                        cols[idx % 5].write(f"{idx+1}º: {txt}")
                    encontrou = True
                    st.divider()
        if not encontrou: st.info(f"Sem 8x nas próximas 15 velas após {ultima}x.")
    else: st.warning("Adicione velas para analisar.")

st.divider()

# --- CONTADOR E VISUALIZAÇÃO ---
st.subheader("📊 Contador")
total = len(st.session_state.velas)
st.header(f"{total} / 10.000")

st.subheader("📋 Últimas Velas Salvas")
if total > 0:
    ultimas_20 = st.session_state.velas[-20:][::-1]
    exibicao = [f"🔥 **{v:.2f}x**" if v >= 8.0 else f"{v:.2f}x" for v in ultimas_20]
    st.write(" | ".join(exibicao))

if st.button("🗑️ RESETAR BANCO DE DADOS"):
    if st.checkbox("Confirmar apagar tudo da Nuvem?"):
        conn.update(spreadsheet=URL_DB, data=pd.DataFrame(columns=["velas"]))
        st.rerun()
