import streamlit as st
import pandas as pd
import os
import re

# Configuração de Limites
DB_FILE = "velas_salvas.csv"
MAX_VELAS = 10000 

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
    # Salva garantindo o limite de 10.000 velas
    pd.DataFrame({"vela": lista[-MAX_VELAS:]}).to_csv(DB_FILE, index=False)

# =========================
# INICIALIZAÇÃO
# =========================
if "velas" not in st.session_state:
    st.session_state.velas = carregar()

# =========================
# EXTRAÇÃO FIEL (RECONHECE 1.23x E 1x)
# =========================
def extrair_velas(texto):
    if not texto:
        return []
    
    # 1. Padroniza vírgula para ponto
    t = texto.replace(',', '.')
    
    # 2. A FÓRMULA QUE FUNCIONA: Captura números colados ou não no 'x'
    # Esse regex ignora o 'x' mas pega o valor numérico perfeitamente
    encontrados = re.findall(r"(\d+(?:\.\d+)?)", t)
    
    velas_validadas = []
    for n in encontrados:
        try:
            v = float(n)
            # Aceita qualquer vela a partir de 1.00 (casa dos 1x incluída)
            if v >= 1.0:
                velas_validadas.append(v)
        except:
            continue
    return velas_validadas

# =========================
# BUSCA COM TOLERÂNCIA
# =========================
def buscar_padrao(lista, padrao):
    resultados = []
    tamanho = len(padrao)
    if tamanho == 0: return []

    for i in range(len(lista) - tamanho + 1):
        trecho = lista[i:i+tamanho]
        # Margem de 0.01 para garantir que 1.23x digitado encontre 1.23 no banco
        match = all(abs(trecho[j] - padrao[j]) < 0.01 for j in range(tamanho))

        if match:
            # Pega as próximas 15 velas para análise do ciclo
            proximas = lista[i+tamanho:i+tamanho+15]
            resultados.append({
                "posicao": i,
                "padrao": trecho,
                "proximas": proximas
            })
    return resultados

# =========================
# INTERFACE PRINCIPAL
# =========================
st.set_page_config(page_title="Scanner de Ciclos 10k", layout="wide")
st.title("📊 SCANNER DE CICLOS - 10.000 VELAS")

# Entrada de Dados
entrada = st.text_area("Cole as velas (Ex: 1.23x 1.05x 9.64x):", height=150)

col_add, col_save, col_reload = st.columns(3)

with col_add:
    if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
        novas = extrair_velas(entrada)
        if novas:
            st.session_state.velas.extend(novas)
            # Mantém apenas as últimas 10k na memória
            st.session_state.velas = st.session_state.velas[-MAX_VELAS:]
            salvar(st.session_state.velas)
            st.success(f"✅ {len(novas)} velas adicionadas!")
            st.rerun()

with col_save:
    if st.button("💾 SALVAR BACKUP", use_container_width=True):
        salvar(st.session_state.velas)
        st.success("Backup salvo com sucesso!")

with col_reload:
    if st.button("🔄 RECARREGAR BANCO", use_container_width=True):
        st.session_state.velas = carregar()
        st.rerun()

# =========================
# 🔍 BUSCA DE PADRÃO
# =========================
st.divider()
st.subheader("🔍 BUSCAR PADRÃO NO HISTÓRICO")
entrada_padrao = st.text_input("Digite a sequência que você lembrou (Aceita o 'x'):")

if st.button("🔎 BUSCAR AGORA"):
    padrao_buscado = extrair_velas(entrada_padrao)
    if not padrao_buscado:
        st.error("Digite um padrão válido!")
    else:
        resultados = buscar_padrao(st.session_state.velas, padrao_buscado)
        if resultados:
            st.error(f"🚨 ENCONTRADO {len(resultados)}x NO HISTÓRICO!")
            for r in resultados:
                with st.expander(f"📍 Ocorrência encontrada na sequência"):
                    st.write("**Padrão:**", [f"{v:.2f}x" for v in r["padrao"]])
                    # Formatação colorida para facilitar visualização
                    txt_prox = []
                    for v in r["proximas"]:
                        cor = "magenta" if v >= 8 else "green" if v >= 2 else "white"
                        txt_prox.append(f":{cor}[{v:.2f}x]")
                    st.markdown(f"**Próximas 15 velas:** {' '.join(txt_prox)}")
        else:
            st.warning("Padrão não encontrado nas 10.000 velas.")

# =========================
# EXIBIÇÃO DO HISTÓRICO
# =========================
st.divider()
if st.session_state.velas:
    st.subheader(f"📋 HISTÓRICO ATUAL (Total: {len(st.session_state.velas)})")
    
    # Inverte para o mais novo aparecer no topo
    df_visual = pd.DataFrame({"VELAS": reversed(st.session_state.velas)})

    def aplicar_cor(val):
        if val >= 8: return "color: #FF00FF; font-weight: bold"
        if val >= 2: return "color: #00FF00; font-weight: bold"
        return "color: #FFFFFF"

    st.dataframe(
        df_visual.style.map(aplicar_cor).format("{:.2f}x"), 
        use_container_width=True, 
        height=400
    )

    # Botões de Redefinição
    st.divider()
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("🗑️ APAGAR ÚLTIMAS 20"):
            st.session_state.velas = st.session_state.velas[:-20]
            salvar(st.session_state.velas)
            st.rerun()
    with col_r2:
        if st.button("🚨 ZERAR TUDO"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            st.session_state.velas = []
            st.rerun()
