import streamlit as st
import pandas as pd
import os

DB_FILE = "banco_velas_projeto.csv"

# =========================
# BANCO DE DADOS
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # Carrega os dados garantindo que sejam números
            st.session_state.velas = df.iloc[:, 0].astype(float).tolist()
        except:
            st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'vela': st.session_state.velas}).to_csv(DB_FILE, index=False)

# =========================
# INTERFACE
# =========================
st.title("📊 HISTÓRICO DE VELAS")

# Entrada de texto simples
entrada = st.text_area("Cole as velas aqui (Ex: 1.16x 9.64x 5.00x)", height=150)

if st.button("🚀 ADICIONAR"):
    if entrada:
        # Limpa o texto: tira 'x' e troca vírgula por espaço para separar os números
        texto_limpo = entrada.replace('x', '').replace(',', ' ')
        partes = texto_limpo.split()
        
        novas = []
        for p in partes:
            try:
                # Converte para número real
                val = float(p)
                novas.append(val)
            except:
                continue
        
        if novas:
            st.session_state.velas += novas
            salvar()
            st.success(f"{len(novas)} velas adicionadas!")
            st.rerun()

st.divider()

# =========================
# EXIBIÇÃO (SEM BURACOS EM BRANCO)
# =========================
if st.session_state.velas:
    st.subheader(f"Total no Histórico: {len(st.session_state.velas)}")
    
    # Criamos a tabela com os dados invertidos (mais recentes no topo)
    dados_invertidos = list(reversed(st.session_state.velas))
    df_visual = pd.DataFrame({"VALOR": dados_invertidos})
    
    # Exibe a tabela SEM o estilo que estava causando o "branco"
    # O estilo agora é aplicado de forma mais simples
    def colorir(val):
        if val >= 8: return 'color: #FF00FF; font-weight: bold'
        if val >= 2: return 'color: #00FF00'
        return 'color: white'

    st.dataframe(
        df_visual.style.applymap(colorir).format("{:.2f}x"),
        use_container_width=True,
        height=500
    )

    st.divider()
    
    # Botões de controle
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ APAGAR ÚLTIMAS 20"):
            st.session_state.velas = st.session_state.velas[:-20]
            salvar()
            st.rerun()
    with col2:
        if st.button("🚨 ZERAR TUDO"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            st.session_state.velas = []
            st.rerun()
