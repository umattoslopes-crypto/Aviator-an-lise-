import streamlit as st
import pandas as pd
import os
import re

# Configurações do Banco
DB_FILE = "banco_velas_projeto.csv"
LIMITE = 10000

# =========================
# BANCO DE DADOS (LIMPEZA TOTAL)
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # Carrega e remove qualquer linha vazia ou erro de tentativas anteriores
            st.session_state.velas = [float(v) for v in df['vela'].dropna() if float(v) > 0]
        except:
            st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    # Salva garantindo que o CSV seja uma lista pura de números
    pd.DataFrame({'vela': st.session_state.velas[-LIMITE:]}).to_csv(DB_FILE, index=False)

# =========================
# INTERFACE (LIMPA E DIRETA)
# =========================
st.set_page_config(page_title="Analisador de Ciclos", layout="centered")
st.title("PROJETO 10.000 VELAS")

st.subheader("📥 INSERIR SEQUÊNCIA MANUAL")
# Área de texto grande para suportar as 6 horas de jogo
manual = st.text_area(
    "Cole as velas aqui (Ex: 1.16x, 9.64x, 5.00x...)", 
    height=250, 
    placeholder="Pode colar a sequência completa aqui..."
)

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    if manual:
        # A MÁGICA DA FIDELIDADE: 
        # 1. Padroniza vírgulas para pontos
        texto_pre_limpo = manual.replace(',', '.')
        # 2. Captura apenas os números (inteiros ou decimais)
        # Isso ignora 'x', espaços, quebras de linha e qualquer lixo
        m_nums = re.findall(r"(\d+(?:\.\d+)?)", texto_pre_limpo)
        
        novas = []
        for n in m_nums:
            try:
                val = float(n)
                if val > 0:
                    novas.append(val)
            except:
                continue

        if novas:
            st.session_state.velas += novas
            # Mantém o limite de 10.000 velas
            if len(st.session_state.velas) > LIMITE:
                st.session_state.velas = st.session_state.velas[-LIMITE:]
            salvar()
            st.success(f"✅ {len(novas)} velas adicionadas com fidelidade total!")
            st.rerun()
        else:
            st.error("Não encontrei números válidos no texto colado.")

st.divider()

# =========================
# BUSCA DE PADRÃO (POR NÚMEROS REAIS)
# =========================
st.write("**🔍 BUSCA DE PADRÃO NO HISTÓRICO**")
col_b1, col_b2 = st.columns([0.8, 0.2])

with col_b1:
    seq_input = st.text_input("Sequência...", label_visibility="collapsed", placeholder="Ex: 1.16 1.09")

with col_b2:
    if st.button("🔎"):
        if seq_input:
            # Extrai o padrão da mesma forma limpa
            padrao = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)", seq_input.replace(',', '.'))]
            h = st.session_state.velas
            achados = 0
            for i in range(len(h) - len(padrao)):
                if h[i:i+len(padrao)] == padrao:
                    achados += 1
                    # Mostra o resultado com a vírgula após o x conforme solicitado
                    st.write(f"📍 Ocorrência {achados}: Próxima vela foi **{h[i+len(padrao)]:.2f}x,**")
            if achados == 0:
                st.warning("Padrão não encontrado no banco de dados.")

st.divider()

# =========================
# HISTÓRICO (FORMATO: 0.00x,)
# =========================
st.write(f"**📋 HISTÓRICO COMPLETO (Total: {len(st.session_state.velas)})**")
if st.session_state.velas:
    # Mostra do mais novo para o mais velho (Linha 0 é a última inserida)
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
# ÚLTIMAS 20 E REDEFINIR
# =========================
col_f1, col_f2 = st.columns([0.6, 0.4])

with col_f1:
    st.write("**📉 ÚLTIMAS 20 ADICIONADAS**")
    if st.session_state.velas:
        ultimas = st.session_state.velas[-20:]
        # Formatação com a vírgula após o x
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
