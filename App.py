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
            # Carrega e remove qualquer erro de tentativas anteriores
            st.session_state.velas = [float(v) for v in df['vela'].dropna() if float(v) > 0]
        except:
            st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    # Salva garantindo que o CSV seja uma lista pura de números
    pd.DataFrame({'vela': st.session_state.velas[-LIMITE_HISTORICO:]}).to_csv(DB_FILE, index=False)

# =========================
# FUNÇÃO DE EXTRAÇÃO (LIDA COM 'x' E VÍRGULA)
# =========================
def extrair_velas_texto(texto):
    if not texto:
        return []
    # 1. Padroniza: vírgula vira ponto e remove letras 'x'
    texto_limpo = texto.lower().replace(',', '.').replace('x', ' ')
    # 2. Captura apenas os números (inteiros ou decimais)
    encontrados = re.findall(r"(\d+(?:\.\d+)?)", texto_limpo)
    
    velas = []
    for n in encontrados:
        try:
            val = float(n)
            if val >= 1.0:
                velas.append(val)
        except:
            continue
    return velas

# =========================
# BUSCA DE PADRÃO (COM TOLERÂNCIA)
# =========================
def buscar_padrao(lista, padrao):
    resultados = []
    tamanho = len(padrao)
    if tamanho == 0: return []

    for i in range(len(lista) - tamanho):
        trecho = lista[i:i+tamanho]
        # Compara se a diferença entre os números é menor que 0.01
        # Isso permite que 1.16x digitado encontre 1.16 no banco
        match = all(abs(trecho[j] - padrao[j]) < 0.01 for j in range(tamanho))

        if match:
            # Pega as próximas 15 velas após o padrão
            proximas = lista[i+tamanho : i+tamanho+15]
            resultados.append({
                "posicao": i,
                "padrao": trecho,
                "proximas": proximas
            })
    return resultados

# =========================
# INTERFACE (LAYOUT DO SEU DESENHO)
# =========================
st.set_page_config(page_title="Scanner de Ciclos", layout="centered")
st.title("PROJETO 10.000 VELAS")

st.subheader("📥 INSERIR SEQUÊNCIA MANUAL")
manual = st.text_area("Cole as velas (Ex: 1.16x, 9.64x, 5.00x...)", height=150)

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    novas = extrair_velas_texto(manual)
    if novas:
        st.session_state.velas += novas
        if len(st.session_state.velas) > LIMITE_HISTORICO:
            st.session_state.velas = st.session_state.velas[-LIMITE_HISTORICO:]
        salvar()
        st.success(f"✅ {len(novas)} velas adicionadas!")
        st.rerun()

st.divider()

# =========================
# BUSCA DE PADRÃO (ACEITA 1.16x)
# =========================
st.write("**🔍 BUSCA DE PADRÃO (EX: 1.16x 1.09x)**")
col_b1, col_b2 = st.columns([0.8, 0.2])

with col_b1:
    seq_input = st.text_input("Digite a sequência para buscar...", label_visibility="collapsed")

with col_b2:
    btn_busca = st.button("🔎")

if btn_busca and seq_input:
    # Extrai o padrão tratando o 'x' e vírgulas
    padrao_buscado = extrair_velas_texto(seq_input)
    
    if len(padrao_buscado) < 2:
        st.error("Digite pelo menos 2 velas para buscar um padrão!")
    else:
        resultados = buscar_padrao(st.session_state.velas, padrao_buscado)
        
        if resultados:
            st.error(f"🚨 PADRÃO ENCONTRADO {len(resultados)}x!")
            for r in resultados:
                with st.expander(f"📍 Ocorrência na Posição {r['posicao']}"):
                    st.write("**Padrão:**", [f"{v:.2f}x," for v in r["padrao"]])
                    # Mostra as próximas coloridas
                    txt_proximas = []
                    for v in r["proximas"]:
                        cor = "magenta" if v >= 8 else "green" if v >= 2 else "white"
                        txt_proximas.append(f":{cor}[{v:.2f}x,]")
                    st.markdown(f"**Próximas:** {' '.join(txt_proximas)}")
        else:
            st.warning("Padrão não encontrado no histórico de 10.000 velas.")

st.divider()

# =========================
# HISTÓRICO (FORMATO 0.00x,)
# =========================
st.write(f"**📋 HISTÓRICO COMPLETO (Total: {len(st.session_state.velas)})**")
if st.session_state.velas:
    df_h = pd.DataFrame({"vela": reversed(st.session_state.velas)})
    st.dataframe(
        df_h.style.map(
            lambda v: "color:#FF00FF; font-weight:bold" if v >= 8 else 
                      "color:#00FF00" if v >= 2 else 
                      "color:white"
        ).format("{:.2f}x,"),
        use_container_width=True, 
        height=400
    )

st.divider()

# =========================
# ÚLTIMAS 20 E RESET
# =========================
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
        salvar()
        st.rerun()
        
    if st.button("🚨 ZERAR TUDO", use_container_width=True):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()
