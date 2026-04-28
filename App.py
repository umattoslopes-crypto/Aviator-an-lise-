
import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Preditor High-Vela 10k", layout="wide")

ARQUIVO_HISTORICO = "banco_velas_permanente.csv"

# --- FUNÇÕES DE MEMÓRIA ---
def carregar_dados():
    if os.path.exists(ARQUIVO_HISTORICO):
        df = pd.read_csv(ARQUIVO_HISTORICO)
        return df.to_dict('records')
    return []

def salvar_dados(lista_dicts):
    lista_dicts = lista_dicts[-10000:] # Limite de 10k
    df = pd.DataFrame(lista_dicts)
    df.to_csv(ARQUIVO_HISTORICO, index=False)
    return lista_dicts

if 'banco' not in st.session_state:
    st.session_state.banco = carregar_dados()

# --- INTERFACE ---
st.title("📈 Analisador de Padrões (Fiel ao Jogo)")

# --- BLOCO 1: ENTRADA DE DADOS ---
with st.expander("📥 ADICIONAR NOVAS VELAS (ATÉ 500)", expanded=True):
    entrada = st.text_area("Cole as velas aqui:", height=120, placeholder="Ex: 2.76, 1.05, 8.40...")
    if st.button("GRAVAR NO HISTÓRICO"):
        if entrada:
            # Captura o número cheio (ex: 2.76)
            velas_encontradas = re.findall(r"\d+\.\d+|\d+", entrada.replace(",", "."))
            novos_registros = []
            agora = datetime.now().strftime("%H:%M")
            
            for v in velas_encontradas:
                novos_registros.append({"valor": float(v), "hora": agora})
            
            st.session_state.banco.extend(novos_registros)
            st.session_state.banco = salvar_dados(st.session_state.banco)
            st.success(f"✅ Adicionadas! Total no sistema: {len(st.session_state.banco)}")
            st.rerun()

# --- BLOCO 2: BUSCA DE PADRÃO ---
st.markdown("---")
st.subheader("🔍 BUSCAR PADRÃO (ÚLTIMAS 10)")
col_input, col_btn = st.columns([3,1])

with col_input:
    txt_busca = st.text_input("Insira o padrão de 10 velas:")
with col_btn:
    buscar = st.button("BUSCAR AGORA", use_container_width=True)

if buscar and txt_busca:
    velas_busca = [float(v) for v in re.findall(r"\d+\.\d+|\d+", txt_busca.replace(",", "."))]
    
    if len(velas_busca) < 10:
        st.error("Insira 10 velas.")
    else:
        valores_banco = [d['valor'] for d in st.session_state.banco]
        encontrou = False
        
        for i in range(len(valores_banco) - 20):
            if valores_banco[i : i+10] == velas_busca:
                encontrou = True
                st.markdown("### 🎯 PADRÃO LOCALIZADO!")
                proximas = valores_banco[i+10 : i+20]
                cols = st.columns(10)
                
                for idx, v in enumerate(proximas):
                    pos = idx + 1
                    with cols[idx]:
                        cor = "#ff00ff" if v >= 8 else ("#00ff00" if v >= 2 else "#ff4b4b")
                        st.markdown(f"**G{pos}**")
                        st.markdown(f"<div style='background-color: {cor}; color: white; padding: 5px; border-radius: 5px; text-align: center; font-weight: bold;'>{v:.2f}x</div>", unsafe_allow_html=True)
        if not encontrou:
            st.warning("Padrão não encontrado no histórico.")

# --- BLOCO 3: HISTÓRICO DAS ÚLTIMAS 100 (FIEL AO JOGO) ---
st.markdown("---")
st.subheader("📋 ÚLTIMAS 100 VELAS ADICIONADAS")

if st.session_state.banco:
    # Pegamos as últimas 100 velas do banco
    ultimas_100 = st.session_state.banco[-100:]
    
    # Criamos uma linha visual com as velas formatadas com "x"
    html_velas = []
    for d in reversed(ultimas_100): # Mostra da mais nova para a mais antiga
        v = d['valor']
        cor = "#ff4b4b" if v < 2 else ("#00ff00" if v < 10 else "#ff00ff")
        html_velas.append(f'<span style="color: {cor}; font-weight: bold; border: 1px solid #333; padding: 2px 6px; border-radius: 4px; margin: 2px; display: inline-block;">{v:.2f}x</span>')
    
    st.markdown(f'<div style="line-height: 2.5;">{" ".join(html_velas)}</div>', unsafe_allow_html=True)

# --- BLOCO 4: GRÁFICO DE 8x ---
st.markdown("---")
st.subheader("📊 FREQUÊNCIA DE VELAS > 8x")
df_grafico = pd.DataFrame(st.session_state.banco)
if not df_grafico.empty:
    df_altas = df_grafico[df_grafico['valor'] >= 8]
    if not df_altas.empty:
        st.bar_chart(df_altas['hora'].value_counts())

if st.button("🗑️ RESETAR TUDO"):
    if os.path.exists(ARQUIVO_HISTORICO): os.remove(ARQUIVO_HISTORICO)
    st.session_state.banco = []
    st.rerun()
