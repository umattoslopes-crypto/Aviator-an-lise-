import streamlit as st
import pandas as pd
import os
import re

DB_FILE = "banco_velas_projeto.csv"
LIMITE = 10000

# =========================
# BANCO DE DADOS (CARREGAMENTO LIMPO)
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # Carrega apenas o que for número real e limpa linhas vazias
            st.session_state.velas = [float(v) for v in df['vela'].dropna().tolist() if float(v) > 0]
        except: 
            st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'vela': st.session_state.velas[-LIMITE:]}).to_csv(DB_FILE, index=False)

# =========================
# INTERFACE (FOCO NA PRECISÃO)
# =========================
st.title("ATE 10.000 VELAS")

st.subheader("INSERIR SEQUÊNCIA")
# Instrução clara: use ponto para decimais
manual = st.text_area("Cole as velas aqui (Ex: 1.16x, 9.64x, 10.00x)", height=150)

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    if manual:
        # 1. Padronização total: vírgula vira ponto, remove 'x' e espaços
        texto_limpo = manual.replace(',', '.')
        
        # 2. Captura apenas os números com seus decimais
        # Este regex pega "1.16", "1.0", "10", "100.45"
        encontrados = re.findall(r"(\d+(?:\.\d+)?)", texto_pre_limpo := texto_limpo)
        
        novas = []
        for n in encontrados:
            try:
                v = float(n)
                if v > 0:
                    novas.append(v)
            except:
                continue

        if novas:
            st.session_state.velas += novas
            # Mantém o limite de 10k
            if len(st.session_state.velas) > LIMITE:
                st.session_state.velas = st.session_state.velas[-LIMITE:]
            salvar()
            st.success(f"✅ {len(novas)} velas adicionadas!")
            st.rerun()
        else:
            st.error("Nenhum número detectado. Use ponto para decimais (Ex: 1.16)")

st.divider()

# =========================
# HISTÓRICO E EXIBIÇÃO
# =========================
if st.session_state.velas:
    st.write(f"**HISTÓRICO COMPLETO (Total: {len(st.session_state.velas)})**")
    
    # Mostra do mais novo para o mais velho
    df_h = pd.DataFrame({"vela": reversed(st.session_state.velas)})
    st.dataframe(
        df_h.style.map(
            lambda v: "color:#FF00FF; font-weight:bold" if v >= 8 else 
                      "color:#00FF00" if v >= 2 else 
                      "color:white"
        ).format("{:.2f}x,"),
        use_container_width=True, height=350
    )

    st.divider()
    
    col_f1, col_f2 = st.columns([0.6, 0.4])
    with col_f1:
        st.write("**ÚLTIMAS 20 ADICIONADAS**")
        ultimas = st.session_state.velas[-20:]
        fmt = [f"<b style='color:{('#FF00FF' if v>=8 else '#00FF00' if v>=2 else '#FFF')}'>{v:.2f}x,</b>" for v in ultimas]
        st.markdown(" ".join(fmt), unsafe_allow_html=True)
    
    with col_f2:
        st.write("**REDEFINIR**")
        if st.button("APAGAR ÚLTIMAS 20"):
            st.session_state.velas = st.session_state.velas[:-20]
            salvar(); st.rerun()
        if st.button("ZERAR TUDO"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.velas = []
            st.rerun()
