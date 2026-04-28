
import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Preditor High-Vela 10k", layout="wide")

ARQUIVO_HISTORICO = "banco_velas_permanente.csv"

# --- FUNÇÕES DE MEMÓRIA (NÃO RESETAR) ---
def carregar_dados():
    if os.path.exists(ARQUIVO_HISTORICO):
        df = pd.read_csv(ARQUIVO_HISTORICO)
        return df.to_dict('records')
    return []

def salvar_dados(lista_dicts):
    # Mantém apenas as últimas 10.000 velas para performance
    lista_dicts = lista_dicts[-10000:]
    df = pd.DataFrame(lista_dicts)
    df.to_csv(ARQUIVO_HISTORICO, index=False)
    return lista_dicts

# Inicializa o banco na sessão
if 'banco' not in st.session_state:
    st.session_state.banco = carregar_dados()

# --- INTERFACE ---
st.title("📈 Analisador de Padrões e Frequência 10k")

# --- BLOCO 1: ENTRADA DE DADOS (ATÉ 500 VELAS) ---
with st.expander("📥 ALIMENTAR BANCO DE DADOS", expanded=True):
    entrada = st.text_area("Cole as velas aqui (ex: 2.76, 1.05, 8.40...)", height=150)
    if st.button("GRAVAR VELAS NO HISTÓRICO"):
        if entrada:
            # REGEX que captura o número inteiro com decimais (Resolve o erro do 2.76)
            velas_encontradas = re.findall(r"\d+\.\d+|\d+", entrada.replace(",", "."))
            novos_registros = []
            agora = datetime.now().strftime("%H:%M")
            
            for v in velas_encontradas:
                novos_registros.append({"valor": float(v), "hora": agora})
            
            st.session_state.banco.extend(novos_registros)
            st.session_state.banco = salvar_dados(st.session_state.banco)
            st.success(f"✅ {len(novos_registros)} velas adicionadas! Total: {len(st.session_state.banco)}")
            st.rerun()

# --- BLOCO 2: BUSCA DE PADRÃO (ÚLTIMAS 10 VELAS) ---
st.markdown("---")
st.subheader("🔍 BUSCAR REPETIÇÃO")
col_input, col_btn = st.columns([4, 1])

with col_input:
    txt_busca = st.text_input("Cole as últimas 10 velas do jogo:")
with col_btn:
    buscar = st.button("BUSCAR AGORA")

if buscar and txt_busca:
    velas_busca = [float(v) for v in re.findall(r"\d+\.\d+|\d+", txt_busca.replace(",", "."))]
    
    if len(velas_busca) < 10:
        st.error("Por favor, insira pelo menos 10 velas para buscar o padrão.")
    else:
        valores_banco = [d['valor'] for d in st.session_state.banco]
        encontrou = False
        
        # Procura o padrão no histórico
        for i in range(len(valores_banco) - 20):
            if valores_banco[i : i+10] == velas_busca:
                encontrou = True
                st.markdown("### 🎯 PADRÃO IDENTIFICADO!")
                
                proximas = valores_banco[i+10 : i+20]
                cols = st.columns(10)
                
                for idx, v in enumerate(proximas):
                    pos = idx + 1
                    with cols[idx]:
                        # Alerta Velas > 8x
                        if v >= 8:
                            st.markdown(f"**G{pos}**")
                            st.markdown(f"<div style='background-color: #ff00ff; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;'>🔥 {v}x</div>", unsafe_allow_html=True)
                            if pos == 1:
                                st.warning("⚠️ ALERTA: VELA ALTA NA PRÓXIMA RODADA!")
                            else:
                                st.info(f"Vela > 8x em G{pos}")
                        else:
                            cor = "green" if v >= 2 else "red"
                            st.markdown(f"G{pos}")
                            st.markdown(f"<div style='color: {cor}; font-weight: bold;'>{v}x</div>", unsafe_allow_html=True)
        
        if not encontrou:
            st.warning("Este padrão exato não foi encontrado nas 10.000 velas anteriores.")

# --- BLOCO 3: GRÁFICO DE FREQUÊNCIA (VELAS > 8x) ---
st.markdown("---")
st.subheader("📊 FREQUÊNCIA DE VELAS > 8x POR HORÁRIO")

if st.session_state.banco:
    df_grafico = pd.DataFrame(st.session_state.banco)
    df_altas = df_grafico[df_grafico['valor'] >= 8].copy()
    
    if not df_altas.empty:
        # Conta quantas velas > 8x ocorreram em cada minuto/hora registrado
        freq = df_altas['hora'].value_counts().sort_index()
        st.bar_chart(freq)
    else:
        st.info("Ainda não há velas acima de 8x registradas para gerar o gráfico.")

# --- HISTÓRICO VISUAL ---
with st.expander("📋 VER TODO O HISTÓRICO (ÚLTIMAS 100)"):
    if st.session_state.banco:
        st.table(pd.DataFrame(st.session_state.banco).tail(100))
        if st.button("LIMPAR TODO O BANCO"):
            if os.path.exists(ARQUIVO_HISTORICO): os.remove(ARQUIVO_HISTORICO)
            st.session_state.banco = []
            st.rerun()
