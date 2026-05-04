import streamlit as st
import pandas as pd
import os
import re

DB_FILE = "velas_salvas.csv"
MAX_VELAS = 500

# =========================
# BANCO LOCAL
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
# EXTRAÇÃO ROBUSTA
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
# BUSCA EXATA (SEM FALHA)
# =========================
def buscar_padrao(lista, padrao):
    resultados = []
    tamanho = len(padrao)

    for i in range(len(lista) - tamanho + 1):
        trecho = lista[i:i+tamanho]

        # comparação arredondada (corrige erro de float)
        match = all(round(trecho[j], 2) == round(padrao[j], 2) for j in range(tamanho))

        if match:
            proximas = lista[i+tamanho:i+tamanho+15]

            resultados.append({
                "posicao": i,
                "padrao": trecho,
                "proximas": proximas
            })

    return resultados

# =========================
# INTERFACE
# =========================
st.title("📊 HISTÓRICO DE VELAS")

entrada = st.text_area("Cole as velas:", height=150)

col1, col2, col3 = st.columns(3)

# ADICIONAR
with col1:
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
            st.error("Nenhuma vela válida!")

# SALVAR
with col2:
    if st.button("💾 SALVAR"):
        salvar(st.session_state.velas)
        st.success("Dados salvos!")

# RELOAD
with col3:
    if st.button("🔄 RELOAD"):
        st.session_state.velas = carregar()
        st.success("Dados recarregados!")
        st.rerun()

# =========================
# 🔍 BUSCA DE PADRÃO
# =========================
st.divider()
st.subheader("🔍 BUSCAR PADRÃO (EXATO - 5 VELAS)")

entrada_padrao = st.text_input("Digite 5 velas (ex: 1.20 1.50 1.10 2.00 1.30)")

if st.button("🔎 BUSCAR PADRÃO"):
    padrao = extrair_velas(entrada_padrao)

    if len(padrao) != 5:
        st.error("Digite exatamente 5 velas!")
    else:
        resultados = buscar_padrao(st.session_state.velas, padrao)

        if resultados:
            st.error(f"🚨 PADRÃO ENCONTRADO {len(resultados)}x!")

            for r in resultados:
                st.markdown(f"**📍 Posição:** {r['posicao']}")
                st.write("Padrão:", [f"{v:.2f}x" for v in r["padrao"]])
                st.write("🔥 Próximas 15 velas:", [f"{v:.2f}x" for v in r["proximas"]])
                st.divider()
        else:
            st.warning("Nenhum padrão encontrado")

# =========================
# BACKUP
# =========================
st.divider()
st.subheader("💾 BACKUP")

colb1, colb2 = st.columns(2)

with colb1:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "rb") as f:
            st.download_button("📥 Baixar Backup", f, "backup_velas.csv")

with colb2:
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
        if val >= 8:
            return "color: #FF00FF; font-weight: bold"
        elif val >= 2:
            return "color: #008000; font-weight: bold"
        else:
            return "color: #000000"

    st.dataframe(
        df.style.map(colorir).format("{:.2f}x"),
        use_container_width=True,
        height=400
    )

    st.divider()

    colx1, colx2 = st.columns(2)

    with colx1:
        if st.button("🗑️ APAGAR ÚLTIMAS 20"):
            st.session_state.velas = st.session_state.velas[:-20]
            salvar(st.session_state.velas)
            st.rerun()

    with colx2:
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
