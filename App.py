import streamlit as st
import pandas as pd
import os
import re

DB_FILE = "velas.csv"
MAX_VELAS = 10000

# =========================
# BANCO
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.velas = df['velas'].dropna().tolist()
        except:
            st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'velas': st.session_state.velas[-MAX_VELAS:]}).to_csv(DB_FILE, index=False)

# =========================
# EXTRAÇÃO PERFEITA
# =========================
def extrair(texto):
    texto = texto.lower().replace(',', '.')
    
    # pega TODOS os números com x
    encontrados = re.findall(r"\d+(\.\d+)?x", texto)

    velas = []
    for e in encontrados:
        try:
            val = float(e.replace('x',''))
            velas.append(val)
        except:
            continue

    return velas

# =========================
# INTERFACE
# =========================
st.title("📊 ANALISADOR DE VELAS (SIMPLES E CERTO)")

entrada = st.text_area(
    "Cole aqui os números do print (ex: 1.25x 2.30x 10.00x)",
    height=150
)

# =========================
# ADICIONAR
# =========================
if st.button("🚀 ADICIONAR"):

    if entrada.strip():

        novas = extrair(entrada)

        if not novas:
            st.error("Nenhuma vela encontrada. Verifique o formato.")
        else:
            st.session_state.velas.extend(novas)
            salvar()

            st.success(f"{len(novas)} velas adicionadas!")
            st.rerun()

st.divider()

# =========================
# BUSCA
# =========================
st.subheader("🔍 BUSCA DE PADRÃO")

seq = st.text_input("Ex: 1.25 2.00 3.50")

if st.button("Buscar"):
    if seq:
        try:
            padrao = [float(x) for x in seq.split()]
            hist = st.session_state.velas

            for i in range(len(hist) - len(padrao)):
                if hist[i:i+len(padrao)] == padrao:
                    st.success("Encontrado!")
                    st.write(hist[i+len(padrao):i+len(padrao)+10])
                    break
            else:
                st.error("Não encontrado")

        except:
            st.error("Erro no padrão")

st.divider()

# =========================
# HISTÓRICO
# =========================
st.subheader("📋 HISTÓRICO")

if st.session_state.velas:
    df = pd.DataFrame({"Vela": st.session_state.velas})

    def cor(v):
        if v >= 8:
            return "color:#FF00FF; font-weight:bold"
        elif v >= 2:
            return "color:#00FF00"
        else:
            return "color:white"

    st.dataframe(
        df.style.map(cor).format("{:.2f}x"),
        height=400,
        use_container_width=True
    )

st.divider()

# =========================
# ÚLTIMAS 20
# =========================
st.subheader("📉 ÚLTIMAS 20")

if st.session_state.velas:
    ultimas = st.session_state.velas[-20:]

    texto = []
    for v in ultimas:
        cor = "#FF00FF" if v >= 8 else "#00FF00" if v >= 2 else "#FFFFFF"
        texto.append(f"<b style='color:{cor}'>{v:.2f}x</b>")

    st.markdown(" , ".join(texto), unsafe_allow_html=True)

st.divider()

# =========================
# RESET
# =========================
if st.checkbox("Reset"):

    if st.button("Apagar últimas 20"):
        st.session_state.velas = st.session_state.velas[:-20]
        salvar()
        st.rerun()

    if st.button("Zerar tudo"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()
