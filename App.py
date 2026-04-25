import streamlit as st

# Configuração da página para parecer um App profissional
st.set_page_config(page_title="Aviator Predictor", page_icon="✈️", layout="centered")

# Estilo para cores de velas
def color_vela(val):
    if val >= 10: return f'<span style="color: #ff00ff; font-weight: bold;">{val}x (ROSA)</span>'
    if val >= 2: return f'<span style="color: #32cd32; font-weight: bold;">{val}x</span>'
    return f'<span style="color: #ff4b4b;">{val}x</span>'

st.title("✈️ Aviator Smart Analyzer")
st.markdown("---")

# Inicializar histórico
if 'dados' not in st.session_state:
    st.session_state.dados = []

# --- ENTRADA DE DADOS ---
st.subheader("📥 Alimentar Histórico")
col1, col2 = st.columns([3, 1])
with col1:
    nova_vela = st.number_input("Digite a última vela que saiu:", min_value=1.0, step=0.1, format="%.2f")
with col2:
    if st.button("Adicionar"):
        st.session_state.dados.append(nova_vela)

# --- ANÁLISE DE VELAS ALTAS ---
if len(st.session_state.dados) > 5:
    st.subheader("🎯 Próximas Velas e Alertas")
    
    # Lógica: Procurar o que aconteceu após as últimas 3 velas
    ultimas_3 = st.session_state.dados[-3:]
    st.write(f"Analisando padrão atual: **{ultimas_3}**")
    
    encontrou = False
    for i in range(len(st.session_state.dados) - 4):
        if st.session_state.dados[i:i+3] == ultimas_3:
            proxima = st.session_state.dados[i+3]
            encontrou = True
            
            # Alerta de Vela Alta
            if proxima >= 5:
                st.success(f"⚠️ **ALERTA DE VELA ALTA!** Na última vez que essa sequência saiu, a próxima vela foi **{proxima}x**.")
            else:
                st.info(f"Probabilidade da próxima vela ser: **{proxima}x**")
    
    if not encontrou:
        st.warning("Aguardando mais dados para identificar um padrão de vela alta.")

# --- EXIBIÇÃO DO HISTÓRICO ---
st.markdown("---")
st.subheader("📋 Últimas Coletadas")
cols = st.columns(5)
for idx, v in enumerate(reversed(st.session_state.dados[-10:])):
    cols[idx % 5].markdown(color_vela(v), unsafe_allow_html=True)
