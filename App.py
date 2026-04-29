import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image
import os

st.set_page_config(page_title="Analisador Pro", layout="centered")

DB_FILE = "banco_de_velas.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            return [float(v) for v in df['velas'].tolist()]
        except: return []
    return []

def salvar_dados(lista):
    pd.DataFrame({"velas": lista}).to_csv(DB_FILE, index=False)

if 'velas' not in st.session_state:
    st.session_state.velas = carregar_dados()

@st.cache_resource
def get_reader():
    return easyocr.Reader(['en'])

st.title("📈 Analisador Pro: Fidelidade Total")

# --- ADICIONAR DADOS ---
with st.expander("🚨 ADICIONAR NOVAS VELAS", expanded=True):
    aba1, aba2, aba3 = st.tabs(["📝 Texto", "📷 Prints (Anti-Cópia)", "📂 Backup"])
    
    with aba1:
        entrada = st.text_area("Cole as velas:")
        if st.button("GRAVAR TEXTO", use_container_width=True):
            if entrada:
                novas = [float(v.strip()) for v in entrada.replace(",", " ").split() if v.strip()]
                st.session_state.velas.extend(novas)
                salvar_dados(st.session_state.velas)
                st.rerun()

    with aba2:
        fotos = st.file_uploader("Suba os prints:", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if fotos and st.button("LER E SINCRONIZAR", use_container_width=True):
            reader = get_reader()
            for foto in fotos:
                res = reader.readtext(np.array(Image.open(foto)))
                lidas = []
                for (_, t, _) in res:
                    val = t.replace('x','').replace(',','.').strip()
                    if val.replace('.','').replace('-','').isdigit():
                        try: lidas.append(float(val))
                        except: continue
                
                if lidas:
                    if not st.session_state.velas:
                        st.session_state.velas.extend(lidas)
                    else:
                        ultimas_banco = st.session_state.velas[-15:]
                        ponto_corte = 0
                        for i in range(len(lidas)):
                            if lidas[i] in ultimas_banco:
                                ponto_corte = i + 1
                            else:
                                break
                        novas_reais = lidas[ponto_corte:]
                        if novas_reais:
                            st.session_state.velas.extend(novas_reais)
            
            salvar_dados(st.session_state.velas)
            st.rerun()

st.divider()

# --- BUSCA DE PADRÃO (10 PADRÃO / 15 SEGUINTES) ---
st.subheader("🔍 BUSCAR PADRÃO (10 VELAS)")
if st.button("ANALISAR AGORA", use_container_width=True):
    if len(st.session_state.velas) >= 25:
        padrao_atual = st.session_state.velas[-10:]
        encontrou = False
        st.write(f"Buscando: **{' | '.join([f'{v:.2f}x' for v in padrao_atual])}**")
        
        for i in range(len(st.session_state.velas) - 25):
            if st.session_state.velas[i:i+10] == padrao_atual:
                encontrou = True
                st.error(f"⚠️ PADRÃO ENCONTRADO!")
                proximas = st.session_state.velas[i+10 : i+25]
                cols = st.columns(5)
                for idx, v in enumerate(proximas):
                    # FORÇANDO O X E O DESTAQUE
                    txt = f"🔥 **{v:.2f}x**" if v >= 8.0 else f"{v:.2f}x"
                    cols[idx % 5].write(f"{idx+1}º: {txt}")
                st.divider()
        if not encontrou:
            st.info("Padrão de 10 velas não repetido.")
    else: st.warning("Mínimo de 25 velas necessárias.")

st.divider()

# --- CONTADOR E VISUALIZAÇÃO ---
st.subheader("📊 Histórico (Tudo com x)")
total = len(st.session_state.velas)
st.header(f"{total} / 10.000")

# LISTA RÁPIDA COM X
if total > 0:
    ultimas_resumo = [f"🔥 **{v:.2f}x**" if v >= 8.0 else f"{v:.2f}x" for v in st.session_state.velas[-10:][::-1]]
    st.write(" | ".join(ultimas_resumo))

with st.expander("👁️ VER TODO O BANCO"):
    if total > 0:
        # TABELA COM X FORÇADO
        df_v = pd.DataFrame({"Vela": [f"{v:.2f}x" for v in st.session_state.velas]})
        st.dataframe(df_v.iloc[::-1], use_container_width=True, height=300)
    else: st.write("Banco vazio.")

st.divider()

# --- RESET REAL (ZERA TUDO) ---
st.subheader("⚙️ Configurações")
confirmar = st.checkbox("Confirmar: APAGAR TUDO e ZERAR?")
if st.button("🗑️ ZERAR HISTÓRICO AGORA", use_container_width=True):
    if confirmar:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.velas = [] 
        st.success("Zerado!")
        st.rerun()
