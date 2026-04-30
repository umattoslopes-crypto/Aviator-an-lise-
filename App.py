import streamlit as st
import pandas as pd
import os
import re

# --- PERSISTÊNCIA DE DADOS (NÃO APAGA AO SAIR) ---
DB_FILE = "historico_velas.csv"

if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.velas = pd.read_csv(DB_FILE)['velas'].tolist()
    else:
        st.session_state.velas = []

def salvar_dados():
    pd.DataFrame({'velas': st.session_state.velas}).to_csv(DB_FILE, index=False)

st.title("🤖 Analisador de Padrões - Crash")

# --- ÁREA DE ENTRADA INTELIGENTE (SEM DUPLICAR) ---
st.subheader("📥 Inserir Dados (Leitor de Prints/Manual)")
input_velas = st.text_area("Cole aqui o texto do leitor de prints:", placeholder="Ex: 9.34 1.20 5.00...", height=150)

if st.button("📥 PROCESSAR E ADICIONAR"):
    if input_velas:
        # Extrai todas as velas do texto (aceita ponto ou vírgula)
        novas_extraidas = [float(v) for v in re.findall(r"\d+\.\d+|\d+", input_velas.replace(',', '.'))]
        
        if novas_extraidas:
            # --- LÓGICA DE NÃO REPETIÇÃO ---
            # Pegamos as últimas 10 velas do banco para comparar
            ultimas_banco = st.session_state.velas[-10:]
            ponto_corte = 0
            
            # Procura onde a sequência do novo print começa a ser inédita
            for i in range(len(novas_extraidas)):
                fatia_nova = novas_extraidas[i:i+len(ultimas_banco)]
                if fatia_nova == ultimas_banco:
                    ponto_corte = i + len(ultimas_banco)
            
            velas_final = novas_extraidas[ponto_corte:]
            
            if velas_final:
                st.session_state.velas.extend(velas_final)
                st.session_state.velas = st.session_state.velas[-10000:]
                salvar_dados()
                st.success(f"Adicionadas {len(velas_final)} novas velas (ignorando repetidas).")
                st.rerun()
            else:
                st.info("Todas as velas deste print já estão no histórico.")

st.divider()

# --- BUSCA MANUAL DE SEQUÊNCIA ---
st.subheader("🔍 Localizar Sequência Manual")
col_input, col_btn = st.columns([3, 1])

with col_input:
    seq_input = st.text_input("Sequência alvo", placeholder="Ex: 1.50, 2.00")

if col_btn.button("🔍 BUSCAR"):
    if seq_input:
        try:
            padrao = [float(x.strip()) for x in seq_input.replace(',', ' ').split()]
            n = len(padrao)
            posicoes = [i+1 for i in range(len(st.session_state.velas)-n+1) if st.session_state.velas[i:i+n] == padrao]
            
            if posicoes:
                st.success(f"✅ Encontrado {len(posicoes)}x. Posições: {posicoes}")
            else:
                st.error("❌ Não encontrado.")
        except:
            st.error("Use apenas números.")

st.divider()

# --- VISUALIZAÇÃO COLORIDA (8x ROSA) ---
total = len(st.session_state.velas)
st.header(f"📊 {total} / 10.000 Velas")

if total > 0:
    resumo = []
    for v in st.session_state.velas[-12:][::-1]:
        cor = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#BBBBBB"
        resumo.append(f"<b style='color: {cor};'>{v:.2f}x</b>")
    st.markdown(" | ".join(resumo), unsafe_allow_html=True)

with st.expander("👁️ VER TODO O BANCO"):
    if total > 0:
        df_v = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
        def style_8x(val):
            return f'color: #FF00FF; font-weight: bold' if val >= 8.0 else 'color: white'
        
        st.dataframe(df_v.style.applymap(style_8x).format("{:.2f}x"), use_container_width=True, height=400)

st.divider()

# --- RESET ---
if st.checkbox("Confirmar exclusão total?"):
    if st.button("🗑️ ZERAR TUDO"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()
