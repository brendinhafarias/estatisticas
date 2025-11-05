import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import json
import re
from datetime import datetime
import numpy as np
import io
import base64

# Configuração da página
st.set_page_config(
    page_title="Stock Car Analytics Pro v2.0 - Complete Edition",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para melhor visual
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #FF6B6B;
    }
    .success-box {
        background: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
</style>
""", unsafe_allow_html=True)

# Base de dados COMPLETA com todos os pilotos da Stock Car 2024-2025
MAPEAMENTO_COMPLETO_PILOTOS = {
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
    "Rafael Suzuki": {"Equipe": "TMG Racing", "Montadora": "Chevrolet", "Numero": "90"},
    "Julio Campos": {"Equipe": "Pole Motorsport", "Montadora": "Toyota", "Numero": "11"},
    "Dudu Barrichello": {"Equipe": "Full Time", "Montadora": "Toyota", "Numero": "91"},
    "Zezinho Muggiati": {"Equipe": "KTF Sports", "Montadora": "Chevrolet", "Numero": "1"},
    "Tuca Antoniazi": {"Equipe": "Hot Car Racing", "Montadora": "Chevrolet", "Numero": "27"},
    "Diego Nunes": {"Equipe": "Blau Motorsport", "Montadora": "Volkswagen", "Numero": "5"},
    "Tony Kanaan": {"Equipe": "Full Time", "Montadora": "Toyota", "Numero": "14"},
    "Marcos Gomes": {"Equipe": "Cavaleiro Sports", "Montadora": "Chevrolet", "Numero": "9"},
    "Arthur Leist": {"Equipe": "Full Time", "Montadora": "Toyota", "Numero": "16"},
    "Gianluca Petecof": {"Equipe": "Full Time", "Montadora": "Toyota", "Numero": "88"},
}

# Pistas oficiais COMPLETAS com dados técnicos detalhados
PISTAS_OFICIAIS_COMPLETAS = {
    "Goiânia": {
        "distancia": 3.835, "setores": 3, "drs_zones": 1, "tipo": "Misto",
        "curvas": 12, "retas_longas": 2, "elevacao": "Baixa"
    },
    "Velocitta": {
        "distancia": 3.150, "setores": 3, "drs_zones": 2, "tipo": "Técnico", 
        "curvas": 14, "retas_longas": 1, "elevacao": "Média"
    },
    "Interlagos": {
        "distancia": 4.309, "setores": 3, "drs_zones": 2, "tipo": "Clássico",
        "curvas": 16, "retas_longas": 2, "elevacao": "Alta"
    },
    "Cascavel": {
        "distancia": 3.458, "setores": 3, "drs_zones": 1, "tipo": "Oval",
        "curvas": 4, "retas_longas": 2, "elevacao": "Baixa"
    },
    "Velopark": {
        "distancia": 3.068, "setores": 3, "drs_zones": 2, "tipo": "Técnico",
        "curvas": 15, "retas_longas": 1, "elevacao": "Baixa"
    },
    "Belo Horizonte": {
        "distancia": 3.067, "setores": 3, "drs_zones": 1, "tipo": "Urbano",
        "curvas": 11, "retas_longas": 2, "elevacao": "Média"
    },
    "Buenos Aires": {
        "distancia": 4.200, "setores": 3, "drs_zones": 2, "tipo": "Clássico",
        "curvas": 18, "retas_longas": 2, "elevacao": "Baixa"
    },
    "Uruguai": {
        "distancia": 3.200, "setores": 3, "drs_zones": 1, "tipo": "Misto",
        "curvas": 13, "retas_longas": 1, "elevacao": "Baixa"
    },
    "Curitiba": {
        "distancia": 2.369, "setores": 3, "drs_zones": 1, "tipo": "Urbano",
        "curvas": 10, "retas_longas": 1, "elevacao": "Baixa"
    },
    "Santa Cruz do Sul": {
        "distancia": 3.067, "setores": 3, "drs_zones": 1, "tipo": "Misto",
        "curvas": 12, "retas_longas": 2, "elevacao": "Baixa"
    },
    "Tarumã": {
        "distancia": 3.068, "setores": 3, "drs_zones": 2, "tipo": "Técnico",
        "curvas": 16, "retas_longas": 1, "elevacao": "Média"
    },
    "Ribeirão Preto": {
        "distancia": 4.216, "setores": 3, "drs_zones": 2, "tipo": "Misto",
        "curvas": 14, "retas_longas": 2, "elevacao": "Baixa"
    }
}

# Sessões oficiais COMPLETAS
SESSOES_OFICIAIS_COMPLETAS = {
    "Treino Rookies": {"duracao": 30, "tipo": "Treino", "pontos": False},
    "Shake Down": {"duracao": 15, "tipo": "Treino", "pontos": False},
    "T1": {"duracao": 90, "tipo": "Treino Livre", "pontos": False},
    "T2": {"duracao": 90, "tipo": "Treino Livre", "pontos": False},
    "Q1-G1": {"duracao": 15, "tipo": "Classificação", "pontos": False},
    "Q1-G2": {"duracao": 15, "tipo": "Classificação", "pontos": False},
    "Q2": {"duracao": 12, "tipo": "Classificação", "pontos": False},
    "Q3": {"duracao": 10, "tipo": "Classificação", "pontos": False},
    "QF": {"duracao": 8, "tipo": "Super Pole", "pontos": False},
    "Prova1 Sprint": {"duracao": 30, "tipo": "Corrida", "pontos": True},
    "P2": {"duracao": 50, "tipo": "Corrida Principal", "pontos": True},
    "Warm Up": {"duracao": 20, "tipo": "Aquecimento", "pontos": False}
}

# Temporadas disponíveis
TEMPORADAS_DISPONIVEIS = ["2020", "2021", "2022", "2023", "2024", "2025"]

# Sistema de pontuação oficial Stock Car
SISTEMA_PONTUACAO = {
    1: 25, 2: 20, 3: 16, 4: 13, 5: 11, 6: 10, 7: 9, 8: 8, 9: 7, 10: 6,
    11: 5, 12: 4, 13: 3, 14: 2, 15: 1
}

def processar_csv_chronon_completo(uploaded_file):
    """Processa CSV no formato oficial do Chronon.com.br com todas as validações"""
    try:
        df = pd.read_csv(uploaded_file)

        # Verificar se é um arquivo válido do Chronon
        if df.empty or len(df.columns) < 5:
            st.error("❌ Arquivo CSV inválido. Verifique se é um arquivo do Chronon.")
            return pd.DataFrame()

        # Identificar linhas com padrão de piloto
        primeira_coluna = df.iloc[:, 0].astype(str)
        pattern_rows = primeira_coluna.str.match(r'^\d+ - .+ - Stock Car PRO \d{4}$', na=False)
        pattern_indices = df.index[pattern_rows].tolist()

        if not pattern_indices:
            st.error("❌ Formato de arquivo não reconhecido. Verifique se é um CSV do Chronon oficial.")
            return pd.DataFrame()

        dados_processados = []

        for i, start_idx in enumerate(pattern_indices):
            info_linha = df.iloc[start_idx, 0]
            partes = info_linha.split(' - ')

            if len(partes) >= 3:
                numero_carro = partes[0]
                nome_piloto = partes[1]
                categoria = partes[2]

                end_idx = pattern_indices[i + 1] if i + 1 < len(pattern_indices) else len(df)
                dados_piloto = df.iloc[start_idx + 1:end_idx].copy()

                if not dados_piloto.empty:
                    dados_piloto['Numero_Carro'] = numero_carro
                    dados_piloto['Nome_Piloto'] = nome_piloto
                    dados_piloto['Categoria'] = categoria

                    # Adicionar informações completas
                    piloto_info = MAPEAMENTO_COMPLETO_PILOTOS.get(nome_piloto, {})
                    dados_piloto['Equipe'] = piloto_info.get('Equipe', 'Independente')
                    dados_piloto['Montadora'] = piloto_info.get('Montadora', 'Outras')
                    dados_piloto['Numero_Oficial'] = piloto_info.get('Numero', numero_carro)

                    dados_processados.append(dados_piloto)

        if dados_processados:
            df_final = pd.concat(dados_processados, ignore_index=True)
            return df_final

    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo: {str(e)}")
        return pd.DataFrame()

    return pd.DataFrame()

def converter_tempo_para_segundos_completo(tempo_str):
    """Conversão completa e robusta de tempos"""
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

def calcular_metricas_avancadas_completas(df):
    """Calcula todas as métricas possíveis dos dados do Chronon"""
    if df.empty:
        return df

    df_calc = df.copy()

    # Colunas de tempo
    colunas_tempo = ['Lap Tm', 'S1 Tm', 'S2 Tm', 'S3 Tm']
    for col in colunas_tempo:
        if col in df.columns:
            nova_coluna = col.replace(' Tm', '_Sec').replace(' ', '_')
            df_calc[nova_coluna] = df_calc[col].apply(converter_tempo_para_segundos_completo)

    # Velocidades
    if 'Speed' in df.columns:
        df_calc['Speed_Kmh'] = pd.to_numeric(df_calc['Speed'].astype(str).str.replace(',', '.'), errors='coerce')

    if 'SPT' in df.columns:
        df_calc['Speed_Trap_Kmh'] = pd.to_numeric(df_calc['SPT'].astype(str).str.replace(',', '.'), errors='coerce')

    # Qualidade do sinal
    if 'Strength' in df.columns:
        df_calc['Signal_Strength'] = pd.to_numeric(df_calc['Strength'], errors='coerce')

    if 'Hits' in df.columns:
        df_calc['Transponder_Hits'] = pd.to_numeric(df_calc['Hits'], errors='coerce')

    # Número da volta
    if 'Lap' in df.columns:
        df_calc['Lap_Number'] = pd.to_numeric(df_calc['Lap'], errors='coerce')

    return df_calc

def formatar_tempo_completo(segundos):
    """Formatação completa de tempo"""
    if pd.isna(segundos) or segundos is None:
        return 'N/A'

    if segundos < 60:
        return f"{segundos:.3f}s"

    minutos = int(segundos // 60)
    segundos_restantes = segundos % 60
    return f"{minutos}:{segundos_restantes:06.3f}"

def calcular_pontos_campeonato(posicao):
    """Calcula pontos baseado no sistema oficial da Stock Car"""
    return SISTEMA_PONTUACAO.get(posicao, 0)

def gerar_relatorio_completo_piloto(df, nome_piloto):
    """Gera relatório completo de um piloto específico"""
    dados_piloto = df[df['Nome_Piloto'] == nome_piloto].copy()

    if dados_piloto.empty:
        return None

    relatorio = {
        'piloto': nome_piloto,
        'equipe': dados_piloto['Equipe'].iloc[0],
        'montadora': dados_piloto['Montadora'].iloc[0],
        'numero': dados_piloto['Numero_Oficial'].iloc[0],
        'total_voltas': len(dados_piloto),
        'voltas_validas': len(dados_piloto.dropna(subset=['Lap_Sec'])),
    }

    # Estatísticas de tempo
    if 'Lap_Sec' in dados_piloto.columns:
        tempos_validos = dados_piloto['Lap_Sec'].dropna()
        if not tempos_validos.empty:
            relatorio.update({
                'melhor_volta': tempos_validos.min(),
                'pior_volta': tempos_validos.max(),
                'tempo_medio': tempos_validos.mean(),
                'consistencia': tempos_validos.std(),
            })

    # Estatísticas de velocidade
    if 'Speed_Kmh' in dados_piloto.columns:
        velocidades = dados_piloto['Speed_Kmh'].dropna()
        if not velocidades.empty:
            relatorio.update({
                'velocidade_maxima': velocidades.max(),
                'velocidade_media': velocidades.mean(),
            })

    if 'Speed_Trap_Kmh' in dados_piloto.columns:
        speed_trap = dados_piloto['Speed_Trap_Kmh'].dropna()
        if not speed_trap.empty:
            relatorio['speed_trap_max'] = speed_trap.max()

    # Análise setorial
    setores = ['S1_Sec', 'S2_Sec', 'S3_Sec']
    setores_existentes = [s for s in setores if s in dados_piloto.columns]

    if setores_existentes:
        for i, setor in enumerate(setores_existentes, 1):
            tempos_setor = dados_piloto[setor].dropna()
            if not tempos_setor.empty:
                relatorio[f'melhor_setor_{i}'] = tempos_setor.min()
                relatorio[f'media_setor_{i}'] = tempos_setor.mean()

    return relatorio

def exportar_dados_para_csv(df, nome_arquivo):
    """Exporta dados processados para CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{nome_arquivo}.csv">📥 Baixar dados processados</a>'
    return href

def criar_grafico_comparacao_montadoras(df):
    """Cria gráfico comparativo entre montadoras"""
    if 'Lap_Sec' not in df.columns:
        return None

    # Melhores tempos por montadora
    melhores_por_mont = df.dropna(subset=['Lap_Sec']).groupby('Montadora').agg({
        'Lap_Sec': ['min', 'mean', 'count'],
        'Speed_Kmh': 'max',
        'Nome_Piloto': 'nunique'
    }).round(3)

    melhores_por_mont.columns = ['_'.join(col).strip() for col in melhores_por_mont.columns]
    melhores_por_mont = melhores_por_mont.reset_index()

    return melhores_por_mont

# Interface principal
st.markdown('<div class="main-header"><h1>🏎️ Stock Car Analytics Pro v2.0 - Complete Edition</h1><p>Sistema Oficial baseado em dados do Chronon.com.br - Audace Tech</p></div>', unsafe_allow_html=True)

# Inicializar session state COMPLETO
if 'dados_etapas_completo' not in st.session_state:
    st.session_state.dados_etapas_completo = {}
if 'dados_referencia_completo' not in st.session_state:
    st.session_state.dados_referencia_completo = {}
if 'configuracoes_usuario' not in st.session_state:
    st.session_state.configuracoes_usuario = {}
if 'historico_analises' not in st.session_state:
    st.session_state.historico_analises = []

# Sidebar COMPLETA para navegação
st.sidebar.title("🏁 Stock Car Analytics")
st.sidebar.markdown("---")

secao = st.sidebar.selectbox(
    "Escolha a seção:",
    ["🏠 Dashboard Principal", "📥 Importação Chronon", "🏆 Resultados Oficiais", 
     "⚡ Análise Speed Trap", "📊 Análise Setorial Pro", "🔄 Comparação Temporal",
     "📈 Rankings Completos", "🎯 Sistema de Referências", "📋 Relatórios Executivos",
     "🏁 Campeonato e Pontos", "⚙️ Configurações Avançadas", "📤 Exportar Dados"]
)

# Estatísticas rápidas na sidebar
if st.session_state.dados_etapas_completo:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Status do Sistema")
    st.sidebar.write(f"**Etapas carregadas:** {len(st.session_state.dados_etapas_completo)}")
    st.sidebar.write(f"**Referências salvas:** {len(st.session_state.dados_referencia_completo)}")

    # Total de pilotos únicos
    todos_pilotos = set()
    for dados in st.session_state.dados_etapas_completo.values():
        if 'Nome_Piloto' in dados['dataframe'].columns:
            todos_pilotos.update(dados['dataframe']['Nome_Piloto'].unique())

    st.sidebar.write(f"**Pilotos no sistema:** {len(todos_pilotos)}")

if secao == "🏠 Dashboard Principal":
    st.header("🏠 Dashboard Principal")

    # Resumo geral do sistema
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Etapas Disponíveis", len(st.session_state.dados_etapas_completo))
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Pistas Oficiais", len(PISTAS_OFICIAIS_COMPLETAS))
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Pilotos Cadastrados", len(MAPEAMENTO_COMPLETO_PILOTOS))
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Sessões Suportadas", len(SESSOES_OFICIAIS_COMPLETAS))
        st.markdown('</div>', unsafe_allow_html=True)

    # Últimas análises
    if st.session_state.dados_etapas_completo:
        st.subheader("📈 Últimas Etapas Carregadas")

        etapas_recentes = list(st.session_state.dados_etapas_completo.keys())[-5:]

        for etapa in etapas_recentes:
            dados = st.session_state.dados_etapas_completo[etapa]

            with st.expander(f"🏁 {dados['etapa']} - {dados['sessao']} ({dados['temporada']})"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Pista:** {dados['pista']}")
                    st.write(f"**Distância:** {dados['dados_pista']['distancia']} km")

                with col2:
                    if 'dataframe' in dados:
                        df = dados['dataframe']
                        st.write(f"**Pilotos:** {df['Nome_Piloto'].nunique()}")
                        st.write(f"**Voltas:** {len(df)}")

                with col3:
                    if 'dataframe' in dados and 'Lap_Sec' in df.columns:
                        melhor_volta = df['Lap_Sec'].min()
                        st.write(f"**Melhor volta:** {formatar_tempo_completo(melhor_volta)}")

    else:
        st.info("💡 Importe dados na seção 'Importação Chronon' para começar a análise")

        # Tutorial rápido
        st.subheader("🎯 Como começar:")
        st.write("1. 📥 Vá para 'Importação Chronon' e carregue um arquivo CSV oficial")
        st.write("2. 🏆 Visualize os resultados em 'Resultados Oficiais'")
        st.write("3. ⚡ Analise velocidades em 'Análise Speed Trap'")
        st.write("4. 📊 Compare setores em 'Análise Setorial Pro'")
        st.write("5. 📋 Gere relatórios em 'Relatórios Executivos'")

elif secao == "📥 Importação Chronon":
    st.header("📥 Importação de Dados Oficiais Chronon")

    # Instruções detalhadas
    with st.expander("ℹ️ Como usar esta funcionalidade"):
        st.write("""
        **Sobre o Chronon.com.br:**
        - Site oficial da Audace Tech (cronometragem oficial da Stock Car)
        - Dados incluem: tempos de volta, setores, velocidades, speed trap
        - Formato padrão: CSV com dados de transponder

        **Como importar:**
        1. Acesse chronon.com.br/resultados/stock-car/
        2. Escolha a temporada e etapa desejada
        3. Baixe o arquivo CSV da sessão
        4. Faça o upload aqui
        """)

    st.info("💡 Este sistema processa arquivos CSV no formato oficial do Chronon.com.br")

    # Formulário de importação COMPLETO
    with st.form("form_importacao_chronon", clear_on_submit=False):
        st.subheader("📋 Dados da Sessão")

        col1, col2 = st.columns(2)

        with col1:
            temporada_chronon = st.selectbox("Temporada:", TEMPORADAS_DISPONIVEIS, index=4)
            etapa_chronon = st.text_input("Etapa (ex: #3 Interlagos, #7 Goiânia):", "")
            sessao_chronon = st.selectbox("Sessão:", list(SESSOES_OFICIAIS_COMPLETAS.keys()))

        with col2:
            pista_chronon = st.selectbox("Pista:", list(PISTAS_OFICIAIS_COMPLETAS.keys()))
            uploaded_file_chronon = st.file_uploader("Arquivo CSV Oficial:", type=['csv'])
            observacoes = st.text_area("Observações (opcional):", placeholder="Ex: Chuva no T2, problema técnico no Q3...")

        # Botão de importação
        submitted = st.form_submit_button("🚀 IMPORTAR DADOS DO CHRONON", type="primary")

        if submitted:
            if uploaded_file_chronon and etapa_chronon:
                with st.spinner("🔄 Processando dados do Chronon..."):
                    df_chronon = processar_csv_chronon_completo(uploaded_file_chronon)

                    if not df_chronon.empty:
                        # Calcular métricas avançadas
                        df_chronon = calcular_metricas_avancadas_completas(df_chronon)

                        # Salvar dados na session
                        chave_etapa = f"{temporada_chronon}_{etapa_chronon}_{sessao_chronon}"
                        st.session_state.dados_etapas_completo[chave_etapa] = {
                            'dataframe': df_chronon,
                            'temporada': temporada_chronon,
                            'etapa': etapa_chronon,
                            'sessao': sessao_chronon,
                            'pista': pista_chronon,
                            'dados_pista': PISTAS_OFICIAIS_COMPLETAS[pista_chronon],
                            'observacoes': observacoes,
                            'data_importacao': datetime.now(),
                            'info_sessao': SESSOES_OFICIAIS_COMPLETAS[sessao_chronon]
                        }

                        # Adicionar ao histórico
                        st.session_state.historico_analises.append({
                            'acao': 'Importação',
                            'etapa': etapa_chronon,
                            'sessao': sessao_chronon,
                            'timestamp': datetime.now()
                        })

                        st.markdown('<div class="success-box">✅ DADOS IMPORTADOS COM SUCESSO!</div>', unsafe_allow_html=True)

                        # Estatísticas da importação
                        st.subheader("📊 Resumo da Importação")

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric("Pilotos Identificados", df_chronon['Nome_Piloto'].nunique())

                        with col2:
                            st.metric("Total de Voltas", len(df_chronon))

                        with col3:
                            if 'Speed_Trap_Kmh' in df_chronon.columns:
                                max_speed = df_chronon['Speed_Trap_Kmh'].max()
                                st.metric("Vel. Máxima", f"{max_speed:.1f} km/h" if pd.notna(max_speed) else "N/A")

                        with col4:
                            if 'Lap_Sec' in df_chronon.columns:
                                melhor_volta = df_chronon['Lap_Sec'].min()
                                st.metric("Melhor Volta", formatar_tempo_completo(melhor_volta) if pd.notna(melhor_volta) else "N/A")

                        # Detalhes da sessão
                        st.subheader("📋 Detalhes da Sessão")

                        col1, col2 = st.columns(2)

                        with col1:
                            info_pista = PISTAS_OFICIAIS_COMPLETAS[pista_chronon]
                            st.write(f"**Pista:** {pista_chronon}")
                            st.write(f"**Distância:** {info_pista['distancia']} km")
                            st.write(f"**Tipo:** {info_pista['tipo']}")
                            st.write(f"**Curvas:** {info_pista['curvas']}")
                            st.write(f"**DRS Zones:** {info_pista['drs_zones']}")

                        with col2:
                            info_sessao = SESSOES_OFICIAIS_COMPLETAS[sessao_chronon]
                            st.write(f"**Sessão:** {sessao_chronon}")
                            st.write(f"**Duração:** {info_sessao['duracao']} min")
                            st.write(f"**Tipo:** {info_sessao['tipo']}")
                            st.write(f"**Pontos:** {'Sim' if info_sessao['pontos'] else 'Não'}")

                        # Distribuição por montadora
                        if 'Montadora' in df_chronon.columns:
                            st.subheader("🏭 Distribuição por Montadora")

                            dist_mont = df_chronon['Montadora'].value_counts()

                            fig_dist = px.pie(
                                values=dist_mont.values,
                                names=dist_mont.index,
                                title="Participação por Montadora",
                                color_discrete_map={
                                    'Chevrolet': '#FFD700',
                                    'Toyota': '#DC143C', 
                                    'Volkswagen': '#4682B4'
                                }
                            )

                            st.plotly_chart(fig_dist, use_container_width=True)

                        # Preview dos dados
                        with st.expander("👀 Preview dos Dados Importados"):
                            colunas_preview = ['Nome_Piloto', 'Equipe', 'Montadora', 'Lap Tm', 'Speed', 'S1 Tm', 'S2 Tm', 'S3 Tm', 'SPT']
                            colunas_existentes = [col for col in colunas_preview if col in df_chronon.columns]

                            st.dataframe(df_chronon[colunas_existentes].head(20), use_container_width=True)

                    else:
                        st.error("❌ Falha na importação. Verifique o formato do arquivo.")

            else:
                st.error("❌ Preencha todos os campos obrigatórios e selecione um arquivo.")

elif secao == "🏆 Resultados Oficiais":
    st.header("🏆 Resultados Oficiais")

    if not st.session_state.dados_etapas_completo:
        st.warning("⚠️ Importe dados do Chronon primeiro")
    else:
        # Seletor de etapa
        etapas_disponiveis = list(st.session_state.dados_etapas_completo.keys())
        etapa_selecionada = st.selectbox("Selecione a Etapa:", etapas_disponiveis)

        dados_etapa = st.session_state.dados_etapas_completo[etapa_selecionada]
        df = dados_etapa['dataframe']
        pista_info = dados_etapa['dados_pista']
        sessao_info = dados_etapa['info_sessao']

        # Cabeçalho da etapa
        st.subheader(f"🏁 {dados_etapa['etapa']} - {dados_etapa['sessao']} ({dados_etapa['temporada']})")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"**Pista:** {dados_etapa['pista']}")
            st.write(f"**Distância:** {pista_info['distancia']} km")
            st.write(f"**Tipo:** {pista_info['tipo']}")

        with col2:
            st.write(f"**Duração:** {sessao_info['duracao']} min")
            st.write(f"**Tipo:** {sessao_info['tipo']}")
            st.write(f"**Pontos:** {'Sim' if sessao_info['pontos'] else 'Não'}")

        with col3:
            if dados_etapa.get('observacoes'):
                st.write(f"**Observações:** {dados_etapa['observacoes']}")

        # Filtros avançados
        st.subheader("🔍 Filtros Avançados")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            equipes_filtro = st.multiselect("Equipes:", df['Equipe'].unique(), default=df['Equipe'].unique())

        with col2:
            montadoras_filtro = st.multiselect("Montadoras:", df['Montadora'].unique(), default=df['Montadora'].unique())

        with col3:
            pilotos_filtro = st.multiselect("Pilotos:", df['Nome_Piloto'].unique(), default=df['Nome_Piloto'].unique())

        with col4:
            # Filtro por número de voltas
            if 'Lap_Number' in df.columns:
                voltas_min, voltas_max = st.slider("Faixa de Voltas:", 
                                                  int(df['Lap_Number'].min()), 
                                                  int(df['Lap_Number'].max()),
                                                  (int(df['Lap_Number'].min()), int(df['Lap_Number'].max())))

        # Aplicar filtros
        df_filtrado = df[
            (df['Equipe'].isin(equipes_filtro)) &
            (df['Montadora'].isin(montadoras_filtro)) &
            (df['Nome_Piloto'].isin(pilotos_filtro))
        ]

        if 'Lap_Number' in df.columns:
            df_filtrado = df_filtrado[
                (df_filtrado['Lap_Number'] >= voltas_min) &
                (df_filtrado['Lap_Number'] <= voltas_max)
            ]

        if not df_filtrado.empty and 'Lap_Sec' in df_filtrado.columns:
            # Classificação oficial
            melhores_tempos = df_filtrado.dropna(subset=['Lap_Sec']).groupby('Nome_Piloto').agg({
                'Lap_Sec': 'min',
                'Speed_Kmh': 'max',
                'Speed_Trap_Kmh': 'max',
                'Equipe': 'first',
                'Montadora': 'first',
                'Numero_Oficial': 'first'
            }).reset_index()

            melhores_tempos = melhores_tempos.sort_values('Lap_Sec')
            melhores_tempos['Posicao'] = range(1, len(melhores_tempos) + 1)

            # Calcular pontos (se for corrida)
            if sessao_info['pontos']:
                melhores_tempos['Pontos'] = melhores_tempos['Posicao'].apply(calcular_pontos_campeonato)

            # Gráfico de classificação
            fig_classificacao = go.Figure()

            cores_montadora = {
                'Chevrolet': '#FFD700',
                'Toyota': '#DC143C', 
                'Volkswagen': '#4682B4',
                'Outras': '#808080'
            }

            fig_classificacao.add_trace(go.Bar(
                x=melhores_tempos['Nome_Piloto'],
                y=melhores_tempos['Lap_Sec'],
                text=[formatar_tempo_completo(t) for t in melhores_tempos['Lap_Sec']],
                textposition='outside',
                marker_color=[cores_montadora.get(m, '#808080') for m in melhores_tempos['Montadora']],
                hovertemplate="<b>%{x}</b><br>Tempo: %{text}<br>Posição: %{marker.color}<extra></extra>"
            ))

            fig_classificacao.update_layout(
                title=f'🏆 Classificação Oficial - {dados_etapa["etapa"]} - {dados_etapa["sessao"]}',
                xaxis_title='Pilotos',
                yaxis_title='Tempo (segundos)',
                height=600,
                showlegend=False
            )

            st.plotly_chart(fig_classificacao, use_container_width=True)

            # Tabela de classificação completa
            st.subheader("📊 Classificação Detalhada")

            tabela_classificacao = melhores_tempos.copy()
            tabela_classificacao['Tempo'] = [formatar_tempo_completo(t) for t in tabela_classificacao['Lap_Sec']]
            tabela_classificacao['Vel. Máxima'] = [f"{v:.1f} km/h" if pd.notna(v) else "N/A" for v in tabela_classificacao['Speed_Kmh']]
            tabela_classificacao['Speed Trap'] = [f"{v:.1f} km/h" if pd.notna(v) else "N/A" for v in tabela_classificacao['Speed_Trap_Kmh']]

            # Delta para o líder
            tempo_lider = melhores_tempos.iloc[0]['Lap_Sec']
            tabela_classificacao['Delta'] = [
                "Líder" if i == 0 else f"+{(tempo - tempo_lider):.3f}s"
                for i, tempo in enumerate(tabela_classificacao['Lap_Sec'])
            ]

            # Colunas da tabela
            colunas_tabela = ['Posicao', 'Numero_Oficial', 'Nome_Piloto', 'Equipe', 'Montadora', 'Tempo', 'Delta', 'Vel. Máxima', 'Speed Trap']

            if sessao_info['pontos']:
                colunas_tabela.insert(-3, 'Pontos')

            st.dataframe(tabela_classificacao[colunas_tabela], hide_index=True, use_container_width=True)

            # Estatísticas da sessão
            st.subheader("📈 Estatísticas da Sessão")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                diferenca_total = melhores_tempos['Lap_Sec'].max() - melhores_tempos['Lap_Sec'].min()
                st.metric("Diferença Total", f"{diferenca_total:.3f}s")

            with col2:
                tempo_medio = melhores_tempos['Lap_Sec'].mean()
                st.metric("Tempo Médio", formatar_tempo_completo(tempo_medio))

            with col3:
                if 'Speed_Trap_Kmh' in melhores_tempos.columns:
                    velocidade_maxima_geral = melhores_tempos['Speed_Trap_Kmh'].max()
                    st.metric("Vel. Máxima Geral", f"{velocidade_maxima_geral:.1f} km/h" if pd.notna(velocidade_maxima_geral) else "N/A")

            with col4:
                st.metric("Pilotos Classificados", len(melhores_tempos))

# Continuar com as outras seções...
elif secao == "⚡ Análise Speed Trap":
    st.header("⚡ Análise Detalhada de Speed Trap")

    if not st.session_state.dados_etapas_completo:
        st.warning("⚠️ Importe dados do Chronon primeiro")
    else:
        etapas_disponiveis = list(st.session_state.dados_etapas_completo.keys())
        etapa_speed = st.selectbox("Etapa para Speed Trap:", etapas_disponiveis, key="speed_analysis")

        dados_etapa = st.session_state.dados_etapas_completo[etapa_speed]
        df = dados_etapa['dataframe']

        if 'Speed_Trap_Kmh' in df.columns:
            st.subheader(f"🚀 Speed Trap - {dados_etapa['etapa']} - {dados_etapa['sessao']}")

            # Análise speed trap por montadora
            speed_por_montadora = df.dropna(subset=['Speed_Trap_Kmh']).groupby('Montadora').agg({
                'Speed_Trap_Kmh': ['max', 'mean', 'std', 'count'],
                'Nome_Piloto': 'nunique'
            }).round(2)

            speed_por_montadora.columns = ['Max', 'Média', 'Desvio', 'Voltas', 'Pilotos']
            speed_por_montadora = speed_por_montadora.reset_index()

            # Gráfico de distribuição
            fig_speed_dist = px.box(
                df.dropna(subset=['Speed_Trap_Kmh']),
                x='Montadora',
                y='Speed_Trap_Kmh',
                color='Montadora',
                color_discrete_map={
                    'Chevrolet': '#FFD700',
                    'Toyota': '#DC143C',
                    'Volkswagen': '#4682B4'
                },
                title='📊 Distribuição de Velocidade no Speed Trap por Montadora'
            )

            st.plotly_chart(fig_speed_dist, use_container_width=True)

            # Top 10 velocidades
            st.subheader("🏆 Top 10 Velocidades Speed Trap")

            top_speeds = df.dropna(subset=['Speed_Trap_Kmh']).nlargest(10, 'Speed_Trap_Kmh')

            col1, col2 = st.columns(2)

            with col1:
                # Lista dos top 10
                for i, (idx, row) in enumerate(top_speeds.iterrows(), 1):
                    st.write(f"**{i}º {row['Nome_Piloto']}** ({row['Montadora']}) - {row['Speed_Trap_Kmh']:.1f} km/h")

            with col2:
                # Gráfico dos top 10
                fig_top_speeds = go.Figure()

                fig_top_speeds.add_trace(go.Bar(
                    x=top_speeds['Nome_Piloto'],
                    y=top_speeds['Speed_Trap_Kmh'],
                    text=[f"{v:.1f}" for v in top_speeds['Speed_Trap_Kmh']],
                    textposition='outside',
                    marker_color=[cores_montadora.get(m, '#808080') for m in top_speeds['Montadora']]
                ))

                fig_top_speeds.update_layout(
                    title="Top 10 Speed Trap",
                    xaxis_title="Pilotos",
                    yaxis_title="Velocidade (km/h)",
                    height=400
                )

                st.plotly_chart(fig_top_speeds, use_container_width=True)

            # Tabela comparativa por montadora
            st.subheader("📊 Análise Comparativa por Montadora")
            st.dataframe(speed_por_montadora, use_container_width=True)

            # Análise de correlação velocidade vs tempo de volta
            if 'Lap_Sec' in df.columns:
                st.subheader("🔍 Correlação Speed Trap vs Tempo de Volta")

                df_correlacao = df.dropna(subset=['Speed_Trap_Kmh', 'Lap_Sec'])

                if not df_correlacao.empty:
                    fig_correlacao = px.scatter(
                        df_correlacao,
                        x='Speed_Trap_Kmh',
                        y='Lap_Sec',
                        color='Montadora',
                        hover_data=['Nome_Piloto'],
                        title='Speed Trap vs Tempo de Volta',
                        color_discrete_map={
                            'Chevrolet': '#FFD700',
                            'Toyota': '#DC143C',
                            'Volkswagen': '#4682B4'
                        }
                    )

                    st.plotly_chart(fig_correlacao, use_container_width=True)

                    # Coeficiente de correlação
                    correlacao = df_correlacao['Speed_Trap_Kmh'].corr(df_correlacao['Lap_Sec'])
                    st.write(f"**Coeficiente de correlação:** {correlacao:.3f}")

                    if correlacao < -0.3:
                        st.success("✅ Correlação negativa forte: maior velocidade no speed trap = tempo de volta menor")
                    elif correlacao > 0.3:
                        st.warning("⚠️ Correlação positiva: pode indicar problemas aerodinâmicos ou de setup")
                    else:
                        st.info("ℹ️ Correlação fraca: velocidade no speed trap não determina o tempo de volta")

        else:
            st.info("💡 Dados de Speed Trap não disponíveis nesta sessão")


# CONTINUAÇÃO DAS SEÇÕES FALTANTES PARA O APLICATIVO COMPLETO

# Adicionar após a seção Speed Trap:

elif secao == "📊 Análise Setorial Pro":
    st.header("📊 Análise Setorial Profissional")

    if not st.session_state.dados_etapas_completo:
        st.warning("⚠️ Importe dados do Chronon primeiro")
    else:
        etapas_disponiveis = list(st.session_state.dados_etapas_completo.keys())
        etapa_setor = st.selectbox("Etapa para Análise Setorial:", etapas_disponiveis, key="setorial_pro")

        dados_etapa = st.session_state.dados_etapas_completo[etapa_setor]
        df = dados_etapa['dataframe']
        pista_info = dados_etapa['dados_pista']

        # Verificar se tem dados setoriais
        setores_disponiveis = [col for col in ['S1_Sec', 'S2_Sec', 'S3_Sec'] if col in df.columns]

        if setores_disponiveis:
            st.subheader(f"🔍 Análise Setorial - {dados_etapa['pista']} ({len(setores_disponiveis)} setores)")

            # Melhores setores por piloto
            analise_setorial = df.dropna(subset=setores_disponiveis).groupby('Nome_Piloto').agg({
                **{setor: ['min', 'mean', 'std'] for setor in setores_disponiveis},
                'Lap_Sec': 'min',
                'Equipe': 'first',
                'Montadora': 'first'
            }).round(3)

            analise_setorial.columns = ['_'.join(col).strip() for col in analise_setorial.columns]
            analise_setorial = analise_setorial.reset_index()

            # Identificar melhor setor por piloto
            if len(setores_disponiveis) >= 3:
                colunas_min = [f'{setor}_min' for setor in setores_disponiveis]
                analise_setorial['Melhor_Setor'] = analise_setorial[colunas_min].idxmin(axis=1).str.replace('_Sec_min', '').str.replace('_', ' ')

            # Heatmap setorial
            st.subheader("🔥 Mapa de Calor - Performance por Setor")

            # Preparar dados para heatmap
            colunas_heatmap = ['Nome_Piloto'] + [f'{setor}_min' for setor in setores_disponiveis]
            heatmap_data = analise_setorial[colunas_heatmap].set_index('Nome_Piloto')

            # Renomear colunas para melhor visualização
            heatmap_data.columns = [col.replace('_Sec_min', '').replace('_', ' ') for col in heatmap_data.columns]

            fig_heatmap = px.imshow(
                heatmap_data.T,
                text_auto='.3f',
                aspect='auto',
                title='Melhores Tempos por Setor (mais escuro = mais rápido)',
                labels={'x': 'Pilotos', 'y': 'Setores', 'color': 'Tempo (s)'},
                color_continuous_scale='RdYlBu_r'
            )

            fig_heatmap.update_layout(height=400)
            st.plotly_chart(fig_heatmap, use_container_width=True)

            # Reis dos setores
            st.subheader("👑 Reis dos Setores")

            cols_reis = st.columns(len(setores_disponiveis))

            for i, setor in enumerate(setores_disponiveis):
                coluna_min = f'{setor}_min'
                if coluna_min in analise_setorial.columns:
                    idx_melhor = analise_setorial[coluna_min].idxmin()
                    melhor_piloto = analise_setorial.loc[idx_melhor]

                    with cols_reis[i]:
                        st.metric(
                            f"🥇 Rei do {setor.replace('_Sec', '').replace('_', ' ')}",
                            melhor_piloto['Nome_Piloto'],
                            f"{melhor_piloto[coluna_min]:.3f}s"
                        )

            # Gráfico comparativo setorial
            st.subheader("📊 Comparação Setorial por Piloto")

            # Seletor de pilotos para comparar
            pilotos_comparar = st.multiselect(
                "Selecione pilotos para comparar setores:",
                analise_setorial['Nome_Piloto'].tolist(),
                default=analise_setorial['Nome_Piloto'].head(5).tolist()
            )

            if pilotos_comparar:
                dados_comparacao = analise_setorial[analise_setorial['Nome_Piloto'].isin(pilotos_comparar)]

                fig_setores_comp = go.Figure()

                for setor in setores_disponiveis:
                    coluna_min = f'{setor}_min'
                    if coluna_min in dados_comparacao.columns:
                        fig_setores_comp.add_trace(go.Bar(
                            name=setor.replace('_Sec', '').replace('_', ' '),
                            x=dados_comparacao['Nome_Piloto'],
                            y=dados_comparacao[coluna_min],
                            text=[f"{v:.3f}s" for v in dados_comparacao[coluna_min]],
                            textposition='outside'
                        ))

                fig_setores_comp.update_layout(
                    title='Comparação de Melhores Setores',
                    xaxis_title='Pilotos',
                    yaxis_title='Tempo (segundos)',
                    barmode='group',
                    height=500
                )

                st.plotly_chart(fig_setores_comp, use_container_width=True)

            # Tabela setorial completa
            st.subheader("📋 Tabela Setorial Completa")

            # Preparar tabela para exibição
            tabela_setorial = analise_setorial.copy()

            # Colunas a mostrar
            colunas_mostrar = ['Nome_Piloto', 'Equipe_first', 'Montadora_first']

            for setor in setores_disponiveis:
                col_min = f'{setor}_min'
                if col_min in tabela_setorial.columns:
                    tabela_setorial[f'Melhor {setor.replace("_Sec", "").replace("_", " ")}'] = [
                        formatar_tempo_completo(t) for t in tabela_setorial[col_min]
                    ]
                    colunas_mostrar.append(f'Melhor {setor.replace("_Sec", "").replace("_", " ")}')

            if 'Melhor_Setor' in tabela_setorial.columns:
                colunas_mostrar.append('Melhor_Setor')

            # Ordenar por melhor volta
            if 'Lap_Sec_min' in tabela_setorial.columns:
                tabela_setorial = tabela_setorial.sort_values('Lap_Sec_min')
                tabela_setorial['Tempo Volta'] = [formatar_tempo_completo(t) for t in tabela_setorial['Lap_Sec_min']]
                colunas_mostrar.append('Tempo Volta')

            st.dataframe(tabela_setorial[colunas_mostrar], hide_index=True, use_container_width=True)

            # Análise de consistência setorial
            st.subheader("📈 Análise de Consistência")

            # Pilotos mais consistentes por setor
            for setor in setores_disponiveis:
                col_std = f'{setor}_std'
                if col_std in analise_setorial.columns:
                    mais_consistente = analise_setorial.loc[analise_setorial[col_std].idxmin()]
                    st.write(f"**Mais consistente no {setor.replace('_Sec', '').replace('_', ' ')}:** {mais_consistente['Nome_Piloto']} (σ = {mais_consistente[col_std]:.3f}s)")

        else:
            st.info("💡 Dados setoriais não disponíveis nesta sessão")

elif secao == "🔄 Comparação Temporal":
    st.header("🔄 Comparação Temporal Entre Etapas")

    if len(st.session_state.dados_etapas_completo) < 2:
        st.warning("⚠️ Importe dados de pelo menos 2 etapas para fazer comparações temporais")
    else:
        st.subheader("📈 Comparação Entre Etapas")

        etapas_disponiveis = list(st.session_state.dados_etapas_completo.keys())

        col1, col2 = st.columns(2)

        with col1:
            etapa1 = st.selectbox("Primeira Etapa:", etapas_disponiveis, key="etapa1_temporal")

        with col2:
            etapa2 = st.selectbox("Segunda Etapa:", etapas_disponiveis, key="etapa2_temporal")

        if etapa1 != etapa2:
            dados1 = st.session_state.dados_etapas_completo[etapa1]
            dados2 = st.session_state.dados_etapas_completo[etapa2]

            df1 = dados1['dataframe']
            df2 = dados2['dataframe']

            # Pilotos em comum
            pilotos_comuns = set(df1['Nome_Piloto'].unique()) & set(df2['Nome_Piloto'].unique())

            if pilotos_comuns:
                st.subheader(f"🔄 {dados1['etapa']} vs {dados2['etapa']}")

                # Comparação geral
                if 'Lap_Sec' in df1.columns and 'Lap_Sec' in df2.columns:
                    # Melhores tempos de cada etapa
                    melhores1 = df1.dropna(subset=['Lap_Sec']).groupby('Nome_Piloto')['Lap_Sec'].min()
                    melhores2 = df2.dropna(subset=['Lap_Sec']).groupby('Nome_Piloto')['Lap_Sec'].min()

                    # Comparação para pilotos comuns
                    comparacao_data = []

                    for piloto in pilotos_comuns:
                        if piloto in melhores1.index and piloto in melhores2.index:
                            tempo1 = melhores1[piloto]
                            tempo2 = melhores2[piloto]
                            evolucao = tempo2 - tempo1

                            comparacao_data.append({
                                'Piloto': piloto,
                                'Etapa1': tempo1,
                                'Etapa2': tempo2,
                                'Evolução': evolucao,
                                'Evolução_Perc': (evolucao / tempo1) * 100,
                                'Equipe': df1[df1['Nome_Piloto'] == piloto]['Equipe'].iloc[0],
                                'Montadora': df1[df1['Nome_Piloto'] == piloto]['Montadora'].iloc[0]
                            })

                    if comparacao_data:
                        df_comparacao = pd.DataFrame(comparacao_data)
                        df_comparacao = df_comparacao.sort_values('Evolução')

                        # Gráfico de evolução
                        fig_evolucao = go.Figure()

                        cores = ['green' if x < 0 else 'red' for x in df_comparacao['Evolução']]

                        fig_evolucao.add_trace(go.Bar(
                            x=df_comparacao['Piloto'],
                            y=df_comparacao['Evolução'],
                            marker_color=cores,
                            text=[f"{x:+.3f}s" for x in df_comparacao['Evolução']],
                            textposition='outside'
                        ))

                        fig_evolucao.update_layout(
                            title=f'Evolução de Performance: {dados1["etapa"]} → {dados2["etapa"]}',
                            xaxis_title='Pilotos',
                            yaxis_title='Evolução (segundos)',
                            height=500
                        )

                        st.plotly_chart(fig_evolucao, use_container_width=True)

                        # Tabela de comparação
                        st.subheader("📊 Tabela de Comparação Detalhada")

                        tabela_comp = df_comparacao.copy()
                        tabela_comp['Tempo Etapa 1'] = [formatar_tempo_completo(t) for t in tabela_comp['Etapa1']]
                        tabela_comp['Tempo Etapa 2'] = [formatar_tempo_completo(t) for t in tabela_comp['Etapa2']]
                        tabela_comp['Evolução Tempo'] = [f"{x:+.3f}s" for x in tabela_comp['Evolução']]
                        tabela_comp['Evolução %'] = [f"{x:+.2f}%" for x in tabela_comp['Evolução_Perc']]

                        colunas_comp = ['Piloto', 'Equipe', 'Montadora', 'Tempo Etapa 1', 'Tempo Etapa 2', 'Evolução Tempo', 'Evolução %']

                        st.dataframe(tabela_comp[colunas_comp], hide_index=True, use_container_width=True)

                        # Estatísticas da comparação
                        st.subheader("📈 Estatísticas da Comparação")

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            melhores = len(df_comparacao[df_comparacao['Evolução'] < 0])
                            st.metric("Pilotos que melhoraram", f"{melhores}/{len(df_comparacao)}")

                        with col2:
                            melhor_evolucao = df_comparacao['Evolução'].min()
                            st.metric("Melhor evolução", f"{melhor_evolucao:.3f}s")

                        with col3:
                            pior_evolucao = df_comparacao['Evolução'].max()
                            st.metric("Pior evolução", f"{pior_evolucao:+.3f}s")

                        with col4:
                            evolucao_media = df_comparacao['Evolução'].mean()
                            st.metric("Evolução média", f"{evolucao_media:+.3f}s")

                        # Análise por montadora
                        st.subheader("🏭 Evolução por Montadora")

                        evolucao_mont = df_comparacao.groupby('Montadora').agg({
                            'Evolução': ['mean', 'count'],
                            'Piloto': 'count'
                        }).round(3)

                        evolucao_mont.columns = ['Evolução Média', 'Total Pilotos', 'Comparações']
                        evolucao_mont = evolucao_mont.reset_index()

                        st.dataframe(evolucao_mont, hide_index=True)

elif secao == "📈 Rankings Completos":
    st.header("📈 Rankings Completos")

    if not st.session_state.dados_etapas_completo:
        st.warning("⚠️ Importe dados do Chronon primeiro")
    else:
        st.subheader("🏆 Sistema de Rankings Avançados")

        # Seletor de tipo de ranking
        tipo_ranking = st.selectbox(
            "Tipo de Ranking:",
            ["🏁 Por Etapa Individual", "🏆 Campeonato Geral", "🏭 Por Montadora", "👥 Por Equipe", "📊 Performance Média"]
        )

        if tipo_ranking == "🏁 Por Etapa Individual":
            etapas_disponiveis = list(st.session_state.dados_etapas_completo.keys())
            etapa_ranking = st.selectbox("Selecione a Etapa:", etapas_disponiveis, key="ranking_etapa")

            dados_etapa = st.session_state.dados_etapas_completo[etapa_ranking]
            df = dados_etapa['dataframe']

            if 'Lap_Sec' in df.columns:
                # Ranking da etapa
                ranking_etapa = df.dropna(subset=['Lap_Sec']).groupby('Nome_Piloto').agg({
                    'Lap_Sec': 'min',
                    'Speed_Kmh': 'max',
                    'Speed_Trap_Kmh': 'max',
                    'Equipe': 'first',
                    'Montadora': 'first',
                    'Numero_Oficial': 'first'
                }).reset_index()

                ranking_etapa = ranking_etapa.sort_values('Lap_Sec')
                ranking_etapa['Posição'] = range(1, len(ranking_etapa) + 1)

                # Adicionar pontos se for corrida
                if dados_etapa['info_sessao']['pontos']:
                    ranking_etapa['Pontos'] = ranking_etapa['Posição'].apply(calcular_pontos_campeonato)

                # Gráfico do ranking
                fig_ranking = go.Figure()

                cores_posicao = ['#FFD700' if i == 1 else '#C0C0C0' if i == 2 else '#CD7F32' if i == 3 else '#4682B4' 
                               for i in ranking_etapa['Posição']]

                fig_ranking.add_trace(go.Bar(
                    x=ranking_etapa['Nome_Piloto'],
                    y=ranking_etapa['Lap_Sec'],
                    marker_color=cores_posicao,
                    text=[f"{i}º" for i in ranking_etapa['Posição']],
                    textposition='outside'
                ))

                fig_ranking.update_layout(
                    title=f'🏆 Ranking - {dados_etapa["etapa"]} - {dados_etapa["sessao"]}',
                    xaxis_title='Pilotos',
                    yaxis_title='Tempo (segundos)',
                    height=600
                )

                st.plotly_chart(fig_ranking, use_container_width=True)

                # Tabela do ranking
                tabela_ranking = ranking_etapa.copy()
                tabela_ranking['Tempo'] = [formatar_tempo_completo(t) for t in tabela_ranking['Lap_Sec']]
                tabela_ranking['Vel. Máx'] = [f"{v:.1f}" if pd.notna(v) else "N/A" for v in tabela_ranking['Speed_Kmh']]
                tabela_ranking['Speed Trap'] = [f"{v:.1f}" if pd.notna(v) else "N/A" for v in tabela_ranking['Speed_Trap_Kmh']]

                colunas_ranking = ['Posição', 'Numero_Oficial', 'Nome_Piloto', 'Equipe', 'Montadora', 'Tempo', 'Vel. Máx', 'Speed Trap']

                if dados_etapa['info_sessao']['pontos']:
                    colunas_ranking.insert(-3, 'Pontos')

                st.dataframe(tabela_ranking[colunas_ranking], hide_index=True, use_container_width=True)

        elif tipo_ranking == "🏆 Campeonato Geral":
            st.subheader("🏆 Ranking de Campeonato")

            # Consolidar pontos de todas as etapas que são corridas
            pontos_campeonato = {}
            etapas_pontuacao = []

            for chave, dados in st.session_state.dados_etapas_completo.items():
                if dados['info_sessao']['pontos'] and 'Lap_Sec' in dados['dataframe'].columns:
                    df = dados['dataframe']

                    # Ranking da etapa
                    ranking = df.dropna(subset=['Lap_Sec']).groupby('Nome_Piloto').agg({
                        'Lap_Sec': 'min',
                        'Equipe': 'first',
                        'Montadora': 'first'
                    }).reset_index()

                    ranking = ranking.sort_values('Lap_Sec')
                    ranking['Posição'] = range(1, len(ranking) + 1)
                    ranking['Pontos'] = ranking['Posição'].apply(calcular_pontos_campeonato)

                    # Acumular pontos
                    for _, row in ranking.iterrows():
                        piloto = row['Nome_Piloto']
                        if piloto not in pontos_campeonato:
                            pontos_campeonato[piloto] = {
                                'pontos_total': 0,
                                'equipe': row['Equipe'],
                                'montadora': row['Montadora'],
                                'vitorias': 0,
                                'podios': 0,
                                'etapas': 0
                            }

                        pontos_campeonato[piloto]['pontos_total'] += row['Pontos']
                        pontos_campeonato[piloto]['etapas'] += 1

                        if row['Posição'] == 1:
                            pontos_campeonato[piloto]['vitorias'] += 1
                        if row['Posição'] <= 3:
                            pontos_campeonato[piloto]['podios'] += 1

                    etapas_pontuacao.append(dados['etapa'])

            if pontos_campeonato:
                # Criar dataframe do campeonato
                dados_campeonato = []
                for piloto, stats in pontos_campeonato.items():
                    dados_campeonato.append({
                        'Piloto': piloto,
                        'Pontos': stats['pontos_total'],
                        'Equipe': stats['equipe'],
                        'Montadora': stats['montadora'],
                        'Vitórias': stats['vitorias'],
                        'Pódios': stats['podios'],
                        'Etapas': stats['etapas'],
                        'Média': stats['pontos_total'] / stats['etapas'] if stats['etapas'] > 0 else 0
                    })

                df_campeonato = pd.DataFrame(dados_campeonato)
                df_campeonato = df_campeonato.sort_values('Pontos', ascending=False)
                df_campeonato['Posição'] = range(1, len(df_campeonato) + 1)

                # Gráfico do campeonato
                fig_campeonato = go.Figure()

                cores_camp = ['#FFD700' if i == 1 else '#C0C0C0' if i == 2 else '#CD7F32' if i == 3 else '#4682B4' 
                             for i in df_campeonato['Posição']]

                fig_campeonato.add_trace(go.Bar(
                    x=df_campeonato['Piloto'],
                    y=df_campeonato['Pontos'],
                    marker_color=cores_camp,
                    text=df_campeonato['Pontos'],
                    textposition='outside'
                ))

                fig_campeonato.update_layout(
                    title=f'🏆 Classificação do Campeonato ({len(etapas_pontuacao)} etapas)',
                    xaxis_title='Pilotos',
                    yaxis_title='Pontos',
                    height=600
                )

                st.plotly_chart(fig_campeonato, use_container_width=True)

                # Tabela do campeonato
                st.dataframe(df_campeonato, hide_index=True, use_container_width=True)

                # Estatísticas do campeonato
                st.subheader("📊 Estatísticas do Campeonato")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    lider = df_campeonato.iloc[0]
                    st.metric("Líder", lider['Piloto'], f"{lider['Pontos']} pts")

                with col2:
                    diferenca_lider = df_campeonato.iloc[1]['Pontos'] - df_campeonato.iloc[0]['Pontos'] if len(df_campeonato) > 1 else 0
                    st.metric("Diferença para 2º", f"{diferenca_lider} pts")

                with col3:
                    maior_vencedor = df_campeonato.loc[df_campeonato['Vitórias'].idxmax()]
                    st.metric("Mais vitórias", f"{maior_vencedor['Piloto']} ({maior_vencedor['Vitórias']})")

                with col4:
                    st.metric("Etapas computadas", len(etapas_pontuacao))

            else:
                st.info("💡 Nenhuma etapa com pontuação foi importada ainda")

elif secao == "🎯 Sistema de Referências":
    st.header("🎯 Sistema Avançado de Referências")

    st.markdown("""
    Configure tempos de referência para comparações precisas entre diferentes sessões e etapas.
    Use para análise de evolução de performance e benchmarking.
    """)

    tab1, tab2 = st.tabs(["➕ Criar Referência", "📋 Gerenciar Referências"])

    with tab1:
        st.subheader("➕ Criar Nova Referência")

        # Opções de criação de referência
        opcao_ref = st.radio(
            "Como criar a referência:",
            ["📊 A partir de dados existentes", "✏️ Inserção manual", "📈 Melhor tempo de etapa"]
        )

        if opcao_ref == "📊 A partir de dados existentes":
            if st.session_state.dados_etapas_completo:
                etapa_ref = st.selectbox("Etapa de origem:", list(st.session_state.dados_etapas_completo.keys()))

                dados_etapa = st.session_state.dados_etapas_completo[etapa_ref]
                df = dados_etapa['dataframe']

                if 'Nome_Piloto' in df.columns:
                    piloto_ref = st.selectbox("Piloto de referência:", df['Nome_Piloto'].unique())
                    nome_ref = st.text_input("Nome da referência:", f"{piloto_ref}_{dados_etapa['etapa']}")

                    if st.button("💾 Salvar Referência dos Dados"):
                        dados_piloto = df[df['Nome_Piloto'] == piloto_ref]

                        if not dados_piloto.empty:
                            referencia = {
                                'nome': nome_ref,
                                'piloto': piloto_ref,
                                'etapa_origem': dados_etapa['etapa'],
                                'sessao_origem': dados_etapa['sessao'],
                                'pista': dados_etapa['pista'],
                                'data_criacao': datetime.now()
                            }

                            # Adicionar tempos se disponíveis
                            if 'Lap_Sec' in dados_piloto.columns:
                                melhor_volta = dados_piloto['Lap_Sec'].min()
                                referencia['volta_referencia'] = melhor_volta

                            # Adicionar setores se disponíveis
                            for i, setor in enumerate(['S1_Sec', 'S2_Sec', 'S3_Sec'], 1):
                                if setor in dados_piloto.columns:
                                    melhor_setor = dados_piloto[setor].min()
                                    referencia[f'setor{i}_referencia'] = melhor_setor

                            # Adicionar velocidades se disponíveis
                            if 'Speed_Trap_Kmh' in dados_piloto.columns:
                                max_speed = dados_piloto['Speed_Trap_Kmh'].max()
                                referencia['speed_trap_referencia'] = max_speed

                            st.session_state.dados_referencia_completo[nome_ref] = referencia
                            st.success(f"✅ Referência '{nome_ref}' criada com sucesso!")

            else:
                st.info("💡 Importe dados primeiro para criar referências")

        elif opcao_ref == "✏️ Inserção manual":
            st.subheader("✏️ Inserção Manual de Referência")

            with st.form("form_ref_manual"):
                nome_manual = st.text_input("Nome da referência:")
                piloto_manual = st.selectbox("Piloto:", list(MAPEAMENTO_COMPLETO_PILOTOS.keys()))
                pista_manual = st.selectbox("Pista:", list(PISTAS_OFICIAIS_COMPLETAS.keys()))

                col1, col2 = st.columns(2)

                with col1:
                    volta_manual = st.text_input("Tempo de volta (MM:SS.sss):", "1:30.000")
                    s1_manual = st.text_input("Setor 1:", "28.500")
                    s2_manual = st.text_input("Setor 2:", "31.250")

                with col2:
                    s3_manual = st.text_input("Setor 3:", "30.250")
                    speed_manual = st.text_input("Speed trap (km/h):", "200.0")
                    obs_manual = st.text_area("Observações:")

                if st.form_submit_button("💾 Salvar Referência Manual"):
                    if nome_manual:
                        referencia_manual = {
                            'nome': nome_manual,
                            'piloto': piloto_manual,
                            'pista': pista_manual,
                            'tipo': 'Manual',
                            'data_criacao': datetime.now(),
                            'observacoes': obs_manual
                        }

                        # Converter tempos
                        referencia_manual['volta_referencia'] = converter_tempo_para_segundos_completo(volta_manual)
                        referencia_manual['setor1_referencia'] = converter_tempo_para_segundos_completo(s1_manual)
                        referencia_manual['setor2_referencia'] = converter_tempo_para_segundos_completo(s2_manual)
                        referencia_manual['setor3_referencia'] = converter_tempo_para_segundos_completo(s3_manual)
                        referencia_manual['speed_trap_referencia'] = float(speed_manual) if speed_manual else None

                        st.session_state.dados_referencia_completo[nome_manual] = referencia_manual
                        st.success(f"✅ Referência manual '{nome_manual}' criada!")

    with tab2:
        st.subheader("📋 Gerenciar Referências Existentes")

        if st.session_state.dados_referencia_completo:
            for nome_ref, dados_ref in st.session_state.dados_referencia_completo.items():
                with st.expander(f"📊 {nome_ref}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Piloto:** {dados_ref.get('piloto', 'N/A')}")
                        st.write(f"**Pista:** {dados_ref.get('pista', 'N/A')}")
                        if 'etapa_origem' in dados_ref:
                            st.write(f"**Etapa origem:** {dados_ref['etapa_origem']}")
                            st.write(f"**Sessão origem:** {dados_ref.get('sessao_origem', 'N/A')}")

                    with col2:
                        if 'volta_referencia' in dados_ref:
                            st.write(f"**Volta:** {formatar_tempo_completo(dados_ref['volta_referencia'])}")

                        for i in range(1, 4):
                            if f'setor{i}_referencia' in dados_ref:
                                st.write(f"**S{i}:** {formatar_tempo_completo(dados_ref[f'setor{i}_referencia'])}")

                        if 'speed_trap_referencia' in dados_ref:
                            st.write(f"**Speed trap:** {dados_ref['speed_trap_referencia']:.1f} km/h")

                    if st.button(f"🗑️ Remover {nome_ref}", key=f"remove_{nome_ref}"):
                        del st.session_state.dados_referencia_completo[nome_ref]
                        st.success(f"Referência '{nome_ref}' removida!")
                        st.experimental_rerun()

        else:
            st.info("💡 Nenhuma referência criada ainda")

elif secao == "📋 Relatórios Executivos":
    st.header("📋 Relatórios Executivos")

    if not st.session_state.dados_etapas_completo:
        st.warning("⚠️ Importe dados do Chronon primeiro")
    else:
        st.subheader("📊 Geração de Relatórios Avançados")

        tipo_relatorio = st.selectbox(
            "Tipo de Relatório:",
            ["👤 Relatório Individual de Piloto", "🏭 Relatório por Montadora", 
             "👥 Relatório por Equipe", "🏁 Relatório de Etapa", "📈 Relatório de Performance"]
        )

        if tipo_relatorio == "👤 Relatório Individual de Piloto":
            # Consolidar todos os pilotos
            todos_pilotos = set()
            for dados in st.session_state.dados_etapas_completo.values():
                if 'Nome_Piloto' in dados['dataframe'].columns:
                    todos_pilotos.update(dados['dataframe']['Nome_Piloto'].unique())

            piloto_relatorio = st.selectbox("Selecione o piloto:", sorted(todos_pilotos))

            if st.button("📋 Gerar Relatório do Piloto"):
                st.subheader(f"📊 Relatório Completo - {piloto_relatorio}")

                # Informações básicas
                if piloto_relatorio in MAPEAMENTO_COMPLETO_PILOTOS:
                    info_piloto = MAPEAMENTO_COMPLETO_PILOTOS[piloto_relatorio]

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Equipe:** {info_piloto['Equipe']}")
                    with col2:
                        st.write(f"**Montadora:** {info_piloto['Montadora']}")
                    with col3:
                        st.write(f"**Número:** #{info_piloto['Numero']}")

                # Análise por etapa
                dados_piloto_completo = []

                for chave_etapa, dados_etapa in st.session_state.dados_etapas_completo.items():
                    df = dados_etapa['dataframe']

                    if piloto_relatorio in df['Nome_Piloto'].values:
                        relatorio_etapa = gerar_relatorio_completo_piloto(df, piloto_relatorio)

                        if relatorio_etapa:
                            relatorio_etapa['etapa'] = dados_etapa['etapa']
                            relatorio_etapa['sessao'] = dados_etapa['sessao']
                            relatorio_etapa['pista'] = dados_etapa['pista']
                            dados_piloto_completo.append(relatorio_etapa)

                if dados_piloto_completo:
                    # Resumo geral
                    st.subheader("📊 Resumo Geral")

                    total_etapas = len(dados_piloto_completo)
                    total_voltas = sum(d['total_voltas'] for d in dados_piloto_completo)

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Etapas Participadas", total_etapas)

                    with col2:
                        st.metric("Total de Voltas", total_voltas)

                    with col3:
                        melhores_voltas = [d['melhor_volta'] for d in dados_piloto_completo if 'melhor_volta' in d]
                        if melhores_voltas:
                            melhor_absoluto = min(melhores_voltas)
                            st.metric("Melhor Volta Absoluta", formatar_tempo_completo(melhor_absoluto))

                    with col4:
                        velocidades_max = [d['velocidade_maxima'] for d in dados_piloto_completo if 'velocidade_maxima' in d]
                        if velocidades_max:
                            vel_max_absoluta = max(velocidades_max)
                            st.metric("Velocidade Máxima", f"{vel_max_absoluta:.1f} km/h")

                    # Evolução por etapa
                    if len(dados_piloto_completo) > 1:
                        st.subheader("📈 Evolução por Etapa")

                        df_evolucao = pd.DataFrame(dados_piloto_completo)

                        if 'melhor_volta' in df_evolucao.columns:
                            fig_evolucao = px.line(
                                df_evolucao,
                                x='etapa',
                                y='melhor_volta',
                                title=f'Evolução de Performance - {piloto_relatorio}',
                                markers=True
                            )

                            st.plotly_chart(fig_evolucao, use_container_width=True)

                    # Tabela detalhada por etapa
                    st.subheader("📋 Detalhamento por Etapa")

                    tabela_piloto = pd.DataFrame(dados_piloto_completo)

                    # Formatar colunas
                    if 'melhor_volta' in tabela_piloto.columns:
                        tabela_piloto['Melhor Volta'] = [formatar_tempo_completo(t) for t in tabela_piloto['melhor_volta']]

                    if 'velocidade_maxima' in tabela_piloto.columns:
                        tabela_piloto['Vel. Máxima'] = [f"{v:.1f} km/h" for v in tabela_piloto['velocidade_maxima']]

                    if 'consistencia' in tabela_piloto.columns:
                        tabela_piloto['Consistência'] = [f"{c:.3f}s" for c in tabela_piloto['consistencia']]

                    colunas_mostrar = ['etapa', 'sessao', 'pista', 'total_voltas']

                    if 'Melhor Volta' in tabela_piloto.columns:
                        colunas_mostrar.append('Melhor Volta')
                    if 'Vel. Máxima' in tabela_piloto.columns:
                        colunas_mostrar.append('Vel. Máxima')
                    if 'Consistência' in tabela_piloto.columns:
                        colunas_mostrar.append('Consistência')

                    st.dataframe(tabela_piloto[colunas_mostrar], hide_index=True, use_container_width=True)

                else:
                    st.info(f"💡 Nenhum dado encontrado para {piloto_relatorio}")

elif secao == "📤 Exportar Dados":
    st.header("📤 Exportação de Dados")

    if not st.session_state.dados_etapas_completo:
        st.warning("⚠️ Importe dados do Chronon primeiro")
    else:
        st.subheader("💾 Exportar Dados Processados")

        # Seletor de etapa para exportar
        etapa_exportar = st.selectbox("Selecione etapa para exportar:", list(st.session_state.dados_etapas_completo.keys()))

        dados_etapa = st.session_state.dados_etapas_completo[etapa_exportar]
        df = dados_etapa['dataframe']

        # Opções de exportação
        formato_export = st.selectbox("Formato de exportação:", ["CSV", "Excel", "JSON"])

        incluir_processados = st.checkbox("Incluir dados processados (tempos em segundos)", value=True)
        incluir_originais = st.checkbox("Incluir dados originais do Chronon", value=True)

        if st.button("📥 Preparar Download"):
            # Preparar dados para exportação
            df_export = df.copy()

            if not incluir_originais:
                # Remover colunas originais do Chronon
                colunas_chronon = ['Time of Day', 'Lap', 'Lap Tm', 'Speed', 'Hits', 'Strength', 'Noise', 'S1', 'S1 Tm', 'S2', 'S2 Tm', 'S3', 'S3 Tm', 'SPT', 'SPT Tm']
                colunas_remover = [col for col in colunas_chronon if col in df_export.columns]
                df_export = df_export.drop(columns=colunas_remover)

            if not incluir_processados:
                # Remover colunas processadas
                colunas_processadas = ['Lap_Sec', 'S1_Sec', 'S2_Sec', 'S3_Sec', 'Speed_Kmh', 'Speed_Trap_Kmh']
                colunas_remover = [col for col in colunas_processadas if col in df_export.columns]
                df_export = df_export.drop(columns=colunas_remover)

            # Nome do arquivo
            nome_arquivo = f"{dados_etapa['temporada']}_{dados_etapa['etapa']}_{dados_etapa['sessao']}"
            nome_arquivo = nome_arquivo.replace(' ', '_').replace('#', '').replace('/', '-')

            if formato_export == "CSV":
                csv = df_export.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="{nome_arquivo}.csv">📥 Baixar CSV</a>'
                st.markdown(href, unsafe_allow_html=True)

            elif formato_export == "Excel":
                # Para Excel, seria necessário usar openpyxl ou xlsxwriter
                st.info("💡 Exportação Excel em desenvolvimento. Use CSV por enquanto.")

            elif formato_export == "JSON":
                json_str = df_export.to_json(orient='records', indent=2)
                b64 = base64.b64encode(json_str.encode()).decode()
                href = f'<a href="data:file/json;base64,{b64}" download="{nome_arquivo}.json">📥 Baixar JSON</a>'
                st.markdown(href, unsafe_allow_html=True)

            # Preview dos dados
            st.subheader("👀 Preview dos dados a exportar")
            st.dataframe(df_export.head(10), use_container_width=True)
            st.write(f"**Total de registros:** {len(df_export)} | **Colunas:** {len(df_export.columns)}")

elif secao == "⚙️ Configurações Avançadas":
    st.header("⚙️ Configurações Avançadas")

    tab1, tab2, tab3 = st.tabs(["🎨 Interface", "📊 Dados", "🔧 Sistema"])

    with tab1:
        st.subheader("🎨 Configurações da Interface")

        # Configurações de tema
        tema_cores = st.selectbox(
            "Tema de cores:",
            ["Padrão Stock Car", "Modo Escuro", "Alto Contraste", "Personalizado"]
        )

        # Configurações de gráficos
        altura_graficos = st.slider("Altura padrão dos gráficos:", 300, 800, 500)

        mostrar_animacoes = st.checkbox("Mostrar animações nos gráficos", value=True)

        # Salvar configurações
        if st.button("💾 Salvar Configurações de Interface"):
            st.session_state.configuracoes_usuario.update({
                'tema_cores': tema_cores,
                'altura_graficos': altura_graficos,
                'mostrar_animacoes': mostrar_animacoes
            })
            st.success("✅ Configurações salvas!")

    with tab2:
        st.subheader("📊 Configurações de Dados")

        # Configurações de importação
        validacao_rigorosa = st.checkbox("Validação rigorosa na importação", value=True)

        # Configurações de precisão
        precisao_tempo = st.selectbox("Precisão de tempo:", ["Milissegundos (0.001s)", "Centésimos (0.01s)", "Décimos (0.1s)"], index=0)

        # Configurações de cache
        tamanho_cache = st.slider("Tamanho do cache (MB):", 50, 500, 100)

        if st.button("💾 Salvar Configurações de Dados"):
            st.session_state.configuracoes_usuario.update({
                'validacao_rigorosa': validacao_rigorosa,
                'precisao_tempo': precisao_tempo,
                'tamanho_cache': tamanho_cache
            })
            st.success("✅ Configurações de dados salvas!")

    with tab3:
        st.subheader("🔧 Configurações do Sistema")

        # Informações do sistema
        st.write("**Versão:** Stock Car Analytics Pro v2.0 Complete Edition")
        st.write("**Baseado em:** Dados oficiais do Chronon.com.br")
        st.write("**Última atualização:** Outubro 2025")

        # Limpeza de dados
        if st.button("🧹 Limpar todos os dados", type="secondary"):
            if st.button("⚠️ CONFIRMAR LIMPEZA (não pode ser desfeita)"):
                st.session_state.dados_etapas_completo.clear()
                st.session_state.dados_referencia_completo.clear()
                st.session_state.historico_analises.clear()
                st.success("✅ Todos os dados foram limpos!")
                st.experimental_rerun()

        # Reset configurações
        if st.button("🔄 Reset Configurações"):
            st.session_state.configuracoes_usuario.clear()
            st.success("✅ Configurações resetadas!")

        # Estatísticas do sistema
        st.subheader("📊 Estatísticas do Sistema")

        if st.session_state.dados_etapas_completo:
            total_registros = sum(len(dados['dataframe']) for dados in st.session_state.dados_etapas_completo.values())
            st.write(f"**Total de registros:** {total_registros:,}")

            todos_pilotos = set()
            for dados in st.session_state.dados_etapas_completo.values():
                if 'Nome_Piloto' in dados['dataframe'].columns:
                    todos_pilotos.update(dados['dataframe']['Nome_Piloto'].unique())

            st.write(f"**Pilotos únicos:** {len(todos_pilotos)}")
            st.write(f"**Etapas carregadas:** {len(st.session_state.dados_etapas_completo)}")
            st.write(f"**Referências:** {len(st.session_state.dados_referencia_completo)}")

# Footer completo
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center;">
        <h3>🏎️ Stock Car Analytics Pro v2.0 - Complete Edition</h3>
        <p><strong>Sistema Oficial baseado em dados do Chronon.com.br - Audace Tech</strong></p>
        <p>Desenvolvido para análise profissional de performance em Stock Car</p>
    </div>
    """, 
    unsafe_allow_html=True
)

# Status do sistema no footer
if st.session_state.dados_etapas_completo:
    total_voltas = sum(len(dados['dataframe']) for dados in st.session_state.dados_etapas_completo.values())
    todos_pilotos = set()
    for dados in st.session_state.dados_etapas_completo.values():
        if 'Nome_Piloto' in dados['dataframe'].columns:
            todos_pilotos.update(dados['dataframe']['Nome_Piloto'].unique())

    st.markdown(f"*📊 Sistema carregado com {len(st.session_state.dados_etapas_completo)} etapas • {total_voltas} voltas • {len(todos_pilotos)} pilotos únicos*")
