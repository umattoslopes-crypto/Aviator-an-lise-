import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURAÇÕES DE PERSISTÊNCIA (PARA NUNCA PERDER OS DADOS) ---
DB_FILE = "historico_velas.csv"

# Se o arquivo existe, ele carrega. Se não, começa do zero.
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.velas = pd.read_csv(DB_FILE)['velas'].tolist()
    else:
        st.session_state.velas = []

# Função que grava no arquivo CSV
def salvar_dados():
    pd.DataFrame({'velas': st.session_state.velas}).to_csv(DB_FILE, index=False)

st.title("🤖 Analisador de Padrões - Crash")

# --- ÁREA DE ENTRADA (OCR / MANUAL / ATÉ 500 VELAS) ---
st.subheader("📥 Inserir Dados")
input_velas = st.text_area("Cole as velas aqui (transcrição do print ou manual):", placeholder="Ex: 1.50 2.10 10.50...")

if st.button("📥 ADICIONAR AO HISTÓRICO"):
    if input_velas:
        # Regex que identifica números decimais e inteiros (trata vírgula como ponto)
        novas_velas = [float(v) for v in re.findall(r"\d+\.\d+|\d+", input_velas.replace(',', '.'))]
        st.session_state.velas.extend(novas_velas)
        
        # Limita a 10 mil velas para não travar o sistema
        st.session_state.velas = st.session_state.velas[-10000:]
        
        # SALVA NO ARQUIVO FISICAMENTE
        salvar_dados()
        st.success(f"{len(novas_velas)} velas adicionadas e salvas!")
        st.rerun()

st.divider()

# --- BUSCA MANUAL DE SEQUÊNCIA ---
st.subheader("🔍 Localizar Sequência Manual")
col_input, col_btn = st.columns([3, 1])

with col_input:
    seq_input = st.text_input("Insira a sequência para busca", placeholder="Ex: 1.50, 2.00, 1.10")

if col_btn.button("🔍 BUSCAR", use_container_width=True):
    if seq_input:
        try:
            padrao_buscado = [float(x.strip()) for x in seq_input.replace(',', ' ').split()]
            n_seq = len(padrao_buscado)
            achou_manual = False
            
            for i in range(len(st.session_state.velas) - n_seq + 1):
                if st.session_state.velas[i:i+n_seq] == padrao_buscado:
                    st.success(f"✅ Padrão encontrado! Inicia na posição {i+1}")
                    achou_manual = True
            
            if not achou_manual:
                st.error("❌ Sequência não encontrada.")
        except:
            st.error("Formato inválido.")

st.divider()

# --- LÓGICA AUTOMÁTICA ---
if len(st.session_state.velas) < 25:
    st.warning("Mínimo de 25 velas necessárias no histórico.")
else:
    st.info("Aguardando detecção de novos padrões...")

st.divider()

# --- CONTADOR E VISUALIZAÇÃO ---
st.subheader("📊 Histórico (Tudo com x)")
total = len(st.session_state.velas)
st.header(f"{total} / 10.000")

# LISTA RÁPIDA (Últimas 10)
if total > 0:
    resumo_html = []
    for v in st.session_state.velas[-10:][::-1]:
        if v >= 8.0:
            resumo_html.append(f"<b style='color: #FF00FF; font-size: 1.2em;'>🔥 {v:.2f}x</b>")
        else:
            resumo_html.append(f"<span style='color: #BBBBBB;'>{v:.2f}x</span>")
    st.markdown(" | ".join(resumo_html), unsafe_allow_html=True)

# --- VER TODO O BANCO COM COR SÓ NAS VELAS > 8x ---
with st.expander("👁️ VER TODO O BANCO"):
    if total > 0:
        df_v = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
        
        def colorir_oito_x(val):
            # Apenas velas >= 8 ficam rosa choque
            color = '#FF00FF' if val >= 8.0 else '#FFFFFF'
            weight = 'bold' if val >= 8.0 else 'normal'
            return f'color: {color}; font-weight: {weight}'

        df_estilizado = df_v.style.applymap(colorir_oito_x, subset=['Vela']).format({"Vela": "{:.2f}x"})
        st.dataframe(df_estilizado, use_container_width=True, height=400)
    else: 
        st.write("Banco vazio.")

st.divider()

# --- RESET ---
st.subheader("⚙️ Configurações")
confirmar = st.checkbox("Confirmar: APAGAR TUDO?")
if st.button("🗑️ ZERAR HISTÓRICO AGORA", use_container_width=True):
    if confirmar:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.velas = [] 
        st.success("Tudo apagado!")
        st.rerun()
        
