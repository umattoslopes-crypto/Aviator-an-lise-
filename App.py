import streamlit as st
import pandas as pd
import os
import re

# Configurações do Banco
DB_FILE = "banco_velas_projeto.csv"
LIMITE_HISTORICO = 10000

# =========================
# BANCO DE DADOS (LIMPEZA TOTAL)
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # Garante que carregue tudo a partir de 1.00
            st.session_state.velas = [float(v) for v in df['vela'].dropna() if float(v) >= 1.0]
        except:
            st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'vela': st.session_state.velas[-LIMITE_HISTORICO:]}).to_csv(DB_FILE, index=False)

# =========================
# EXTRAÇÃO (CURA PARA CASA 1.00x - 1.99x)
# =========================
def extrair_velas_texto(texto):
    if not texto:
        return []
    
    # 1. Troca vírgula por ponto (essencial para decimais)
    t = texto.replace(',', '.')
    
    # 2. Captura números que podem ou não ter decimais e podem ter o 'x' colado
    # Este regex é focado em pegar o número puro, ignorando o 'x'
    encontrados = re.findall(r"(\d+(?:\.\d+)?)", t)
    
    velas = []
    for n in encontrados:
        try:
            val = float(n)
            # REGRA DE OURO: Aceita TUDO a partir de 1.00
            if val >= 1.0:
                velas.append(val)
        except:
            continue
    return velas

# =========================
# BUSCA (ACEITA 1.16x E 1x)
# =========================
def buscar_padrao(lista, padrao):
    resultados = []
    tamanho = len(padrao)
    if tamanho == 0: return []

    for i in range(len(lista) - tamanho):
        trecho = lista[i:i+tamanho]
        # Tolerância de 0.01 para não errar por arredondamento
        match = all(abs(trecho[j] - padrao[j]) < 0.01 for j in range(tamanho))

        if match:
            proximas = lista[i+tamanho : i+tamanho+15]
            resultados.append({"posicao": i, "padrao": trecho, "proximas": proximas})
    return resultados

# =========================
# INTERFACE
# =========================
st.set_page_config(page_title="Scanner de Ciclos", layout="centered")
st.title("PROJETO 10.000 VELAS")

st.subheader("📥 INSERIR SEQUÊNCIA MANUAL")
manual = st.text_area("Cole as velas (Ex: 1.16x, 1x, 9.64x, 1.05x...)", height=150)

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    novas = extrair_velas_texto(manual)
    if novas:
        st.session_state.velas += novas
        if len(st.session_state.velas) > LIMITE_HISTORICO:
            st.session_state.velas = st.session_state.velas[-LIMITE_HISTORICO:]
        salvar()
        st.success(f"✅ {len(novas)} velas adicionadas! (Velas de 1x incluídas)")
        st.rerun()

st.divider()

# BUSCA DE PADRÃO
st.write("**🔍 BUSCA DE PADRÃO (Pode usar 1.16x)**")
col_b1, col_b2 = st.columns([0.8, 0.2])
with col_b1:
    seq_input = st.text_input("Sequência...", label_visibility="collapsed")
with col_b2:
    btn_busca = st.button("🔎")

if btn_busca and seq_input:
    padrao_buscado = extrair_velas_texto(seq_input)
    if len(padrao_buscado) < 2:
        st.error("Digite pelo menos 2 velas!")
    else:
        res = buscar_padrao(st.session_state.velas, padrao_buscado)
        if res:
            st.error(f"🚨 ENCONTRADO {len(res)}x!")
            for r in res:
                with st.expander(f"📍 Posição {r['posicao']}"):
                    st.write("**Padrão:**", [f"{v:.2f}x," for v in r["padrao"]])
                    # Próximas coloridas
                    txt = []
                    for v in r["proximas"]:
                        cor = "magenta" if v >= 8 else "green" if v >= 2 else "white"
                        txt.append(f":{cor}[{v:.2f}x,]")
                    st.markdown(f"**Próximas:** {' '.join(txt)}")
        else:
            st.warning("Padrão não encontrado.")

st.divider()

# HISTÓRICO COMPLETO
st.write(f"**📋 HISTÓRICO COMPLETO (Total: {len(st.session_state.velas)})**")
if st.session_state.velas:
    df_h = pd.DataFrame({"vela": reversed(st.session_state.velas)})
    st.dataframe(
        df_h.style.map(
            lambda v: "color:#FF00FF; font-weight:bold" if v >= 8 else 
                      "color:#00FF00" if v >= 2 else "color:white"
        ).format("{:.2f}x,"),
        use_container_width=True, height=400
    )

st.divider()

# ÚLTIMAS 20 E RESET
col_f1, col_f2 = st.columns([0.6, 0.4])
with col_f1:
    st.write("**📉 ÚLTIMAS 20 ADICIONADAS**")
    if st.session_state.velas:
        ultimas = st.session_state.velas[-20:]
        fmt = [f"<b style='color:{('#FF00FF' if v>=8 else '#00FF00' if v>=2 else '#FFF')}'>{v:.2f}x,</b>" for v in ultimas]
        st.markdown(" ".join(fmt), unsafe_allow_html=True)

with col_f2:
    st.write("**⚙️ REDEFINIR**")
    if st.button("🗑️ APAGAR ÚLTIMAS 20", use_container_width=True):
        st.session_state.velas = st.session_state.velas[:-20]
        salvar(); st.rerun()
    if st.button("🚨 ZERAR TUDO", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []; st.rerun()
