import streamlit as st
import pandas as pd
import os
import re

DB_FILE = "velas_salvas.csv"
MAX_VELAS = 10000 

if "velas" not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.velas = df["vela"].astype(float).tolist()
        except: st.session_state.velas = []
    else: st.session_state.velas = []

def salvar(lista):
    pd.DataFrame({"vela": lista[-MAX_VELAS:]}).to_csv(DB_FILE, index=False)

# =========================
# EXTRAÇÃO FORÇA BRUTA (NÃO FALHA)
# =========================
def extrair_velas(texto):
    if not texto: return []
    # 1. Troca vírgula por ponto
    t = texto.replace(',', '.')
    # 2. Explode o texto em pedaços por espaço ou quebra de linha
    partes = t.split()
    
    velas_validadas = []
    for p in partes:
        # 3. Remove QUALQUER coisa que não seja número ou ponto (limpa o 'x', 'X', etc)
        numero_limpo = re.sub(r'[^0-9.]', '', p)
        if numero_limpo:
            try:
                v = float(numero_limpo)
                if v >= 1.0:
                    velas_validadas.append(v)
            except: continue
    return velas_validadas

# =========================
# BUSCA COM MARGEM DE ERRO
# =========================
def buscar_padrao(lista, padrao):
    resultados = []
    t = len(padrao)
    if t == 0: return []
    for i in range(len(lista) - t + 1):
        trecho = lista[i:i+t]
        # Se a diferença for menor que 0.01, ele aceita (resolve 1.16x vs 1.16)
        if all(abs(trecho[j] - padrao[j]) < 0.01 for j in range(t)):
            resultados.append({"posicao": i, "padrao": trecho, "proximas": lista[i+t:i+t+15]})
    return resultados

# =========================
# INTERFACE
# =========================
st.title("📊 SCANNER DE CICLOS - 10k")

entrada = st.text_area("Cole as velas aqui (Ex: 1.16x 1.23x 9.64x):", height=150)

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    novas = extrair_velas(entrada)
    if novas:
        st.session_state.velas.extend(novas)
        salvar(st.session_state.velas)
        st.success(f"✅ {len(novas)} velas adicionadas!")
        st.rerun()

st.divider()
st.subheader("🔍 BUSCAR PADRÃO")
entrada_padrao = st.text_input("Sequência para busca (Ex: 1.16x 1.23x):")

if st.button("🔎 BUSCAR"):
    padrao = extrair_velas(entrada_padrao)
    if padrao:
        res = buscar_padrao(st.session_state.velas, padrao)
        if res:
            st.error(f"🚨 ENCONTRADO {len(res)}x!")
            for r in res:
                with st.expander(f"📍 Ocorrência"):
                    st.write("Padrão:", [f"{v:.2f}x" for v in r["padrao"]])
                    prox = []
                    for v in r["proximas"]:
                        cor = "magenta" if v >= 8 else "green" if v >= 2 else "white"
                        prox.append(f":{cor}[{v:.2f}x]")
                    st.markdown(f"**Próximas:** {' '.join(prox)}")
        else: st.warning("Não encontrado.")

st.divider()
if st.session_state.velas:
    df_visual = pd.DataFrame({"VELAS": reversed(st.session_state.velas)})
    st.dataframe(df_visual.style.map(lambda v: "color: #FF00FF; font-weight: bold" if v >= 8 else "color: #00FF00; font-weight: bold" if v >= 2 else "color: white").format("{:.2f}x"), use_container_width=True, height=400)
    
    if st.button("🚨 ZERAR TUDO"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()
