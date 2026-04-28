
import streamlit as st
import re
import time

st.set_page_config(page_title="Aviator Predictor 10k", page_icon="✈️", layout="centered")

def formatar_vela(val):
    if val >= 100: return f'<b style="color: #ffffff; background-color: #4B0082; padding: 2px 5px; border-radius: 5px;">{val}x 💎</b>'
    if val >= 10: return f'<b style="color: #ff00ff;">{val}x 🚀</b>'
    if val >= 8: return f'<b style="color: #ffd700;">{val}x ⭐</b>'
    if val >= 2: return f'<b style="color: #00ff00;">{val}x</b>'
    return f'<b style="color: #ff4b4b;">{val}x</b>'

st.title("✈️ Analisador de Ciclos 10k")

# Inicializa o banco acumulativo
if 'banco' not in st.session_state:
    st.session_state.banco = []

# --- EXIBIÇÃO DO STATUS DO BANCO ---
st.info(f"📊 Inteligência: {len(st.session_state.banco)} velas armazenadas (Limite: 10.000)")

# --- 1. ÁREA DE IMPORTAÇÃO (ATÉ 500+) ---
with st.expander("📥 Importar Grande Remessa", expanded=True):
    texto_lista = st.text_area("Cole até 500 velas aqui para somar ao banco:")
    if st.button("ALIMENTAR BANCO DE DADOS", use_container_width=True):
        if texto_lista:
            nums = re.findall(r"[-+]?\d*\.\d+|\d+", texto_lista.replace(',', '.'))
            novas = [float(n) for n in nums]
            st.session_state.banco.extend(novas)
            # Trava o limite em 10.000 para performance
            st.session_state.banco = st.session_state.banco[-10000:]
            st.success(f"Sucesso! {len(novas)} velas somadas ao histórico.")
            st.rerun()

# --- 2. ENTRADA MANUAL ---
st.markdown("---")
col_m1, col_m2 = st.columns([2, 1])
with col_m1:
    v_manual = st.number_input("Última vela que saiu:", min_value=1.0, step=0.01, key="v_man")
with col_m2:
    if st.button("Salvar Vela", use_container_width=True):
        st.session_state.banco.append(v_manual)
        st.rerun()

# --- 3. BOTÃO DE BUSCA POR REPETIÇÃO ---
st.markdown("---")
if st.button("🔍 ACHAR PADRÃO E PREVER PRÓXIMAS", use_container_width=True):
    if len(st.session_state.banco) >= 21: # 10 padrão + 10 futuro + margem
        padrao_busca = st.session_state.banco[-10:]
        st.write(f"Buscando repetições para: `{padrao_busca}`")
        
        # Simula 10 segundos de análise para o "timing" de entrada
        with st.spinner('Analisando ciclos de repetição...'):
            time.sleep(1) # Delay técnico para organização visual
            
        encontrou = False
        # Percorre o banco de 10k velas
        for i in range(len(st.session_state.banco) - 21):
            if st.session_state.banco[i:i+10] == padrao_busca:
                encontrou = True
                # Escaneia as próximas 10 casas após o padrão
                futuro_10 = st.session_state.banco[i+10:i+20]
                
                st.subheader("🎯 CICLO ENCONTRADO NO HISTÓRICO")
                for pos, v in enumerate(futuro_10, 1):
                    if v >= 8:
                        dist = "PRÓXIMA VELA" if pos == 1 else f"EM {pos} RODADAS"
                        st.markdown(f'''
                        <div style="background-color: #ffd700; padding: 15px; border-radius: 10px; color: black; text-align: center; font-weight: bold; border: 3px solid black; margin-bottom: 10px;">
                            <h2 style="margin:0;">⚠️ {dist}</h2>
                            <h1 style="margin:0;">VELA ALTA DE {v}x</h1>
                        </div>
                        ''', unsafe_allow_html=True)
                    else:
                        st.write(f"Rodada {pos}: {v}x")
        
        if not encontrou:
            st.warning("Padrão de 10 velas não localizado nas 10.000 rodadas do banco.")
    else:
        st.error("Alimente o app com mais dados. Precisamos das últimas 10 velas para procurar.")

# --- 4. HISTÓRICO E LIMPEZA ---
st.markdown("---")
if st.session_state.banco:
    if st.button("🗑️ Resetar Banco de Dados"):
        st.session_state.banco = []
        st.rerun()
    
    st.subheader("📋 Últimas 20 Velas")
    velas_html = " | ".join([formatar_vela(v) for v in st.session_state.banco[-20:]])
    st.markdown(velas_html, unsafe_allow_html=True)
