import streamlit as st
import re

st.set_page_config(page_title="Aviator Predictor Pro", page_icon="✈️")

def formatar_vela(val):
    if val >= 10: return f'<b style="color: #ff00ff;">{val}x</b>'
    if val >= 8: return f'<b style="color: #ffd700; font-size: 18px;">{val}x ⭐</b>'
    if val >= 2: return f'<b style="color: #00ff00;">{val}x</b>'
    return f'<b style="color: #ff4b4b;">{val}x</b>'

st.title("✈️ Analisador de Padrões")

if 'dados' not in st.session_state:
    st.session_state.dados = []

# --- INSERIR DADOS ---
st.subheader("📥 Alimentar Dados")
col1, col2 = st.columns([3, 1])

with col1:
    nova_vela = st.number_input("Última vela:", min_value=1.0, step=0.01, key="input_vela")
with col2:
    if st.button("Salvar"):
        st.session_state.dados.append(nova_vela)
        st.rerun()

# --- PROCURAR PADRÃO ---
st.markdown("---")
if st.button("🔍 PROCURAR PADRÃO", use_container_width=True):
    if len(st.session_state.dados) >= 11:
        # Usa as últimas 10 como base
        padrao_busca = st.session_state.dados[-10:]
        encontrou = False
        
        # Procura no histórico
        for i in range(len(st.session_state.dados) - 13):
            if st.session_state.dados[i:i+10] == padrao_busca:
                encontrou = True
                # Pega as 3 próximas
                v1, v2, v3 = st.session_state.dados[i+10], st.session_state.dados[i+11], st.session_state.dados[i+12]
                
                st.subheader("🎯 SINAL IDENTIFICADO")
                
                for pos, v in enumerate([v1, v2, v3], 1):
                    if v >= 8:
                        # Exibe a mensagem exatamente como você pediu
                        distancia = "APÓS ESSA RODADA" if pos == 1 else f"DAQUI A {pos} RODADAS"
                        st.markdown(f"""
                        <div style="background-color: #ffd700; padding: 20px; border-radius: 10px; border: 2px solid #b8860b; color: black; text-align: center;">
                            <h2 style="margin: 0;">⚠️ {distancia}</h2>
                            <h1 style="margin: 0;">VELA DE {v}x</h1>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.write(f"Rodada {pos}: {v}x")
        
        if not encontrou:
            st.warning("Padrão de 10 velas não localizado no histórico.")
    else:
        st.error("Insira pelo menos 11 velas para analisar.")

# --- HISTÓRICO ---
st.markdown("---")
if st.session_state.dados:
    st.subheader("📋 Histórico")
    velas_html = " | ".join([formatar_vela(v) for v in st.session_state.dados[-20:]])
    st.markdown(velas_html, unsafe_allow_html=True)
    if st.button("Limpar Tudo"):
        st.session_state.dados = []
        st.rerun()
