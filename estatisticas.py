import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import re
from datetime import datetime
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Stock Car Analytics Pro",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Base de dados fixa para mapeamento de equipes e montadoras
MAPEAMENTO_EQUIPES_MONTADORAS = {
    "Gabriel Casagrande": {"Equipe": "A.Mattheis Vogel", "Montadora": "Volkswagen"},
    "Allam Khodair": {"Equipe": "Blau Motorsport", "Montadora": "Volkswagen"},
    "Cesar Ramos": {"Equipe": "Ipiranga Racing", "Montadora": "Toyota"},
    "Daniel Serra": {"Equipe": "Eurofarma-RC", "Montadora": "Chevrolet"},
    "Felipe Massa": {"Equipe": "TMG Racing", "Montadora": "Chevrolet"},
    "Rubens Barrichello": {"Equipe": "Full Time", "Montadora": "Toyota"},
    "Cacá Bueno": {"Equipe": "KTF Sports", "Montadora": "Chevrolet"},
    "Thiago Camilo": {"Equipe": "Ipiranga Racing", "Montadora": "Toyota"},
    "Bruno Baptista": {"Equipe": "RCM Motorsport", "Montadora": "Toyota"},
    "Felipe Fraga": {"Equipe": "Blau Motorsport", "Montadora": "Volkswagen"},
    "Ricardo Zonta": {"Equipe": "RMatheus", "Montadora": "Toyota"},
    "Gaetano di Mauro": {"Equipe": "Cavaleiro Sports", "Montadora": "Chevrolet"},
    "Nelson Piquet Jr": {"Equipe": "Cavaleiro Sports", "Montadora": "Chevrolet"},
    "Guilherme Salas": {"Equipe": "KTF Racing", "Montadora": "Chevrolet"},
    "Átila Abreu": {"Equipe": "Pole Motorsport", "Montadora": "Toyota"},
    "Ricardo Maurício": {"Equipe": "Eurofarma-RC", "Montadora": "Chevrolet"},
    # Adicione mais pilotos conforme necessário
}

# Dicionário de pistas e suas distâncias (em km)
PISTAS = {
    "Interlagos": 4.309,
    "Goiânia": 3.835,
    "Santa Cruz do Sul": 3.067,
    "Cascavel": 3.458,
    "Curitiba": 2.369,
    "Londrina": 3.295,
    "Campo Grande": 3.433,
    "Brasília": 5.476,
    "Ribeirão Preto": 4.216,
    "Tarumã": 3.068,
    "Velopark": 3.150,
    "Outros": 0.0
}

def processar_csv(uploaded_file):
    """Processa o arquivo CSV e separa os dados por carro"""
    df = pd.read_csv(uploaded_file)

    # Identificar linhas com padrão de carro (número - nome - categoria)
    pattern_rows = df['Time of Day'].str.match(r'^\d+ - .+ - .+$', na=False)
    pattern_indices = df.index[pattern_rows].tolist()

    # Criar lista para armazenar dados processados
    dados_processados = []

    for i, start_idx in enumerate(pattern_indices):
        # Extrair informações da linha padrão
        info_linha = df.loc[start_idx, 'Time of Day']
        numero_carro = info_linha.split(' - ')[0]
        nome_piloto = info_linha.split(' - ')[1]

        # Determinar fim dos dados deste carro
        end_idx = pattern_indices[i + 1] if i + 1 < len(pattern_indices) else len(df)

        # Extrair dados de voltas do carro
        dados_carro = df.loc[start_idx + 1:end_idx - 1].copy()

        if not dados_carro.empty:
            dados_carro['Numero_Carro'] = numero_carro
            dados_carro['Nome_Piloto'] = nome_piloto
            dados_processados.append(dados_carro)

    if dados_processados:
        df_final = pd.concat(dados_processados, ignore_index=True)

        # Adicionar informações de equipe e montadora
        df_final['Equipe'] = df_final['Nome_Piloto'].map(
            lambda piloto: MAPEAMENTO_EQUIPES_MONTADORAS.get(piloto, {}).get('Equipe', 'Desconhecida')
        )
        df_final['Montadora'] = df_final['Nome_Piloto'].map(
            lambda piloto: MAPEAMENTO_EQUIPES_MONTADORAS.get(piloto, {}).get('Montadora', 'Desconhecida')
        )

        return df_final

    return pd.DataFrame()

def converter_tempo_para_segundos(tempo_str):
    """Converte string de tempo (MM:SS.sss) para segundos"""
    try:
        if pd.isna(tempo_str) or tempo_str == '' or tempo_str == 'No Time':
            return None

        # Remover espaços e converter para string
        tempo_str = str(tempo_str).strip()

        # Padrão para MM:SS.sss
        if ':' in tempo_str and '.' in tempo_str:
            partes = tempo_str.split(':')
            minutos = int(partes[0])
            segundos_partes = partes[1].split('.')
            segundos = int(segundos_partes[0])
            milesimos = int(segundos_partes[1])
            return minutos * 60 + segundos + milesimos / 1000

        return float(tempo_str)
    except:
        return None

def formatar_tempo(segundos):
    """Converte segundos para formato MM:SS.sss"""
    if pd.isna(segundos) or segundos is None:
        return 'N/A'

    minutos = int(segundos // 60)
    segundos_restantes = segundos % 60

    return f"{minutos:02d}:{segundos_restantes:06.3f}"

def calcular_delta(tempo_atual, tempo_referencia):
    """Calcula o delta entre dois tempos"""
    if pd.isna(tempo_atual) or pd.isna(tempo_referencia) or tempo_atual is None or tempo_referencia is None:
        return None

    delta = tempo_atual - tempo_referencia
    sinal = "+" if delta > 0 else ""
    return f"{sinal}{delta:.3f}s"

def calcular_estatisticas_basicas(df):
    """Calcula estatísticas básicas do dataframe"""
    if df.empty:
        return {}

    stats = {}

    # Colunas de tempo para analisar
    colunas_tempo = ['Lap Time', 'Sector 1', 'Sector 2', 'Sector 3']

    for coluna in colunas_tempo:
        if coluna in df.columns:
            tempos_numericos = df[coluna].apply(converter_tempo_para_segundos).dropna()

            if not tempos_numericos.empty:
                stats[coluna] = {
                    'melhor': tempos_numericos.min(),
                    'pior': tempos_numericos.max(),
                    'media': tempos_numericos.mean(),
                    'mediana': tempos_numericos.median()
                }

    return stats

# Título principal
st.title("🏎️ Stock Car Analytics Pro")
st.markdown("### Sistema Completo de Análise de Performance")

# Inicializar session state
if 'dados_etapas' not in st.session_state:
    st.session_state.dados_etapas = {}
if 'dados_referencia' not in st.session_state:
    st.session_state.dados_referencia = {}

# Sidebar para navegação
st.sidebar.title("📊 Navegação")

# Seção 1: Importação de Dados
secao = st.sidebar.selectbox(
    "Escolha a seção:",
    ["📥 Importação de Dados", "🏁 Dashboard Aproveitamento", "📈 Comparações Temporais", 
     "🏆 Rankings por Equipe", "⚡ Análise de Performance", "📋 Inserção Manual", 
     "🎯 Tempos de Referência", "📊 Histórico Comparativo"]
)

if secao == "📥 Importação de Dados":
    st.header("📥 Importação de Dados por Etapa")

    col1, col2 = st.columns(2)

    with col1:
        temporada = st.selectbox("Temporada:", ["2024", "2025"])
        etapa = st.text_input("Etapa (ex: Interlagos, Goiânia):", "")
        sessao = st.selectbox("Sessão:", ["Treino Livre 1", "Treino Livre 2", "Classificação", "Corrida 1", "Corrida 2"])

    with col2:
        pista_selecionada = st.selectbox("Pista:", list(PISTAS.keys()))
        uploaded_file = st.file_uploader("Carregar arquivo CSV:", type=['csv'])

    if uploaded_file and etapa:
        df_processado = processar_csv(uploaded_file)

        if not df_processado.empty:
            # Salvar dados na session
            chave_etapa = f"{temporada}_{etapa}_{sessao}"
            st.session_state.dados_etapas[chave_etapa] = {
                'dataframe': df_processado,
                'temporada': temporada,
                'etapa': etapa,
                'sessao': sessao,
                'pista': pista_selecionada,
                'distancia_km': PISTAS[pista_selecionada]
            }

            st.success(f"✅ Dados importados com sucesso para {temporada} - {etapa} - {sessao}")

            # Preview dos dados
            st.subheader("👀 Preview dos Dados Importados")
            st.write(f"**Total de registros:** {len(df_processado)}")
            st.write(f"**Pilotos encontrados:** {len(df_processado['Nome_Piloto'].unique())}")
            st.write(f"**Equipes:** {len(df_processado['Equipe'].unique())}")
            st.write(f"**Montadoras:** {len(df_processado['Montadora'].unique())}")

            # Mostrar alguns dados
            with st.expander("Ver dados detalhados"):
                st.dataframe(df_processado.head(20))
        else:
            st.error("❌ Erro ao processar o arquivo CSV. Verifique o formato.")

elif secao == "📋 Inserção Manual":
    st.header("📋 Inserção Manual de Dados")

    col1, col2 = st.columns(2)

    with col1:
        temporada_manual = st.selectbox("Temporada:", ["2024", "2025"], key="temp_manual")
        etapa_manual = st.text_input("Etapa:", "", key="etapa_manual")
        sessao_manual = st.selectbox("Sessão:", ["Treino Livre 1", "Treino Livre 2", "Classificação", "Corrida 1", "Corrida 2"], key="sessao_manual")
        piloto_manual = st.selectbox("Piloto:", list(MAPEAMENTO_EQUIPES_MONTADORAS.keys()), key="piloto_manual")

    with col2:
        volta_manual = st.text_input("Tempo da Volta (MM:SS.sss):", "01:30.500", key="volta_manual")
        setor1_manual = st.text_input("Setor 1 (MM:SS.sss):", "00:28.200", key="s1_manual")
        setor2_manual = st.text_input("Setor 2 (MM:SS.sss):", "00:31.150", key="s2_manual")
        setor3_manual = st.text_input("Setor 3 (MM:SS.sss):", "00:31.150", key="s3_manual")

    if st.button("➕ Adicionar Registro Manual"):
        if etapa_manual and piloto_manual:
            chave_etapa = f"{temporada_manual}_{etapa_manual}_{sessao_manual}"

            # Criar novo registro
            novo_registro = {
                'Nome_Piloto': piloto_manual,
                'Lap Time': volta_manual,
                'Sector 1': setor1_manual,
                'Sector 2': setor2_manual,
                'Sector 3': setor3_manual,
                'Equipe': MAPEAMENTO_EQUIPES_MONTADORAS[piloto_manual]['Equipe'],
                'Montadora': MAPEAMENTO_EQUIPES_MONTADORAS[piloto_manual]['Montadora'],
                'Numero_Carro': '99'  # Valor padrão
            }

            # Adicionar aos dados existentes ou criar novo dataframe
            if chave_etapa in st.session_state.dados_etapas:
                # Adicionar ao dataframe existente
                df_existente = st.session_state.dados_etapas[chave_etapa]['dataframe']
                novo_df = pd.concat([df_existente, pd.DataFrame([novo_registro])], ignore_index=True)
                st.session_state.dados_etapas[chave_etapa]['dataframe'] = novo_df
            else:
                # Criar nova entrada
                st.session_state.dados_etapas[chave_etapa] = {
                    'dataframe': pd.DataFrame([novo_registro]),
                    'temporada': temporada_manual,
                    'etapa': etapa_manual,
                    'sessao': sessao_manual,
                    'pista': 'Manual',
                    'distancia_km': 0.0
                }

            st.success(f"✅ Registro adicionado para {piloto_manual} em {etapa_manual}")

elif secao == "🎯 Tempos de Referência":
    st.header("🎯 Configuração de Tempos de Referência")

    st.markdown("Configure tempos de referência para comparações futuras.")

    col1, col2 = st.columns(2)

    with col1:
        ref_temporada = st.selectbox("Temporada de Referência:", ["2024", "2025"], key="ref_temp")
        ref_etapa = st.text_input("Etapa de Referência:", "", key="ref_etapa")
        ref_piloto = st.selectbox("Piloto de Referência:", list(MAPEAMENTO_EQUIPES_MONTADORAS.keys()), key="ref_piloto")

    with col2:
        ref_volta = st.text_input("Tempo de Referência (MM:SS.sss):", "01:30.000", key="ref_volta")
        ref_s1 = st.text_input("Setor 1 Referência:", "00:28.000", key="ref_s1")
        ref_s2 = st.text_input("Setor 2 Referência:", "00:31.000", key="ref_s2") 
        ref_s3 = st.text_input("Setor 3 Referência:", "00:31.000", key="ref_s3")

    if st.button("💾 Salvar Referência"):
        if ref_etapa and ref_piloto:
            chave_ref = f"{ref_temporada}_{ref_etapa}_{ref_piloto}"
            st.session_state.dados_referencia[chave_ref] = {
                'temporada': ref_temporada,
                'etapa': ref_etapa,
                'piloto': ref_piloto,
                'volta_referencia': converter_tempo_para_segundos(ref_volta),
                'setor1_referencia': converter_tempo_para_segundos(ref_s1),
                'setor2_referencia': converter_tempo_para_segundos(ref_s2),
                'setor3_referencia': converter_tempo_para_segundos(ref_s3)
            }

            st.success(f"✅ Referência salva para {ref_piloto} - {ref_etapa}")

    # Mostrar referências salvas
    if st.session_state.dados_referencia:
        st.subheader("📋 Referências Salvas")
        for chave, dados in st.session_state.dados_referencia.items():
            st.write(f"**{dados['piloto']}** - {dados['etapa']} ({dados['temporada']}) - Volta: {formatar_tempo(dados['volta_referencia'])}")

elif secao == "🏁 Dashboard Aproveitamento":
    st.header("🏁 Dashboard de Aproveitamento")

    if not st.session_state.dados_etapas:
        st.warning("⚠️ Importe dados primeiro na seção 'Importação de Dados'")
    else:
        # Seletor de etapa
        etapas_disponiveis = list(st.session_state.dados_etapas.keys())
        etapa_selecionada = st.selectbox("Selecione a Etapa:", etapas_disponiveis)

        dados_etapa = st.session_state.dados_etapas[etapa_selecionada]
        df = dados_etapa['dataframe']

        st.subheader(f"📊 Análise: {dados_etapa['etapa']} - {dados_etapa['sessao']}")

        # Filtros
        col1, col2, col3 = st.columns(3)

        with col1:
            equipes_filtro = st.multiselect("Filtrar por Equipe:", df['Equipe'].unique(), default=df['Equipe'].unique())

        with col2:
            montadoras_filtro = st.multiselect("Filtrar por Montadora:", df['Montadora'].unique(), default=df['Montadora'].unique())

        with col3:
            pilotos_filtro = st.multiselect("Filtrar por Piloto:", df['Nome_Piloto'].unique(), default=df['Nome_Piloto'].unique())

        # Aplicar filtros
        df_filtrado = df[
            (df['Equipe'].isin(equipes_filtro)) &
            (df['Montadora'].isin(montadoras_filtro)) &
            (df['Nome_Piloto'].isin(pilotos_filtro))
        ]

        if not df_filtrado.empty:
            # Converter tempos para segundos para análise
            df_filtrado_copy = df_filtrado.copy()
            df_filtrado_copy['Lap_Time_Sec'] = df_filtrado_copy['Lap Time'].apply(converter_tempo_para_segundos)
            df_filtrado_copy['S1_Sec'] = df_filtrado_copy['Sector 1'].apply(converter_tempo_para_segundos)
            df_filtrado_copy['S2_Sec'] = df_filtrado_copy['Sector 2'].apply(converter_tempo_para_segundos)
            df_filtrado_copy['S3_Sec'] = df_filtrado_copy['Sector 3'].apply(converter_tempo_para_segundos)

            # Melhores tempos por piloto
            melhores_por_piloto = df_filtrado_copy.groupby('Nome_Piloto').agg({
                'Lap_Time_Sec': 'min',
                'S1_Sec': 'min',
                'S2_Sec': 'min',
                'S3_Sec': 'min',
                'Equipe': 'first',
                'Montadora': 'first'
            }).reset_index()

            # Remover NaN
            melhores_por_piloto = melhores_por_piloto.dropna()

            if not melhores_por_piloto.empty:
                # Ordenar por melhor tempo de volta
                melhores_por_piloto = melhores_por_piloto.sort_values('Lap_Time_Sec')

                # Gráfico de barras - Melhores tempos
                fig_barras = go.Figure()

                fig_barras.add_trace(go.Bar(
                    x=melhores_por_piloto['Nome_Piloto'],
                    y=melhores_por_piloto['Lap_Time_Sec'],
                    name='Melhor Volta',
                    text=[formatar_tempo(t) for t in melhores_por_piloto['Lap_Time_Sec']],
                    textposition='outside',
                    marker_color='rgb(55, 83, 109)'
                ))

                fig_barras.update_layout(
                    title='🏆 Melhores Tempos por Piloto',
                    xaxis_title='Pilotos',
                    yaxis_title='Tempo (segundos)',
                    showlegend=False,
                    height=500
                )

                st.plotly_chart(fig_barras, use_container_width=True)

                # Tabela de melhores tempos
                st.subheader("📋 Tabela de Melhores Tempos")

                tabela_display = melhores_por_piloto.copy()
                tabela_display['Posição'] = range(1, len(tabela_display) + 1)
                tabela_display['Melhor Volta'] = [formatar_tempo(t) for t in tabela_display['Lap_Time_Sec']]
                tabela_display['Setor 1'] = [formatar_tempo(t) for t in tabela_display['S1_Sec']]
                tabela_display['Setor 2'] = [formatar_tempo(t) for t in tabela_display['S2_Sec']]
                tabela_display['Setor 3'] = [formatar_tempo(t) for t in tabela_display['S3_Sec']]

                # Calcular delta para o líder
                tempo_lider = melhores_por_piloto.iloc[0]['Lap_Time_Sec']
                tabela_display['Delta p/ Líder'] = [
                    calcular_delta(tempo, tempo_lider) if tempo != tempo_lider else "Líder"
                    for tempo in tabela_display['Lap_Time_Sec']
                ]

                colunas_mostrar = ['Posição', 'Nome_Piloto', 'Equipe', 'Montadora', 'Melhor Volta', 
                                 'Setor 1', 'Setor 2', 'Setor 3', 'Delta p/ Líder']

                st.dataframe(tabela_display[colunas_mostrar], hide_index=True)

elif secao == "📈 Comparações Temporais":
    st.header("📈 Comparações Temporais e Progressão")

    if len(st.session_state.dados_etapas) < 2:
        st.warning("⚠️ Importe dados de pelo menos 2 etapas para fazer comparações temporais")
    else:
        # Selecionar etapas para comparar
        etapas_disponiveis = list(st.session_state.dados_etapas.keys())

        col1, col2 = st.columns(2)

        with col1:
            etapa1 = st.selectbox("Primeira Etapa:", etapas_disponiveis, key="etapa1_comp")

        with col2:
            etapa2 = st.selectbox("Segunda Etapa:", etapas_disponiveis, key="etapa2_comp")

        if etapa1 != etapa2:
            dados1 = st.session_state.dados_etapas[etapa1]
            dados2 = st.session_state.dados_etapas[etapa2]

            df1 = dados1['dataframe']
            df2 = dados2['dataframe']

            # Pilotos em comum
            pilotos_comuns = set(df1['Nome_Piloto'].unique()) & set(df2['Nome_Piloto'].unique())

            if pilotos_comuns:
                st.subheader(f"🔄 Comparação: {dados1['etapa']} vs {dados2['etapa']}")

                piloto_comparacao = st.selectbox("Selecionar Piloto para Comparação:", list(pilotos_comuns))

                # Dados do piloto em ambas as etapas
                dados_piloto1 = df1[df1['Nome_Piloto'] == piloto_comparacao].copy()
                dados_piloto2 = df2[df2['Nome_Piloto'] == piloto_comparacao].copy()

                # Converter tempos
                dados_piloto1['Lap_Time_Sec'] = dados_piloto1['Lap Time'].apply(converter_tempo_para_segundos)
                dados_piloto2['Lap_Time_Sec'] = dados_piloto2['Lap Time'].apply(converter_tempo_para_segundos)

                melhor1 = dados_piloto1['Lap_Time_Sec'].min()
                melhor2 = dados_piloto2['Lap_Time_Sec'].min()

                # Comparação visual
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        label=f"{dados1['etapa']}",
                        value=formatar_tempo(melhor1) if pd.notna(melhor1) else "N/A"
                    )

                with col2:
                    st.metric(
                        label=f"{dados2['etapa']}",
                        value=formatar_tempo(melhor2) if pd.notna(melhor2) else "N/A"
                    )

                with col3:
                    if pd.notna(melhor1) and pd.notna(melhor2):
                        delta = melhor2 - melhor1
                        delta_str = f"{delta:+.3f}s"
                        st.metric(
                            label="Evolução",
                            value=delta_str,
                            delta=delta_str
                        )
            else:
                st.warning("⚠️ Nenhum piloto em comum entre as etapas selecionadas")

elif secao == "🏆 Rankings por Equipe":
    st.header("🏆 Rankings por Equipe e Montadora")

    if not st.session_state.dados_etapas:
        st.warning("⚠️ Importe dados primeiro")
    else:
        etapas_disponiveis = list(st.session_state.dados_etapas.keys())
        etapa_ranking = st.selectbox("Selecione a Etapa:", etapas_disponiveis, key="etapa_ranking")

        dados_etapa = st.session_state.dados_etapas[etapa_ranking]
        df = dados_etapa['dataframe'].copy()

        # Converter tempos
        df['Lap_Time_Sec'] = df['Lap Time'].apply(converter_tempo_para_segundos)

        tab1, tab2 = st.tabs(["🏁 Ranking por Equipe", "🚗 Ranking por Montadora"])

        with tab1:
            st.subheader("🏁 Performance por Equipe")

            # Melhor tempo por equipe
            ranking_equipe = df.dropna(subset=['Lap_Time_Sec']).groupby('Equipe').agg({
                'Lap_Time_Sec': 'min',
                'Nome_Piloto': lambda x: x.iloc[df.loc[x.index, 'Lap_Time_Sec'].idxmin()]
            }).reset_index()

            ranking_equipe = ranking_equipe.sort_values('Lap_Time_Sec')
            ranking_equipe['Posição'] = range(1, len(ranking_equipe) + 1)

            # Gráfico de barras por equipe
            fig_equipe = go.Figure()

            fig_equipe.add_trace(go.Bar(
                x=ranking_equipe['Equipe'],
                y=ranking_equipe['Lap_Time_Sec'],
                text=[formatar_tempo(t) for t in ranking_equipe['Lap_Time_Sec']],
                textposition='outside',
                marker_color='rgb(26, 118, 255)'
            ))

            fig_equipe.update_layout(
                title='🏆 Melhor Tempo por Equipe',
                xaxis_title='Equipes',
                yaxis_title='Tempo (segundos)',
                height=500
            )

            st.plotly_chart(fig_equipe, use_container_width=True)

            # Tabela de ranking
            tabela_equipe = ranking_equipe.copy()
            tabela_equipe['Melhor Tempo'] = [formatar_tempo(t) for t in tabela_equipe['Lap_Time_Sec']]

            st.dataframe(
                tabela_equipe[['Posição', 'Equipe', 'Nome_Piloto', 'Melhor Tempo']],
                hide_index=True
            )

        with tab2:
            st.subheader("🚗 Performance por Montadora")

            # Melhor tempo por montadora
            ranking_montadora = df.dropna(subset=['Lap_Time_Sec']).groupby('Montadora').agg({
                'Lap_Time_Sec': 'min',
                'Nome_Piloto': lambda x: x.iloc[df.loc[x.index, 'Lap_Time_Sec'].idxmin()],
                'Equipe': lambda x: x.iloc[df.loc[x.index, 'Lap_Time_Sec'].idxmin()]
            }).reset_index()

            ranking_montadora = ranking_montadora.sort_values('Lap_Time_Sec')
            ranking_montadora['Posição'] = range(1, len(ranking_montadora) + 1)

            # Gráfico de barras por montadora
            fig_montadora = go.Figure()

            cores_montadora = {'Chevrolet': 'rgb(255, 215, 0)', 'Toyota': 'rgb(220, 20, 60)', 'Volkswagen': 'rgb(70, 130, 180)'}

            fig_montadora.add_trace(go.Bar(
                x=ranking_montadora['Montadora'],
                y=ranking_montadora['Lap_Time_Sec'],
                text=[formatar_tempo(t) for t in ranking_montadora['Lap_Time_Sec']],
                textposition='outside',
                marker_color=[cores_montadora.get(m, 'rgb(128, 128, 128)') for m in ranking_montadora['Montadora']]
            ))

            fig_montadora.update_layout(
                title='🚗 Melhor Tempo por Montadora',
                xaxis_title='Montadoras',
                yaxis_title='Tempo (segundos)',
                height=500
            )

            st.plotly_chart(fig_montadora, use_container_width=True)

            # Tabela de ranking
            tabela_montadora = ranking_montadora.copy()
            tabela_montadora['Melhor Tempo'] = [formatar_tempo(t) for t in tabela_montadora['Lap_Time_Sec']]

            st.dataframe(
                tabela_montadora[['Posição', 'Montadora', 'Nome_Piloto', 'Equipe', 'Melhor Tempo']],
                hide_index=True
            )

elif secao == "⚡ Análise de Performance":
    st.header("⚡ Análise Detalhada de Performance")

    if not st.session_state.dados_etapas:
        st.warning("⚠️ Importe dados primeiro")
    else:
        etapas_disponiveis = list(st.session_state.dados_etapas.keys())
        etapa_performance = st.selectbox("Selecione a Etapa:", etapas_disponiveis, key="etapa_perf")

        dados_etapa = st.session_state.dados_etapas[etapa_performance]
        df = dados_etapa['dataframe'].copy()

        # Converter tempos para análise
        df['Lap_Time_Sec'] = df['Lap Time'].apply(converter_tempo_para_segundos)
        df['S1_Sec'] = df['Sector 1'].apply(converter_tempo_para_segundos)
        df['S2_Sec'] = df['Sector 2'].apply(converter_tempo_para_segundos)
        df['S3_Sec'] = df['Sector 3'].apply(converter_tempo_para_segundos)

        tab1, tab2, tab3 = st.tabs(["📊 Análise Setorial", "🎯 Comparação com Referência", "📈 Distribuição de Tempos"])

        with tab1:
            st.subheader("📊 Análise Setorial Detalhada")

            # Seletor de pilotos para comparação
            pilotos_selecionados = st.multiselect(
                "Selecione pilotos para comparação:",
                df['Nome_Piloto'].unique(),
                default=df['Nome_Piloto'].unique()[:5] if len(df['Nome_Piloto'].unique()) >= 5 else df['Nome_Piloto'].unique()
            )

            if pilotos_selecionados:
                df_selecionados = df[df['Nome_Piloto'].isin(pilotos_selecionados)]

                # Melhores setores por piloto
                melhores_setores = df_selecionados.groupby('Nome_Piloto').agg({
                    'S1_Sec': 'min',
                    'S2_Sec': 'min', 
                    'S3_Sec': 'min',
                    'Lap_Time_Sec': 'min'
                }).reset_index()

                # Gráfico de comparação setorial
                fig_setores = go.Figure()

                fig_setores.add_trace(go.Bar(
                    x=melhores_setores['Nome_Piloto'],
                    y=melhores_setores['S1_Sec'],
                    name='Setor 1',
                    marker_color='rgb(255, 99, 132)'
                ))

                fig_setores.add_trace(go.Bar(
                    x=melhores_setores['Nome_Piloto'],
                    y=melhores_setores['S2_Sec'],
                    name='Setor 2',
                    marker_color='rgb(54, 162, 235)'
                ))

                fig_setores.add_trace(go.Bar(
                    x=melhores_setores['Nome_Piloto'],
                    y=melhores_setores['S3_Sec'],
                    name='Setor 3',
                    marker_color='rgb(75, 192, 192)'
                ))

                fig_setores.update_layout(
                    title='🏁 Comparação de Melhores Setores',
                    xaxis_title='Pilotos',
                    yaxis_title='Tempo (segundos)',
                    barmode='group',
                    height=500
                )

                st.plotly_chart(fig_setores, use_container_width=True)

                # Identificar melhor setor de cada piloto
                st.subheader("🎯 Melhor Setor por Piloto")

                for _, row in melhores_setores.iterrows():
                    setores = [row['S1_Sec'], row['S2_Sec'], row['S3_Sec']]
                    melhor_setor_idx = np.argmin(setores)
                    melhor_setor_nome = ['Setor 1', 'Setor 2', 'Setor 3'][melhor_setor_idx]

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.write(f"**{row['Nome_Piloto']}**")

                    with col2:
                        st.write(f"Forte em: {melhor_setor_nome}")

                    with col3:
                        st.write(f"Tempo: {formatar_tempo(setores[melhor_setor_idx])}")

                    with col4:
                        volta_total = row['Lap_Time_Sec']
                        st.write(f"Volta: {formatar_tempo(volta_total)}")

        with tab2:
            st.subheader("🎯 Comparação com Tempos de Referência")

            if st.session_state.dados_referencia:
                # Selecionar referência
                refs_disponiveis = list(st.session_state.dados_referencia.keys())
                ref_selecionada = st.selectbox("Selecione a Referência:", refs_disponiveis, key="ref_comp")

                dados_ref = st.session_state.dados_referencia[ref_selecionada]

                # Comparar com a referência
                df_comparacao = df.dropna(subset=['Lap_Time_Sec']).copy()

                # Calcular deltas
                df_comparacao['Delta_Volta'] = df_comparacao['Lap_Time_Sec'] - dados_ref['volta_referencia']
                df_comparacao['Delta_S1'] = df_comparacao['S1_Sec'] - dados_ref['setor1_referencia']
                df_comparacao['Delta_S2'] = df_comparacao['S2_Sec'] - dados_ref['setor2_referencia']
                df_comparacao['Delta_S3'] = df_comparacao['S3_Sec'] - dados_ref['setor3_referencia']

                # Melhores deltas por piloto
                melhores_deltas = df_comparacao.groupby('Nome_Piloto').agg({
                    'Delta_Volta': 'min',
                    'Delta_S1': 'min',
                    'Delta_S2': 'min',
                    'Delta_S3': 'min',
                    'Lap_Time_Sec': 'min'
                }).reset_index()

                # Ordenar por melhor delta de volta
                melhores_deltas = melhores_deltas.sort_values('Delta_Volta')

                # Exibir comparação
                st.write(f"**Referência:** {dados_ref['piloto']} - {dados_ref['etapa']} - {formatar_tempo(dados_ref['volta_referencia'])}")

                # Tabela de comparação
                tabela_comp = melhores_deltas.copy()
                tabela_comp['Tempo Atual'] = [formatar_tempo(t) for t in tabela_comp['Lap_Time_Sec']]
                tabela_comp['Delta Volta'] = [f"{d:+.3f}s" for d in tabela_comp['Delta_Volta']]
                tabela_comp['Delta S1'] = [f"{d:+.3f}s" for d in tabela_comp['Delta_S1']]
                tabela_comp['Delta S2'] = [f"{d:+.3f}s" for d in tabela_comp['Delta_S2']]
                tabela_comp['Delta S3'] = [f"{d:+.3f}s" for d in tabela_comp['Delta_S3']]

                # Destacar melhores tempos
                def highlight_best(s):
                    if s.name in ['Delta Volta', 'Delta S1', 'Delta S2', 'Delta S3']:
                        values = [float(x.replace('s', '').replace('+', '')) for x in s if 's' in str(x)]
                        if values:
                            min_val = min(values)
                            return ['background-color: #90EE90' if float(str(x).replace('s', '').replace('+', '')) == min_val else 'background-color: #FFB6C1' if float(str(x).replace('s', '').replace('+', '')) > 0 else '' for x in s if 's' in str(x)]
                    return ['' for _ in s]

                st.dataframe(
                    tabela_comp[['Nome_Piloto', 'Tempo Atual', 'Delta Volta', 'Delta S1', 'Delta S2', 'Delta S3']],
                    hide_index=True
                )

                # Estatísticas da comparação
                melhores_que_ref = len(melhores_deltas[melhores_deltas['Delta_Volta'] < 0])
                total_pilotos = len(melhores_deltas)

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Pilotos mais rápidos que referência", f"{melhores_que_ref}/{total_pilotos}")

                with col2:
                    if not melhores_deltas.empty:
                        melhor_delta = melhores_deltas.iloc[0]['Delta_Volta']
                        st.metric("Melhor delta", f"{melhor_delta:+.3f}s")

                with col3:
                    if not melhores_deltas.empty:
                        delta_medio = melhores_deltas['Delta_Volta'].mean()
                        st.metric("Delta médio", f"{delta_medio:+.3f}s")

            else:
                st.info("💡 Configure tempos de referência na seção 'Tempos de Referência' primeiro")

        with tab3:
            st.subheader("📈 Distribuição de Tempos")

            # Box plot dos tempos
            if not df.dropna(subset=['Lap_Time_Sec']).empty:
                fig_box = px.box(
                    df.dropna(subset=['Lap_Time_Sec']), 
                    x='Montadora', 
                    y='Lap_Time_Sec',
                    color='Equipe',
                    title='📊 Distribuição de Tempos por Montadora e Equipe'
                )

                fig_box.update_layout(height=500)
                st.plotly_chart(fig_box, use_container_width=True)

                # Estatísticas descritivas
                stats = df.dropna(subset=['Lap_Time_Sec'])['Lap_Time_Sec'].describe()

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Tempo mais rápido", formatar_tempo(stats['min']))

                with col2:
                    st.metric("Tempo mais lento", formatar_tempo(stats['max']))

                with col3:
                    st.metric("Tempo médio", formatar_tempo(stats['mean']))

                with col4:
                    diferenca = stats['max'] - stats['min']
                    st.metric("Diferença total", f"{diferenca:.3f}s")

elif secao == "📊 Histórico Comparativo":
    st.header("📊 Histórico Comparativo e Evolução")

    if len(st.session_state.dados_etapas) < 2:
        st.warning("⚠️ Importe dados de pelo menos 2 etapas para análise histórica")
    else:
        st.subheader("📈 Evolução de Performance ao Longo das Etapas")

        # Consolidar dados de todas as etapas
        todos_dados = []

        for chave, dados in st.session_state.dados_etapas.items():
            df_etapa = dados['dataframe'].copy()
            df_etapa['Etapa_Chave'] = chave
            df_etapa['Etapa'] = dados['etapa']
            df_etapa['Sessao'] = dados['sessao']
            df_etapa['Temporada'] = dados['temporada']
            todos_dados.append(df_etapa)

        df_historico = pd.concat(todos_dados, ignore_index=True)
        df_historico['Lap_Time_Sec'] = df_historico['Lap Time'].apply(converter_tempo_para_segundos)

        # Filtros para análise histórica
        col1, col2 = st.columns(2)

        with col1:
            piloto_hist = st.selectbox("Selecione Piloto para Análise Histórica:", df_historico['Nome_Piloto'].unique())

        with col2:
            sessao_hist = st.selectbox("Tipo de Sessão:", df_historico['Sessao'].unique())

        # Dados filtrados
        df_piloto_hist = df_historico[
            (df_historico['Nome_Piloto'] == piloto_hist) & 
            (df_historico['Sessao'] == sessao_hist)
        ].dropna(subset=['Lap_Time_Sec'])

        if not df_piloto_hist.empty:
            # Melhores tempos por etapa
            melhores_por_etapa = df_piloto_hist.groupby(['Etapa', 'Etapa_Chave']).agg({
                'Lap_Time_Sec': 'min',
                'Temporada': 'first'
            }).reset_index()

            # Ordenar por etapa
            melhores_por_etapa = melhores_por_etapa.sort_values('Etapa_Chave')

            # Gráfico de linha - Evolução
            fig_evolucao = go.Figure()

            fig_evolucao.add_trace(go.Scatter(
                x=melhores_por_etapa['Etapa'],
                y=melhores_por_etapa['Lap_Time_Sec'],
                mode='lines+markers',
                name=f'Evolução - {piloto_hist}',
                text=[formatar_tempo(t) for t in melhores_por_etapa['Lap_Time_Sec']],
                textposition='top center',
                marker=dict(size=10, color='rgb(26, 118, 255)'),
                line=dict(width=3)
            ))

            fig_evolucao.update_layout(
                title=f'📈 Evolução de {piloto_hist} - {sessao_hist}',
                xaxis_title='Etapas',
                yaxis_title='Melhor Tempo (segundos)',
                height=500,
                showlegend=False
            )

            st.plotly_chart(fig_evolucao, use_container_width=True)

            # Análise da evolução
            if len(melhores_por_etapa) >= 2:
                primeira_etapa = melhores_por_etapa.iloc[0]['Lap_Time_Sec']
                ultima_etapa = melhores_por_etapa.iloc[-1]['Lap_Time_Sec']
                evolucao = ultima_etapa - primeira_etapa

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Primeira Etapa", formatar_tempo(primeira_etapa))

                with col2:
                    st.metric("Última Etapa", formatar_tempo(ultima_etapa))

                with col3:
                    st.metric("Evolução Total", f"{evolucao:+.3f}s")

                with col4:
                    melhor_tempo_hist = melhores_por_etapa['Lap_Time_Sec'].min()
                    st.metric("Melhor Tempo Histórico", formatar_tempo(melhor_tempo_hist))

                # Tabela histórica
                st.subheader("📋 Histórico Detalhado")

                tabela_hist = melhores_por_etapa.copy()
                tabela_hist['Melhor Tempo'] = [formatar_tempo(t) for t in tabela_hist['Lap_Time_Sec']]
                tabela_hist['Posição Histórica'] = tabela_hist['Lap_Time_Sec'].rank(method='min').astype(int)

                st.dataframe(
                    tabela_hist[['Temporada', 'Etapa', 'Melhor Tempo', 'Posição Histórica']],
                    hide_index=True
                )

# Footer
st.markdown("---")
st.markdown("### 🏎️ Stock Car Analytics Pro")
st.markdown("**Desenvolvido para análise profissional de performance em Stock Car**")
st.markdown("*Dados importados:* " + str(len(st.session_state.dados_etapas)) + " etapas | " + 
           "*Referências salvas:* " + str(len(st.session_state.dados_referencia)))
