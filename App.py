
        
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
        try:
            df = pd.read_csv(ARQUIVO_HISTORICO)
            return df.to_dict('records')
        except:
            return []
    return []

def salvar_dados(lista_dicts):
    lista_dicts = lista_dicts[-10000:] # Limite rigoroso de 10k
    df = pd.DataFrame(lista_dicts)
    df.to_csv(ARQUIVO_HISTORICO, index=False)
    return lista_dicts

if 'banco' not in st.session_state:
    st.session_state.banco = carregar_dados()

# --- INTERFACE ---
st.title("📈 Analisador Pro: Histórico & Padrões")

# --- BLOCO 1: ENTRADA DE DADOS ---
with st.expander("📥 ADICIONAR NOVAS VELAS", expanded=True):
    entrada = st.text_area("Cole até 500 velas aqui:", height=100, placeholder="Ex: 2.76, 1.05, 8.40...")
    if st.button("GRAVAR NO HISTÓRICO"):
        if entrada:
            # Captura o número cheio (ex: 2.76) - Resolve erro do 2 virar 0
            velas_encontradas = re.findall(r"\d+\.\d+|\d+", entrada.replace(",", "."))
            novos_registros = []
            agora = datetime.now().strftime("%H:%M")
            
            for v in velas_encontradas:
                novos_registros.append({"valor": float(v), "hora": agora})
            
            st.session_state.banco.extend(novos_registros)
            st.session_state.banco = salvar_dados(st.session_state.banco)
            st.success(f"✅ Adicionadas {len(novos_registros)} velas!")
            st.rerun()

# --- BLOCO 2: BUSCA DE PADRÃO ---
st.markdown("---")
st.subheader("🔍 BUSCAR PADRÃO (ÚLTIMAS 10)")
col_input, col_btn = st.columns([3, 1])

with col_input:
    txt_busca = st.text_input("Insira as 10 velas para buscar repetição no banco:")
with col_btn:
    st.write(" ") # Alinhamento
    buscar = st.button("BUSCAR AGORA", use_container_width=True)

if buscar and txt_busca:
    velas_busca = [float(v) for v in re.findall(r"\d+\.\d+|\d+", txt_busca.replace(",", "."))]
    if len(velas_busca) < 10:
        st.error("Insira exatamente 10 velas.")
    else:
        valores_banco = [d['valor'] for d in st.session_state.banco]
        encontrou = False
        for i in range(len(valores_banco) - 20):
            if valores_banco[i : i+10] == velas_busca:
                encontrou = True
                st.success(f"🎯 PADRÃO LOCALIZADO NA POSIÇÃO {i}!")
                proximas = valores_banco[i+10 : i+20]
                cols = st.columns(10)
                for idx, v in enumerate(proximas):
                    pos = idx + 1
                    with cols[idx]:
                        cor = "#ff00ff" if v >= 8 else ("#00ff00" if v >= 2 else "#ff4b4b")
                        st.markdown(f"**G{pos}**")
                        st.markdown(f"<div style='background-color: {cor}; color: white; padding: 5px; border-radius: 5px; text-align: center; font-weight: bold;'>{v:.2f}x</div>", unsafe_allow_html=True)
        if not encontrou:
            st.warning("Padrão não encontrado nas velas acumuladas.")

# --- BLOCO 3: CONTADOR E HISTÓRICO VISUAL ---
st.markdown("---")
total_atual = len(st.session_state.banco)
percentual = min(total_atual / 10000, 1.0)

col_cont, col_hist = st.columns([1, 3])

with col_cont:
    st.subheader("📊 Contador")
    st.metric("Velas Acumuladas", f"{total_atual} / 10.000")
    st.progress(percentual)
    if total_atual >= 10000:
        st.success("🎯 Banco de 10k Completo!")
    else:
        st.info(f"Faltam {10000 - total_atual} velas.")

with col_hist:
    st.subheader("📋 Últimas 100 Velas")
    if st.session_state.banco:
        ultimas_100 = st.session_state.banco[-100:]
        html_velas = []
        for d in reversed(ultimas_100):
            v = d['valor']
            # Cores: Vermelho < 2 | Verde >= 2 | Rosa >= 10
            cor = "#ff4b4b" if v < 2 else ("#00ff00" if v < 10 else "#ff00ff")
            html_velas.append(f'<span style="color: {cor}; font-weight: bold; border: 1px solid #444; padding: 3px 8px; border-radius: 5px; margin: 3px; display: inline-block; background: #262730;">{v:.2f}x</span>')
        
        st.markdown(f'<div style="line-height: 2.5; max-height: 300px; overflow-y: auto;">{" ".join(html_velas)}</div>', unsafe_allow_html=True)

# --- BLOCO 4: LIMPEZA ---
st.markdown("---")
if st.button("🗑️ RESETAR BANCO DE DADOS"):
    if os.path.exists(ARQUIVO_HISTORICO): os.remove(ARQUIVO_HISTORICO)
    st.session_state.banco = []
    st.rerun()
     
