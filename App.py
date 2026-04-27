
import streamlit as st
import re

st.set_page_config(page_title="Aviator Data 10k", page_icon="✈️")

# Estilos de velas para o histórico
def formatar_vela(val):
    if val >= 10: return f'<b style="color: #ff00ff;">{val}x</b>'
    if val >= 5: return f'<b style="color: #ffd700;">{val}x ⭐</b>'
    if val >= 2: return f'<b style="color: #00ff00;">{val}x</b>'
    return f'<b style="color: #ff4b4b;">{val}x</b>'

st.title("✈️ Analisador de Ciclos 10k")

# Inicializa o banco de dados se não existir
if 'banco_dados' not in st.session_state:
    st.session_state.banco_dados = []

# --- 1. PAINEL DE CONTROLE DO BANCO ---
st.subheader(f"📊 Banco de Dados: {len(st.session_state.banco_dados)} velas")

# Campo para colar novas remessas
texto_import = st.text_area("Cole novas velas para ACUMULAR no banco:", height=100)

col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("➕ ADICIONAR AO BANCO", use_container_width=True):
        if texto_import:
            # Extrai apenas os números
            novos_nums = re.findall(r"[-+]?\d*\.\d+|\d+", texto_import.replace(',', '.'))
            lista_novos = [float(n) for n in novos_nums]
            # O SEGREDO: .extend adiciona sem apagar o que já existe
            st.session_state.banco_dados.extend(lista_novos)
            st.success(f"Mais {len(lista_novos)} velas salvas!")
            st.rerun()

with col_b2:
    if st.button("🗑️ LIMPAR TUDO", use_container_width=True):
        st.session_state.banco_dados = []
        st.rerun()

st.markdown("---")

# --- 2. ENTRADA MANUAL (TEMPO REAL) ---
st.subheader("✍️ Registro Manual")
c1, c2 = st.columns([3, 1])
with c1:
    v_manual = st.number_input("Última vela:", min_value=1.0, step=0.01, key="v_man")
with c2:
    if st.button("Salvar"):
        st.session_state.banco_dados.append(v_manual)
        st.rerun()

# --- 3. PROCURAR PADRÃO (BUSCA EM TODO O BANCO) ---
st.markdown("---")
if st.button("🔍 PROCURAR PADRÃO NAS 10k VELAS", use_container_width=True):
    # Precisamos de 10 para o padrão e olhamos até 3 no futuro
    if len(st.session_state.banco_dados) >= 13:
        padrao_atual = st.session_state.banco_dados[-10:]
        encontrou = False
        
        # Percorre o banco inteiro acumulado
        for i in range(len(st.session_state.banco_dados) - 13):
            if st.session_state.banco_dados[i:i+10] == padrao_atual:
                encontrou = True
                v1, v2, v3 = st.session_state.banco_dados[i+10], st.session_state.banco_dados[i+11], st.session_state.banco_dados[i+12]
                
                st.subheader("🎯 PADRÃO IDENTIFICADO")
                for pos, v in enumerate([v1, v2, v3], 1):
                    if v >= 5:
                        msg = "APÓS ESSA RODADA" if pos == 1 else f"DAQUI A {pos} RODADAS"
                        cor = "#ffd700" if v < 10 else "#ff00ff"
                        st.markdown(f'''
                        <div style="background-color: {cor}; padding: 15px; border-radius: 10px; color: black; text-align: center; font-weight: bold; border: 2px solid black; margin-bottom: 8px;">
                            ⚠️ {msg}: VELA DE {v}x
                        </div>
                        ''', unsafe_allow_html=True)
                    else:
                        st.write(f"Rodada {pos} após padrão: {v}x")
        
        if not encontrou:
            st.warning("Padrão de 10 velas não encontrado no seu banco acumulado.")
    else:
        st.error("Alimente o banco com pelo menos 13 velas.")

# --- 4. HISTÓRICO VISUAL ---
st.markdown("---")
if st.session_state.banco_dados:
    st.write("📋 **Últimas 20 velas do banco:**")
    h_html = " | ".join([formatar_vela(v) for v in st.session_state.banco_dados[-20:]])
    st.markdown(h_html, unsafe_allow_html=True)
