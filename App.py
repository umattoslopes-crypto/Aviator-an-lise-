import streamlit as st
import pandas as pd
import os

# --- CONFIGURAÇÕES INICIAIS ---
DB_FILE = "historico_velas.csv"
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.velas = pd.read_csv(DB_FILE)['velas'].tolist()
    else:
        st.session_state.velas = []

def salvar_dados():
    pd.DataFrame({'velas': st.session_state.velas}).to_csv(DB_FILE, index=False)

# --- LÓGICA DE PADRÃO (O que você já tinha) ---
encontrou = False # Variável para controle do seu if lá embaixo
# (Aqui viria sua lógica de busca automática de 10 velas se desejar manter)

st.divider()
if not encontrou:
    st.info("Padrão de 10 velas não repetido.")
else: 
    st.warning("Mínimo de 25 velas necessárias.")

st.divider()

# --- NOVO: BUSCA MANUAL DE PADRÃO ---
st.subheader("🔍 Localizar Sequência Manual")
col_input, col_btn = st.columns([3, 1])

with col_input:
    seq_input = st.text_input("Digite a sequência separada por vírgula", placeholder="Ex: 1.50, 2.00, 1.10")

if col_btn.button("🔍 BUSCAR", use_container_width=True):
    if seq_input:
        try:
            padrao_buscado = [float(x.strip()) for x in seq_input.split(",")]
            n_seq = len(padrao_buscado)
            achou_manual = False
            
            for i in range(len(st.session_state.velas) - n_seq + 1):
                if st.session_state.velas[i:i+n_seq] == padrao_buscado:
                    st.success(f"✅ Padrão encontrado na posição {i+1}!")
                    achou_manual = True
            
            if not achou_manual:
                st.error("❌ Sequência não encontrada.")
        except:
            st.error("Formato inválido! Use: 1.50, 2.00")

st.divider()

# --- CONTADOR E VISUALIZAÇÃO COM CORES ---
st.subheader("📊 Histórico (Tudo com x)")
total = len(st.session_state.velas)
st.header(f"{total} / 10.000")

# LISTA RÁPIDA COM CORES (Velas > 8x em Rosa Choque)
if total > 0:
    resumo_html = []
    # Pega as últimas 10 velas e inverte a ordem
    for v in st.session_state.velas[-10:][::-1]:
        if v >= 8.0:
            # Rosa Choque / Pink
            resumo_html.append(f"<b style='color: #FF00FF; font-size: 1.1em;'>🔥 {v:.2f}x</b>")
        elif v >= 2.0:
            # Verde
            resumo_html.append(f"<span style='color: #00FF00;'>{v:.2f}x</span>")
        else:
            # Cinza Claro
            resumo_html.append(f"<span style='color: #DDDDDD;'>{v:.2f}x</span>")
    
    st.markdown(" | ".join(resumo_html), unsafe_allow_html=True)

with st.expander("👁️ VER TODO O BANCO"):
    if total > 0:
        df_v = pd.DataFrame({"Vela": [f"{v:.2f}x" for v in st.session_state.velas]})
        st.dataframe(df_v.iloc[::-1], use_container_width=True, height=300)
    else: 
        st.write("Banco vazio.")

st.divider()

# --- RESET REAL (ZERA TUDO) ---
st.subheader("⚙️ Configurações")
confirmar = st.checkbox("Confirmar: APAGAR TUDO e ZERAR?")
if st.button("🗑️ ZERAR HISTÓRICO AGORA", use_container_width=True):
    if confirmar:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.velas = [] 
        st.success("Zerado!")
        st.rerun()
