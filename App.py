import streamlit as st
import re

st.set_page_config(page_title="Analisador Pro", page_icon="✈️")

def formatar_vela(val):
    if val >= 10: return f'<b style="color: #ff00ff;">{val}x</b>'
    if val >= 8: return f'<b style="color: #ffd700; font-size: 18px;">{val}x ⭐</b>'
    if val >= 2: return f'<b style="color: #00ff00;">{val}x</b>'
    return f'<b style="color: #ff4b4b;">{val}x</b>'

st.title("✈️ Analisador de Padrões")

if 'dados' not in st.session_state:
    st.session_state.dados = []

# --- 1. ÁREA DE IMPORTAÇÃO (ABERTA NO TOPO) ---
st.subheader("📥 Importar Lista (500 velas)")
texto_lista = st.text_area("Cole os números do site aqui:", height=100, help="Cole o histórico copiado do jogo")
if st.button("IMPORTAR TUDO", use_container_width=True):
    if texto_lista:
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", texto_lista.replace(',', '.'))
        st.session_state.dados.extend([float(n) for n in nums])
        st.success(f"{len(nums)} velas adicionadas!")

st.markdown("---")

# --- 2. ÁREA MANUAL ---
st.subheader("✍️ Entrada Manual")
col1, col2 = st.columns([3, 1])
with col1:
    nova_vela = st.number_input("Última vela:", min_value=1.0, step=0.01, key="input_vela")
with col2:
    if st.button("Salvar"):
        st.session_state.dados.append(nova_vela)
        st.rerun()

# --- 3. BOTÃO DE PROCURA ---
st.markdown("---")
if st.button("🔍 PROCURAR PADRÃO", use_container_width=True):
    if len(st.session_state.dados) >= 11:
        padrao_busca = st.session_state.dados[-10:]
        encontrou = False
        for i in range(len(st.session_state.dados) - 13):
            if st.session_state.dados[i:i+10] == padrao_busca:
                encontrou = True
                v1, v2, v3 = st.session_state.dados[i+10], st.session_state.dados[i+11], st.session_state.dados[i+12]
                st.subheader("🎯 SINAL IDENTIFICADO")
                for pos, v in enumerate([v1, v2, v3], 1):
                    if v >= 8:
                        distancia = "APÓS ESSA RODADA" if pos == 1 else f"DAQUI A {pos} RODADAS"
                        st.markdown(f'<div style="background-color: #ffd700; padding: 15px; border-radius: 10px; color: black; text-align: center; font-weight: bold; border: 2px solid black;">⚠️ {distancia}: VELA DE {v}x</div>', unsafe_allow_html=True)
        if not encontrou:
            st.warning("Padrão de 10 velas não encontrado.")
    else:
        st.error("Alimente com pelo menos 11 velas.")

# --- 4. HISTÓRICO ---
st.markdown("---")
if st.session_state.dados:
    st.subheader("📋 Histórico Registrado")
    velas_html = " | ".join([formatar_vela(v) for v in st.session_state.dados[-20:]])
    st.markdown(velas_html, unsafe_allow_html=True)
    if st.button("Limpar Tudo"):
        st.session_state.dados = []
        st.rerun()
