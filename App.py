
import streamlit as st
import re
import time

# Configuração da página - Mantendo layout centrado
st.set_page_config(page_title="Aviator Predictor 10k", page_icon="✈️", layout="centered")

# Cores e Formatação - Mantendo o sistema de cores anterior
def formatar_vela(val):
    if val >= 100: return f'<b style="color: #ffffff; background-color: #4B0082; padding: 2px 5px; border-radius: 5px;">{val}x 💎</b>'
    if val >= 10: return f'<b style="color: #ff00ff;">{val}x 🚀</b>'
    if val >= 8: return f'<b style="color: #ffd700;">{val}x ⭐</b>'
    if val >= 2: return f'<b style="color: #00ff00;">{val}x</b>'
    return f'<b style="color: #ff4b4b;">{val}x</b>'

st.title("✈️ Analisador de Ciclos 10k")

# Inicializa o banco acumulativo (Sem apagar o que já existe)
if 'banco' not in st.session_state:
    st.session_state.banco = []

# Exibição do contador de banco de dados
st.info(f"📊 Inteligência: {len(st.session_state.banco)} velas armazenadas")

# --- 1. ÁREA DE IMPORTAÇÃO (CORREÇÃO DO NÚMERO ANTES DO PONTO) ---
with st.expander("📥 Importar Grande Remessa", expanded=True):
    texto_lista = st.text_area("Cole as velas aqui para somar ao banco:")
    if st.button("ALIMENTAR BANCO DE DADOS", use_container_width=True):
        if texto_lista:
            # CORREÇÃO AQUI: Captura o número inteiro e os decimais juntos
            # A regra busca: dígitos + (opcionalmente: ponto ou vírgula + dígitos)
            nums = re.findall(r"\d+[.,]?\d*", texto_lista)
            # Converte para float tratando vírgulas como pontos
            novas = [float(n.replace(',', '.')) for n in nums]
            
            st.session_state.banco.extend(novas)
            # Mantém o limite de 10.000 velas
            st.session_state.banco = st.session_state.banco[-10000:]
            st.success(f"Sucesso! {len(novas)} velas integradas corretamente (ex: 3.45).")
            st.rerun()

# --- 2. ENTRADA MANUAL (MANTIDA) ---
st.markdown("---")
col_m1, col_m2 = st.columns()
with col_m1:
    v_manual = st.number_input("Última vela:", min_value=1.0, step=0.01, key="v_man")
with col_m2:
    if st.button("Salvar Vela", use_container_width=True):
        st.session_state.banco.append(v_manual)
        st.rerun()

# --- 3. BUSCA POR REPETIÇÃO (ANTECIPAÇÃO DE 10 RODADAS) ---
st.markdown("---")
if st.button("🔍 ACHAR PADRÃO E PREVER PRÓXIMAS", use_container_width=True):
    if len(st.session_state.banco) >= 21:
        padrao_busca = st.session_state.banco[-10:]
        encontrou = False
        
        # Percorre o banco inteiro
        for i in range(len(st.session_state.banco) - 21):
            # Compara as 10 velas com o padrão atual
            if all(abs(st.session_state.banco[i+j] - padrao_busca[j]) < 0.01 for j in range(10)):
                encontrou = True
                # Pega as próximas 10 casas futuras do histórico
                futuro_10 = st.session_state.banco[i+10:i+20]
                
                st.subheader("🎯 CICLO ENCONTRADO")
                for pos, v in enumerate(futuro_10, 1):
                    # Alerta para velas acima de 8x (Destaque Dourado)
                    if v >= 8:
                        dist = "PRÓXIMA VELA" if pos == 1 else f"DAQUI A {pos} RODADAS"
                        st.markdown(f'''
                        <div style="background-color: #ffd700; padding: 15px; border-radius: 10px; color: black; text-align: center; font-weight: bold; border: 3px solid black; margin-bottom: 10px;">
                            <h2 style="margin:0;">⚠️ {dist}</h2>
                            <h1 style="margin:0;">VELA ALTA DE {v}x</h1>
                        </div>
                        ''', unsafe_allow_html=True)
                    else:
                        st.write(f"Rodada {pos} após o padrão: {v}x")
        
        if not encontrou:
            st.warning("Padrão de 10 velas não localizado nas 10.000 rodadas.")
    else:
        st.error("Alimente o app com pelo menos 11 velas para iniciar a busca.")

# --- 4. HISTÓRICO VISUAL (MANTIDO) ---
st.markdown("---")
if st.session_state.banco:
    if st.button("🗑️ Resetar Banco"):
        st.session_state.banco = []
        st.rerun()
    
    st.subheader("📋 Últimas 20 Velas")
    velas_html = " | ".join([formatar_vela(v) for v in st.session_state.banco[-20:]])
    st.markdown(velas_html, unsafe_allow_html=True)
