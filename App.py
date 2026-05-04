import streamlit as st
import pandas as pd
import os
import re

DB_FILE = "banco_velas_projeto.csv"
MAX_VELAS = 500

# =========================
# CARREGAR BANCO
# =========================
def carregar_dados():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            return pd.to_numeric(df["vela"], errors="coerce").dropna().tolist()
        except:
            return []
    return []

def salvar_dados(lista):
    pd.DataFrame({"vela": lista}).to_csv(DB_FILE, index=False)

# =========================
# INICIALIZAÇÃO
# =========================
if "velas" not in st.session_state:
    st.session_state.velas = carregar_dados()

# =========================
# FUNÇÃO DE EXTRAÇÃO (ROBUSTA)
# =========================
def extrair_velas(texto):
    if not texto:
        return []

    texto = texto.lower().replace(",", ".")
    
    # pega qualquer número decimal
    encontrados = re.findall(r"\d+\.?\d*", texto)

    velas = []
    for n in encontrados:
        try:
            v = float(n)
            if v >= 1.0 and v < 10000:
                velas.append(v)
        except:
            continue

    return velas

# =========================
# INTERFACE
# =========================
st.title("📊 HISTÓRICO DE VELAS")

entrada = st.text_area(
    "Cole as velas:",
    placeholder="Ex: 1.16x 9.64x 5,00x\n1.05x 1.99x 20x",
    height=150
)

# =========================
# BOTÃO ADICIONAR
# =========================
if st.button("🚀 ADICIONAR"):
    novas = extrair_velas(entrada)

    if novas:
        if len(novas) > MAX_VELAS:
            novas = novas[:MAX_VELAS]
            st.warning(f"Limitado a {MAX_VELAS} velas por vez")

        st.session_state.velas.extend(novas)
        salvar_dados(st.session_state.velas)

        st.success(f"{len(novas)} velas adicionadas!")
        st.rerun()
    else:
        st.error("Nenhuma vela válida encontrada!")

st.divider()

# =========================
# EXIBIÇÃO
# =========================
if st.session_state.velas:

    total = len(st.session_state.velas)
    st.subheader(f"Total no Histórico: {total}")

    dados = list(reversed(st.session_state.velas))
    df = pd.DataFrame({"VELAS": dados})

    # 🔥 CORRIGIDO: NUNCA MAIS FICA INVISÍVEL
    def colorir(val):
        try:
            val = float(val)
            if val >= 8:
                return "color: #FF00FF; font-weight: bold"
            elif val >= 2:
                return "color: #008000; font-weight: bold"
            else:
                return "color: #000000"  # preto
        except:
            return ""

    st.dataframe(
        df.style.map(colorir).format("{:.2f}x"),
        use_container_width=True,
        height=500
    )

    st.divider()

    # =========================
    # BOTÕES
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ APAGAR ÚLTIMAS 20"):
            if len(st.session_state.velas) >= 20:
                st.session_state.velas = st.session_state.velas[:-20]
            else:
                st.session_state.velas = []

            salvar_dados(st.session_state.velas)
            st.rerun()

    with col2:
        if st.button("🚨 ZERAR TUDO"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)

            st.session_state.velas = []
            st.rerun()

# =========================
# ANÁLISE REAL
# =========================
if st.session_state.velas:
    st.divider()
    st.subheader("📈 ANÁLISE RÁPIDA")

    ultimas = st.session_state.velas[-20:]

    if ultimas:
        acima_2 = sum(1 for v in ultimas if v >= 2)
        acima_6 = sum(1 for v in ultimas if v >= 6)

        st.write(f"Últimas 20 velas analisadas:")
        st.write(f"✔ >=2x: {acima_2}")
        st.write(f"🔥 >=6x: {acima_6}")

        # 🔥 DEBUG (se algo der errado você vê aqui)
        with st.expander("🔍 Ver últimas velas (debug)"):
            st.write(ultimas)
