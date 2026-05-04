import streamlit as st
import pandas as pd
import os
import re

DB_FILE = "velas_salvas.csv"
MAX_VELAS = 500

# =========================
# FUNÇÕES DE ARQUIVO
# =========================
def carregar():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            return pd.to_numeric(df["vela"], errors="coerce").dropna().tolist()
        except:
            return []
    return []

def salvar(lista):
    pd.DataFrame({"vela": lista}).to_csv(DB_FILE, index=False)

# =========================
# INICIALIZAÇÃO
# =========================
if "velas" not in st.session_state:
    st.session_state.velas = carregar()

# =========================
# EXTRAÇÃO
# =========================
def extrair_velas(texto):
    if not texto:
        return []

    texto = texto.lower().replace(",", ".")
    encontrados = re.findall(r"\d+\.?\d*", texto)

    velas = []
    for n in encontrados:
        try:
            v = float(n)
            if v >= 1.0:
                velas.append(v)
        except:
            continue

    return velas

# =========================
# INTERFACE
# =========================
st.title("📊 HISTÓRICO DE VELAS")

entrada = st.text_area("Cole as velas:", height=150)

# =========================
# BOTÕES PRINCIPAIS
# =========================
colA, colB, colC = st.columns(3)

with colA:
    if st.button("🚀 ADICIONAR"):
        novas = extrair_velas(entrada)

        if novas:
            if len(novas) > MAX_VELAS:
                novas = novas[:MAX_VELAS]

            st.session_state.velas.extend(novas)
            salvar(st.session_state.velas)

            st.success(f"{len(novas)} velas adicionadas!")
            st.rerun()
        else:
            st.error("Nenhuma vela válida encontrada!")

with colB:
    if st.button("💾 SALVAR"):
        salvar(st.session_state.velas)
        st.success("Dados salvos!")

with colC:
    if st.button("🔄 RELOAD"):
        st.session_state.velas = carregar()
        st.success("Dados recarregados do arquivo!")
        st.rerun()

# =========================
# BACKUP / RESTAURAÇÃO
# =========================
st.divider()
st.subheader("💾 Backup")

col1, col2 = st.columns(2)

with col1:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "rb") as file:
            st.download_button(
                "📥 Baixar Backup",
                file,
                file_name="backup_velas.csv"
            )

with col2:
    arquivo = st.file_uploader("📤 Restaurar Backup", type=["csv"])

    if arquivo:
        df = pd.read_csv(arquivo)
        st.session_state.velas = pd.to_numeric(df["vela"], errors="coerce").dropna().tolist()
        salvar(st.session_state.velas)
        st.success("Backup restaurado!")
        st.rerun()

# =========================
# EXIBIÇÃO
# =========================
if st.session_state.velas:

    dados = list(reversed(st.session_state.velas))
    df = pd.DataFrame({"VELAS": dados})

    def colorir(val):
        try:
            if val >= 8:
                return "color: #FF00FF; font-weight: bold"
            elif val >= 2:
                return "color: #008000; font-weight: bold"
            else:
                return "color: #000000"
        except:
            return ""

    st.dataframe(
        df.style.map(colorir).format("{:.2f}x"),
        use_container_width=True,
        height=400
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ APAGAR ÚLTIMAS 20"):
            st.session_state.velas = st.session_state.velas[:-20]
            salvar(st.session_state.velas)
            st.rerun()

    with col2:
        if st.button("🚨 ZERAR TUDO"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            st.session_state.velas = []
            st.rerun()

# =========================
# ANÁLISE
# =========================
if st.session_state.velas:
    st.divider()
    st.subheader("📈 ANÁLISE RÁPIDA")

    ultimas = st.session_state.velas[-20:]

    if ultimas:
        acima_2 = sum(1 for v in ultimas if v >= 2)
        acima_6 = sum(1 for v in ultimas if v >= 6)

        st.write(f"✔ >=2x: {acima_2}")
        st.write(f"🔥 >=6x: {acima_6}")
