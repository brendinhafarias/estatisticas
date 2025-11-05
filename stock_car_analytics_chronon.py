import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import json
import re
from datetime import datetime
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Stock Car Analytics Pro v2.0",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Base de dados atualizada com informações do Chronon.com.br
MAPEAMENTO_EQUIPES_MONTADORAS = {
    "Daniel Serra": {"Equipe": "Eurofarma-RC", "Montadora": "Chevrolet", "Numero": "29"},
    "Bruno Baptista": {"Equipe": "RCM Motorsport", "Montadora": "Toyota", "Numero": "44"},
    "Gabriel Casagrande": {"Equipe": "A.Mattheis Vogel", "Montadora": "Volkswagen", "Numero": "83"},
    "Guilherme Salas": {"Equipe": "KTF Racing", "Montadora": "Chevrolet", "Numero": "85"},
    "Cesar Ramos": {"Equipe": "Ipiranga Racing", "Montadora": "Toyota", "Numero": "30"},
    "Enzo Elias": {"Equipe": "Crown Racing", "Montadora": "Toyota", "Numero": "28"},
    "Thiago Camilo": {"Equipe": "Ipiranga Racing", "Montadora": "Toyota", "Numero": "21"},
    "Lucas Foresti": {"Equipe": "A.Mattheis Vogel", "Montadora": "Volkswagen", "Numero": "12"},
    "Felipe Massa": {"Equipe": "TMG Racing", "Montadora": "Chevrolet", "Numero": "19"},
    "Rubens Barrichello": {"Equipe": "Full Time", "Montadora": "Toyota", "Numero": "111"},
    "Cacá Bueno": {"Equipe": "KTF Sports", "Montadora": "Chevrolet", "Numero": "0"},
    "Felipe Fraga": {"Equipe": "Blau Motorsport", "Montadora": "Volkswagen", "Numero": "8"},
    "Ricardo Zonta": {"Equipe": "RMatheus", "Montadora": "Toyota", "Numero": "10"},
    "Gaetano di Mauro": {"Equipe": "Cavaleiro Sports", "Montadora": "Chevrolet", "Numero": "77"},
    "Nelson Piquet Jr": {"Equipe": "Cavaleiro Sports", "Montadora": "Chevrolet", "Numero": "33"},
    "Átila Abreu": {"Equipe": "Pole Motorsport", "Montadora": "Toyota", "Numero": "51"},
    "Ricardo Maurício": {"Equipe": "Eurofarma-RC", "Montadora": "Chevrolet", "Numero": "18"},
    "Allam Khodair": {"Equipe": "Blau Motorsport", "Montadora": "Volkswagen", "Numero": "80"},
}

# Pistas oficiais baseadas no Chronon.com.br
PISTAS_OFICIAIS = {
    "Goiânia": {"distancia": 3.835, "setores": 3, "drs_zones": 1},
    "Velocitta": {"distancia": 3.150, "setores": 3, "drs_zones": 2},
    "Interlagos": {"distancia": 4.309, "setores": 3, "drs_zones": 2},
    "Cascavel": {"distancia": 3.458, "setores": 3, "drs_zones": 1},
    "Velopark": {"distancia": 3.068, "setores": 3, "drs_zones": 2},
    "Belo Horizonte": {"distancia": 3.067, "setores": 3, "drs_zones": 1},
    "Buenos Aires": {"distancia": 4.200, "setores": 3, "drs_zones": 2},
    "Uruguai": {"distancia": 3.200, "setores": 3, "drs_zones": 1}
}

# Sessões oficiais baseadas no Chronon.com.br
SESSOES_OFICIAIS = [
    "Treino Rookies", "Shake Down", "T1", "T2", 
    "Q1-G1", "Q1-G2", "Q2", "Q3", "QF", 
    "Prova1 Sprint", "P2", "Warm Up"
]

# Temporadas disponíveis no Chronon
TEMPORADAS_DISPONIVEIS = ["2020", "2021", "2022", "2023", "2024", "2025"]

def processar_csv_chronon(uploaded_file):
    """Processa CSV no formato oficial do Chronon.com.br"""
    df = pd.read_csv(uploaded_file)

    # Identificar linhas com padrão de piloto (número - nome - categoria)
    pattern_rows = df.iloc[:, 0].astype(str).str.match(r'^\d+ - .+ - Stock Car PRO \d{4}$', na=False)
    pattern_indices = df.index[pattern_rows].tolist()

    # Criar lista para armazenar dados processados
    dados_processados = []

    for i, start_idx in enumerate(pattern_indices):
        # Extrair informações da linha padrão
        info_linha = df.iloc[start_idx, 0]
        partes = info_linha.split(' - ')
        numero_carro = partes[0]
        nome_piloto = partes[1]
        categoria = partes[2]

        # Determinar fim dos dados deste piloto
        end_idx = pattern_indices[i + 1] if i + 1 < len(pattern_indices) else len(df)

        # Extrair dados de voltas do piloto
        dados_piloto = df.iloc[start_idx + 1:end_idx].copy()

        if not dados_piloto.empty:
            dados_piloto['Numero_Carro'] = numero_carro
            dados_piloto['Nome_Piloto'] = nome_piloto
            dados_piloto['Categoria'] = categoria

            # Adicionar informações de equipe e montadora
            piloto_info = MAPEAMENTO_EQUIPES_MONTADORAS.get(nome_piloto, {})
            dados_piloto['Equipe'] = piloto_info.get('Equipe', 'Desconhecida')
            dados_piloto['Montadora'] = piloto_info.get('Montadora', 'Desconhecida')

            dados_processados.append(dados_piloto)

    if dados_processados:
        df_final = pd.concat(dados_processados, ignore_index=True)
        return df_final

    return pd.DataFrame()

def converter_tempo_chronon(tempo_str):
    """Converte tempo no formato do Chronon (1:23.253) para segundos"""
    try:
        if pd.isna(tempo_str) or tempo_str == '' or 'No Time' in str(tempo_str):
            return None

        tempo_str = str(tempo_str).strip().replace(',', '.')

        if ':' in tempo_str:
            partes = tempo_str.split(':')
            minutos = int(partes[0])
            segundos = float(partes[1])
            return minutos * 60 + segundos

        return float(tempo_str)
    except:
        return None

def calcular_metricas_avancadas(df):
    """Calcula métricas avançadas baseadas nos dados do Chronon"""
    if df.empty:
        return {}

    # Converter colunas numéricas do Chronon
    df_calc = df.copy()

    # Colunas de tempo
    if 'Lap Tm' in df.columns:
        df_calc['Lap_Time_Sec'] = df_calc['Lap Tm'].apply(converter_tempo_chronon)
    if 'S1 Tm' in df.columns:
        df_calc['S1_Sec'] = df_calc['S1 Tm'].apply(converter_tempo_chronon)
    if 'S2 Tm' in df.columns:
        df_calc['S2_Sec'] = df_calc['S2 Tm'].apply(converter_tempo_chronon)
    if 'S3 Tm' in df.columns:
        df_calc['S3_Sec'] = df_calc['S3 Tm'].apply(converter_tempo_chronon)

    # Velocidade
    if 'Speed' in df.columns:
        df_calc['Speed_Kmh'] = pd.to_numeric(df_calc['Speed'].astype(str).str.replace(',', '.'), errors='coerce')

    # Speed trap
    if 'SPT' in df.columns:
        df_calc['Speed_Trap'] = pd.to_numeric(df_calc['SPT'].astype(str).str.replace(',', '.'), errors='coerce')

    return df_calc

def formatar_tempo_chronon(segundos):
    """Formata tempo no padrão do Chronon"""
    if pd.isna(segundos) or segundos is None:
        return 'N/A'

    minutos = int(segundos // 60)
    segundos_restantes = segundos % 60

    if minutos > 0:
        return f"{minutos}:{segundos_restantes:06.3f}"
    else:
        return f"{segundos_restantes:.3f}s"

def gerar_analise_speed_trap(df):
    """Análise específica de speed trap baseada nos dados do Chronon"""
    if 'Speed_Trap' not in df.columns:
        return None

    speed_trap_stats = df.groupby('Nome_Piloto').agg({
        'Speed_Trap': ['max', 'mean', 'std'],
        'Lap_Time_Sec': 'min',
        'Equipe': 'first',
        'Montadora': 'first'
    }).round(3)

    speed_trap_stats.columns = ['_'.join(col).strip() for col in speed_trap_stats.columns]
    speed_trap_stats = speed_trap_stats.reset_index()

    return speed_trap_stats

def gerar_analise_setorial_avancada(df):
    """Análise setorial detalhada com dados do Chronon"""
    if not all(col in df.columns for col in ['S1_Sec', 'S2_Sec', 'S3_Sec']):
        return None

    # Melhores setores por piloto
    setores_stats = df.groupby('Nome_Piloto').agg({
        'S1_Sec': ['min', 'mean'],
        'S2_Sec': ['min', 'mean'], 
        'S3_Sec': ['min', 'mean'],
        'Lap_Time_Sec': 'min',
        'Equipe': 'first',
        'Montadora': 'first'
    }).round(3)

    setores_stats.columns = ['_'.join(col).strip() for col in setores_stats.columns]
    setores_stats = setores_stats.reset_index()

    # Identificar melhor setor de cada piloto
    setores_stats['Melhor_Setor'] = setores_stats.apply(lambda row: 
        np.argmin([row['S1_Sec_min'], row['S2_Sec_min'], row['S3_Sec_min']]) + 1, axis=1)

    return setores_stats

# Interface principal
st.title("🏎️ Stock Car Analytics Pro v2.0")
st.markdown("### Sistema Oficial baseado em dados do Chronon.com.br")

# Inicializar session state
if 'dados_etapas_v2' not in st.session_state:
    st.session_state.dados_etapas_v2 = {}
if 'dados_referencia_v2' not in st.session_state:
    st.session_state.dados_referencia_v2 = {}

# Sidebar para navegação
st.sidebar.title("🏁 Navegação Chronon")

secao = st.sidebar.selectbox(
    "Escolha a seção:",
    ["📥 Importação Chronon CSV", "🏆 Dashboard Oficial", "⚡ Análise Speed Trap", 
     "📊 Análise Setorial Pro", "🔄 Comparação Temporal", "📈 Rankings Avançados",
     "🎯 Sistema de Referências", "📋 Relatórios Executivos"]
)

if secao == "📥 Importação Chronon CSV":
    st.header("📥 Importação de Dados Oficiais Chronon")

    st.info("💡 Este sistema processa arquivos CSV no formato oficial do Chronon.com.br da Audace Tech")

    col1, col2 = st.columns(2)

    with col1:
        temporada_chronon = st.selectbox("Temporada:", TEMPORADAS_DISPONIVEIS, index=4)  # Default 2024
        etapa_chronon = st.text_input("Etapa (ex: #3 Interlagos):", "")
        sessao_chronon = st.selectbox("Sessão:", SESSOES_OFICIAIS)

    with col2:
        pista_chronon = st.selectbox("Pista:", list(PISTAS_OFICIAIS.keys()))
        uploaded_file_chronon = st.file_uploader("Arquivo CSV Oficial:", type=['csv'])

    if uploaded_file_chronon and etapa_chronon:
        df_chronon = processar_csv_chronon(uploaded_file_chronon)

        if not df_chronon.empty:
            # Calcular métricas avançadas
            df_chronon = calcular_metricas_avancadas(df_chronon)

            # Salvar dados na session
            chave_etapa = f"{temporada_chronon}_{etapa_chronon}_{sessao_chronon}"
            st.session_state.dados_etapas_v2[chave_etapa] = {
                'dataframe': df_chronon,
                'temporada': temporada_chronon,
                'etapa': etapa_chronon,
                'sessao': sessao_chronon,
                'pista': pista_chronon,
                'dados_pista': PISTAS_OFICIAIS[pista_chronon]
            }

            st.success(f"✅ Dados Chronon importados: {temporada_chronon} - {etapa_chronon} - {sessao_chronon}")

            # Preview dos dados Chronon
            st.subheader("👀 Preview dos Dados Chronon")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Pilotos", len(df_chronon['Nome_Piloto'].unique()))

            with col2:
                st.metric("Voltas Registradas", len(df_chronon))

            with col3:
                if 'Speed_Trap' in df_chronon.columns:
                    max_speed = df_chronon['Speed_Trap'].max()
                    st.metric("Vel. Máxima", f"{max_speed:.1f} km/h")

            with col4:
                if 'Lap_Time_Sec' in df_chronon.columns:
                    melhor_volta = df_chronon['Lap_Time_Sec'].min()
                    st.metric("Melhor Volta", formatar_tempo_chronon(melhor_volta))

            # Tabela de preview
            with st.expander("Ver dados detalhados do Chronon"):
                colunas_mostrar = ['Nome_Piloto', 'Equipe', 'Montadora', 'Lap Tm', 'Speed', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT']
                colunas_existentes = [col for col in colunas_mostrar if col in df_chronon.columns]
                st.dataframe(df_chronon[colunas_existentes].head(20))

elif secao == "🏆 Dashboard Oficial":
    st.header("🏆 Dashboard Oficial Stock Car")

    if not st.session_state.dados_etapas_v2:
        st.warning("⚠️ Importe dados do Chronon primeiro")
    else:
        # Seletor de etapa
        etapas_v2 = list(st.session_state.dados_etapas_v2.keys())
        etapa_dash = st.selectbox("Selecione a Etapa Chronon:", etapas_v2)

        dados_etapa = st.session_state.dados_etapas_v2[etapa_dash]
        df = dados_etapa['dataframe']
        pista_info = dados_etapa['dados_pista']

        st.subheader(f"📊 {dados_etapa['etapa']} - {dados_etapa['sessao']} ({dados_etapa['pista']})")
        st.write(f"**Distância da pista:** {pista_info['distancia']} km | **Setores:** {pista_info['setores']} | **DRS Zones:** {pista_info['drs_zones']}")

        if 'Lap_Time_Sec' in df.columns:
            # Melhores voltas por piloto
            melhores_voltas = df.dropna(subset=['Lap_Time_Sec']).groupby('Nome_Piloto').agg({
                'Lap_Time_Sec': 'min',
                'Speed_Kmh': 'max',
                'Speed_Trap': 'max',
                'Equipe': 'first',
                'Montadora': 'first'
            }).reset_index()

            melhores_voltas = melhores_voltas.sort_values('Lap_Time_Sec')
            melhores_voltas['Posicao'] = range(1, len(melhores_voltas) + 1)

            # Gráfico principal de tempos
            fig_oficial = go.Figure()

            # Cores por montadora
            cores_mont = {'Chevrolet': '#FFD700', 'Toyota': '#DC143C', 'Volkswagen': '#4682B4'}

            fig_oficial.add_trace(go.Bar(
                x=melhores_voltas['Nome_Piloto'],
                y=melhores_voltas['Lap_Time_Sec'],
                text=[formatar_tempo_chronon(t) for t in melhores_voltas['Lap_Time_Sec']],
                textposition='outside',
                marker_color=[cores_mont.get(m, '#808080') for m in melhores_voltas['Montadora']],
                name='Melhores Tempos Oficiais'
            ))

            fig_oficial.update_layout(
                title=f'🏁 Classificação Oficial - {dados_etapa["etapa"]}',
                xaxis_title='Pilotos',
                yaxis_title='Tempo (segundos)',
                height=600,
                showlegend=False
            )

            st.plotly_chart(fig_oficial, use_container_width=True)

            # Tabela oficial
            st.subheader("📋 Classificação Detalhada")

            tabela_oficial = melhores_voltas.copy()
            tabela_oficial['Tempo'] = [formatar_tempo_chronon(t) for t in tabela_oficial['Lap_Time_Sec']]
            tabela_oficial['Vel. Média'] = [f"{v:.1f} km/h" if pd.notna(v) else "N/A" for v in tabela_oficial['Speed_Kmh']]
            tabela_oficial['Speed Trap'] = [f"{v:.1f} km/h" if pd.notna(v) else "N/A" for v in tabela_oficial['Speed_Trap']]

            # Delta pro líder
            tempo_lider = melhores_voltas.iloc[0]['Lap_Time_Sec']
            tabela_oficial['Delta'] = [
                "Líder" if i == 0 else f"+{(tempo - tempo_lider):.3f}s"
                for i, tempo in enumerate(tabela_oficial['Lap_Time_Sec'])
            ]

            colunas_tabela = ['Posicao', 'Nome_Piloto', 'Equipe', 'Montadora', 'Tempo', 'Delta', 'Vel. Média', 'Speed Trap']
            st.dataframe(tabela_oficial[colunas_tabela], hide_index=True)

elif secao == "⚡ Análise Speed Trap":
    st.header("⚡ Análise Detalhada de Speed Trap")

    if not st.session_state.dados_etapas_v2:
        st.warning("⚠️ Importe dados do Chronon primeiro")
    else:
        etapas_v2 = list(st.session_state.dados_etapas_v2.keys())
        etapa_speed = st.selectbox("Etapa para Speed Trap:", etapas_v2, key="speed_trap")

        dados_etapa = st.session_state.dados_etapas_v2[etapa_speed]
        df = dados_etapa['dataframe']

        if 'Speed_Trap' in df.columns:
            speed_analysis = gerar_analise_speed_trap(df)

            if speed_analysis is not None:
                # Gráfico de speed trap por montadora
                fig_speed = px.box(
                    df.dropna(subset=['Speed_Trap']), 
                    x='Montadora', 
                    y='Speed_Trap',
                    color='Montadora',
                    color_discrete_map={'Chevrolet': '#FFD700', 'Toyota': '#DC143C', 'Volkswagen': '#4682B4'},
                    title='📊 Distribuição de Velocidade no Speed Trap por Montadora'
                )

                fig_speed.update_layout(height=500)
                st.plotly_chart(fig_speed, use_container_width=True)

                # Top velocidades
                st.subheader("🚀 Top Velocidades Speed Trap")

                top_speeds = speed_analysis.sort_values('Speed_Trap_max', ascending=False).head(10)

                col1, col2 = st.columns(2)

                with col1:
                    for i, row in top_speeds.iterrows():
                        st.write(f"**{row['Nome_Piloto']}** ({row['Montadora_first']}) - {row['Speed_Trap_max']:.1f} km/h")

                with col2:
                    # Gráfico de barras das top speeds
                    fig_top = go.Figure()
                    fig_top.add_trace(go.Bar(
                        x=top_speeds['Nome_Piloto'],
                        y=top_speeds['Speed_Trap_max'],
                        text=[f"{v:.1f}" for v in top_speeds['Speed_Trap_max']],
                        textposition='outside'
                    ))
                    fig_top.update_layout(title="Top 10 Speed Trap", height=400)
                    st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.info("💡 Dados de Speed Trap não disponíveis nesta sessão")

elif secao == "📊 Análise Setorial Pro":
    st.header("📊 Análise Setorial Profissional")

    if not st.session_state.dados_etapas_v2:
        st.warning("⚠️ Importe dados do Chronon primeiro")
    else:
        etapas_v2 = list(st.session_state.dados_etapas_v2.keys())
        etapa_setor = st.selectbox("Etapa para Análise Setorial:", etapas_v2, key="setorial")

        dados_etapa = st.session_state.dados_etapas_v2[etapa_setor]
        df = dados_etapa['dataframe']

        analise_setores = gerar_analise_setorial_avancada(df)

        if analise_setores is not None:
            # Heatmap de setores
            st.subheader("🔥 Mapa de Calor - Performance Setorial")

            # Preparar dados para heatmap
            heatmap_data = analise_setores[['Nome_Piloto', 'S1_Sec_min', 'S2_Sec_min', 'S3_Sec_min']].set_index('Nome_Piloto')

            fig_heatmap = px.imshow(
                heatmap_data.T,
                text_auto='.3f',
                aspect='auto',
                title='Melhores Tempos por Setor (mais escuro = mais rápido)',
                labels={'x': 'Pilotos', 'y': 'Setores', 'color': 'Tempo (s)'}
            )

            st.plotly_chart(fig_heatmap, use_container_width=True)

            # Análise de pontos fortes
            st.subheader("💪 Pontos Fortes por Setor")

            col1, col2, col3 = st.columns(3)

            # Melhor em cada setor
            melhor_s1 = analise_setores.loc[analise_setores['S1_Sec_min'].idxmin()]
            melhor_s2 = analise_setores.loc[analise_setores['S2_Sec_min'].idxmin()]
            melhor_s3 = analise_setores.loc[analise_setores['S3_Sec_min'].idxmin()]

            with col1:
                st.metric(
                    "🥇 Rei do Setor 1",
                    melhor_s1['Nome_Piloto'],
                    f"{melhor_s1['S1_Sec_min']:.3f}s"
                )

            with col2:
                st.metric(
                    "🥇 Rei do Setor 2", 
                    melhor_s2['Nome_Piloto'],
                    f"{melhor_s2['S2_Sec_min']:.3f}s"
                )

            with col3:
                st.metric(
                    "🥇 Rei do Setor 3",
                    melhor_s3['Nome_Piloto'], 
                    f"{melhor_s3['S3_Sec_min']:.3f}s"
                )

            # Tabela setorial completa
            st.subheader("📋 Análise Setorial Completa")

            tabela_setores = analise_setores.copy()
            tabela_setores['Setor Forte'] = tabela_setores['Melhor_Setor'].map({1: 'S1', 2: 'S2', 3: 'S3'})

            colunas_setor = ['Nome_Piloto', 'Equipe_first', 'Montadora_first', 'S1_Sec_min', 'S2_Sec_min', 'S3_Sec_min', 'Setor Forte']
            st.dataframe(tabela_setores[colunas_setor], hide_index=True)

# Footer
st.markdown("---")
st.markdown("### 🏎️ Stock Car Analytics Pro v2.0 - Chronon Edition")
st.markdown("**Baseado nos dados oficiais da Audace Tech Cronometragem**")
st.markdown(f"*Dados importados:* {len(st.session_state.dados_etapas_v2)} etapas | " + 
           f"*Sistema:* Chronon.com.br Integration")

# Informações do Chronon
with st.expander("ℹ️ Sobre os dados do Chronon.com.br"):
    st.write("""
    **Cronometragem Oficial:**
    - Audace Tech é a cronometragem oficial da Stock Car Pro Series
    - Dados incluem: tempos de volta, setores, speed trap, velocidade média
    - Precisão: milissegundos com transponders profissionais
    - Categorias: Stock Car PRO Series, Stock Light, F4 Brasil, TCR South America

    **Estrutura dos Dados:**
    - Time of Day: Horário da volta
    - Lap Tm: Tempo da volta
    - Speed: Velocidade média da volta  
    - S1/S2/S3 Tm: Tempos dos setores 1, 2 e 3
    - SPT: Velocidade no speed trap
    - Hits/Strength/Noise: Dados de qualidade do transponder
    """)
