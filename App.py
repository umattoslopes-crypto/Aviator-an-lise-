import streamlit as st
import re

# Configuração da página para celular
st.set_page_config(page_title="Aviator Master Bot", page_icon="✈️")

# Estilo visual das velas
def cor_vela(val):
    if val >= 10: return f'<div style="background-color: #ff00ff; color: white; padding: 5px; border-radius: 5px; margin: 2px; display: inline-block; font-weight: bold;">{val}x 🚀</div>'
    if val >= 2: return f'<div style="background-color: #32cd32; color: white; padding: 5px; border-radius: 5px; margin: 2px; display: inline-block; font-weight: bold;">{val}x</div>'
    return f'<div style="background-color: #ff4b4b; color: white; padding: 5px; border-radius: 5px; margin: 2px; display: inline-block;">{val}x</div>'

st.title("✈️ Aviator Smart Analyzer")

# Memória dos dados
if 'dados' not in st.session_state:
    st.session_state.dados = []

# --- 📥 MÓDULO DE IMPORTAÇÃO (LISTA GRANDE) ---
with st.expander("📥 Importar Lista de Velas (500+)", expanded=False):
    st.write("Se conseguir copiar os números do site, cole-os abaixo:")
    lista_texto = st.text_area("Cole aqui (ex: 1.54, 2.80, 10.5, 1.22...)")
    if st.button("Processar e Salvar Lista"):
        if lista_texto:
            # Puxa apenas os números, ignorando letras 'x', vírgulas ou espaços
            numeros = re.findall(r"[-+]?\d*\.\d+|\d+", lista_texto.replace(',', '.'))
            novos_dados = [float(n) for n in numeros]
            st.session_state.dados.extend(novos_dados)
            st.success(f"Sucesso! {len(novos_dados)} velas adicionadas.")
            st.rerun()

# --- ➕ MÓDULO DE ENTRADA MANUAL ---
st.markdown("---")
nova_vela = st.number_input("Última vela que saiu:", min_value=1.0, step=0.01)
if st.button("Adicionar Vela"):
    st.session_state.dados.append(nova_vela)
    st.success(f"Vela {nova_vela}x registrada!")

# --- 🎯 ANÁLISE E ALERTAS ---
if len(st.session_state.dados) >= 4:
    st.subheader("🎯 Alertas de Próximas Velas")
    # Analisa as últimas 3 velas para prever a próxima
    ultimas_3 = st.session_state.dados[-3:]
    st.write(f"Padrão atual: **{ultimas_3}**")
    
    encontrados = []
    for i in range(len(st.session_state.dados) - 4):
        if st.session_state.dados[i:i+3] == ultimas_3:
            proxima = st.session_state.dados[i+3]
            encontrados.append(proxima)
    
    if encontrados:
        for p in encontrados:
            if p >= 10:
                st.error(f"🚨 **ALERTA DE VELA ROSA!** Após esse padrão, já saiu uma vela de {p}x!")
            elif p >= 5:
                st.warning(f"🔥 **ALERTA DE VELA ALTA!** Possível vela de {p}x identificada no histórico.")
            else:
                st.info(f"✅ Padrão encontrado: Próxima foi {p}x.")
    else:
        st.write("Buscando repetição no histórico...")

# --- 📋 HISTÓRICO VISUAL ---
st.markdown("---")
st.subheader("📋 Histórico (Últimas 20)")
if st.session_state.dados:
    cols = st.columns(1)
    for v in reversed(st.session_state.dados[-20:]):
        st.markdown(cor_vela(v), unsafe_allow_html=True)
    
    if st.button("Limpar Histórico"):
        st.session_state.dados = []
        st.rerun()
