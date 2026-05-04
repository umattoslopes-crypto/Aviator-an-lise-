import streamlit as st
import pandas as pd
import os
import re

DB_FILE = "banco_velas_projeto.csv"
MAX_VELAS = 500

# =========================
# BANCO DE DADOS
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.velas = pd.to_numeric(df['vela'], errors='coerce').dropna().tolist()
        except:
            st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'vela': st.session_state.velas}).to_csv(DB_FILE, index=False)

# =========================
# FUNÇÃO ULTRA ROBUSTA (CORREÇÃO TOTAL)
# =========================
def extrair_velas(texto):
    if not texto:
        return []

    # 🔥 Normaliza tudo
    texto = texto.lower()
    texto = texto.replace(',', '.')  # vírgula -> ponto

    # 🔥 Regex pega QUALQUER número decimal
    numeros = re.findall(r'\d+\.?\d*', texto)

    velas = []
    for num in numeros:
        try:
            val = float(num)

            # 🔥 FILTRO INTELIGENTE (remove lixo, mas aceita 1.00+)
            if val >= 1.0 and val < 10000:
                velas.append(val)

        except:
            continue

    return velas

# =========================
# INTERFACE
# =========================
st.title("📊 HISTÓRICO DE VELAS (PRO)")

entrada = st.text_area(
    "Cole as velas (qualquer formato)",
    placeholder="Ex: 1.16x 9.64x 5,00x\n1.05x 1.99x 20x",
    height=150
)

if st.button("🚀 ADICIONAR"):
    novas = extrair_velas(entrada)

    if novas:
        # 🔥 Limita para não travar
        if len(novas) > MAX_VELAS:
            novas = novas[:MAX_VELAS]
            st.warning(f"Limitado a {MAX_VELAS} velas por vez")

        st.session_state.velas.extend(novas)
        salvar()

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

    dados_invertidos = list(reversed(st.session_state.velas))
    df_visual = pd.DataFrame({"VALOR": dados_invertidos})

    # 🔥 COLORAÇÃO CORRIGIDA (100% funcional)
    def colorir(val):
        try:
            val = float(val)
            if val >= 8:
                return 'color: #FF00FF; font-weight: bold'
            elif val >= 2:
                return 'color: #00FF00'
            else:
                return 'color: #FFFFFF'
        except:
            return ''

    st.dataframe(
        df_visual.style.map(colorir).format("{:.2f}x"),
        use_container_width=True,
        height=500
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ APAGAR ÚLTIMAS 20"):
            if len(st.session_state.velas) >= 20:
                st.session_state.velas = st.session_state.velas[:-20]
            else:
                st.session_state.velas = []
            salvar()
            st.rerun()

    with col2:
        if st.button("🚨 ZERAR TUDO"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            st.session_state.velas = []
            st.rerun()

# =========================
# EXTRA (ANÁLISE RÁPIDA)
# =========================
if st.session_state.velas:
    st.divider()
    st.subheader("📈 ANÁLISE RÁPIDA")

    ultimas = st.session_state.velas[-20:]

    if ultimas:
        acima_2 = sum(1 for v in ultimas if v >= 2)
        acima_6 = sum(1 for v in ultimas if v >= 6)

        st.write(f"Últimas 20 velas:")
        st.write(f"✔ >=2x: {acima_2}")
        st.write(f"🔥 >=6x: {acima_6}")
