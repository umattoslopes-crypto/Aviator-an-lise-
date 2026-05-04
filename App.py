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

entrada = st.text_area("Digite ou cole as velas (Ex: 1.16x 9.64x 5.00x)", height=150)

if st.button("🚀 ADICIONAR"):
    if entrada:
        # Limpa o texto para pegar apenas os números
        texto_limpo = entrada.lower().replace('x', '').replace(',', ' ').replace('\n', ' ')
        partes = texto_limpo.split()
        
        novas = []
        for p in partes:
            try:
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
# EXIBIÇÃO (CORREÇÃO DO ERRO VISUAL)
# =========================
if st.session_state.velas:
    st.subheader(f"Total no Histórico: {len(st.session_state.velas)}")
    
    # Inverte a ordem para o mais novo ficar no topo
    dados_invertidos = list(reversed(st.session_state.velas))
    df_visual = pd.DataFrame({"VALOR": dados_invertidos})
    
    # Função de cor atualizada para evitar o erro AttributeError
    def colorir(val):
        if val >= 8: return 'color: #FF00FF; font-weight: bold'
        if val >= 2: return 'color: #00FF00'
        return 'color: white'

    # O segredo está aqui: usar .map em vez de .applymap
    st.dataframe(
        df_visual.style.map(colorir).format("{:.2f}x"),
        use_container_width=True,
        height=500
    )

    st.divider()
    
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
