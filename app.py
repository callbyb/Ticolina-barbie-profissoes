import streamlit as st
import pandas as pd
import pulp
import calendar
import io
import json
import os

st.set_page_config(layout="wide", page_title="Escala Hospitalar Profissional")

# --- SISTEMA DE ARQUIVOS (SALVAMENTO PERMANENTE) ---
FILE_CONFIG = "config_escala.json"

def carregar_config():
    if os.path.exists(FILE_CONFIG):
        with open(FILE_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "tecnicos": "Andrea Rosalem, Angela Alberto dos Santos, Anivalda Caetano Gama, Bianca de Paula Rosa, Carla Maria Beck da Silva, Edicleide de Lima Silva, Fabiana de Alcantara Fernandes, Maria Ronilda Pereira Paz, Marinês Guimarães dos Santos Xavier, Marlúcia Gil de Sousa Louzada, Renata Aparecida Ribeiro, Marizete Cerqueira M. Santos, Pablo Henrique Ferreira da Silva, Rosimeire Alves Andrade Borges, Vanessa Pires de Souza, Vanuza Gonçalves Pereira",
        "enfermeiros": "Graciele Katia da Silva Camargo, Heloisa Gonçalves Silva, Kelly Priscila Azevedo Rodrigues, Larissa Aguiar de Sousa, Jessica Cristina Moraes De Souza, Raquel Rodrigues de Souza, Natalia Caitano de Lima Costa, Thaís Rodrigues Alves, Debora Maria Alves Gregorio, Veronica Martz Venancio da Silva",
        "incompativeis_tec": "Andrea-Bianca",
        "incompativeis_enf": ""
    }

def salvar_config(dados):
    with open(FILE_CONFIG, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

config = carregar_config()

st.title("Gestão de Escala Hospitalar")

# --- DATA E TIPO DE PLANTÃO ---
col_cfg1, col_cfg2 = st.columns(2)
with col_cfg1:
    mes = st.number_input("Mês", min_value=1, max_value=12, value=4)
    ano = st.number_input("Ano", min_value=2024, max_value=2030, value=2026)
with col_cfg2:
    tipo_dias = st.radio("Dias do Plantão", ["Pares", "Ímpares", "Todos"], horizontal=True)

_, num_dias = calendar.monthrange(ano, mes)
dias_mes = list(range(1, num_dias + 1))
dias_plantao = [d for d in dias_mes if (tipo_dias == "Pares" and d % 2 == 0) or (tipo_dias == "Ímpares" and d % 2 != 0) or (tipo_dias == "Todos")]

# --- ABAS ---
tab_escala, tab_folgas, tab_config = st.tabs(["📅 Gerar Escala", "🏥 Folgas e Proibições", "⚙️ Configurações Mestres"])

with tab_config:
    st.subheader("Configurações Permanentes")
    col_c1, col_c2 = st.columns(2)
    new_tec = col_c1.text_area("Nomes (Técnicos):", value=config["tecnicos"], height=150)
    new_inc_tec = col_c1.text_area("Incompatíveis (Técnicos):", value=config.get("incompativeis_tec", ""), height=100)
    new_enf = col_c2.text_area("Nomes (Enfermeiros):", value=config["enfermeiros"], height=150)
    new_inc_enf = col_c2.text_area("Incompatíveis (Enfermeiros):", value=config.get("incompativeis_enf", ""), height=100)
    if st.button("💾 Salvar Alterações"):
        salvar_config({"tecnicos": new_tec, "enfermeiros": new_enf, "incompativeis_tec": new_inc_tec, "incompativeis_enf": new_inc_enf})
        st.rerun()

tecnicos_nomes = [n.strip() for n in new_tec.split(",") if n.strip()]
enfermeiros_nomes = [n.strip() for n in new_enf.split(",") if n.strip()]
def processar_pares(t): return [tuple(p.split("-")) for p in [i.strip() for i in t.split(",") if i.strip()] if "-" in p]
inc_tec = processar_pares(new_inc_tec); inc_enf = processar_pares(new_inc_enf)

# --- SETORES ---
setores_tec = {
    "Puerpério": {"vagas": 2, "sigla": "P", "max": 2, "co": True},
    "Recém-nascido": {"vagas": 1, "sigla": "RN", "max": 2, "co": True},
    "Pré-parto": {"vagas": 1, "sigla": "PP", "max": 2, "co": True},
    "Patologia": {"vagas": 1, "sigla": "PATO", "max": 2, "co": True},
    "Observação": {"vagas": 2, "sigla": "OBS", "max": 2, "co": False},
    "Medicação": {"vagas": 2, "sigla": "MED", "max": 2, "co": False},
    "Sala 6": {"vagas": 1, "sigla": "S6", "max": 2, "co": True},
    "Sala 7": {"vagas": 1, "sigla": "S7", "max": 2, "co": True}
}

setores_enf = {
    "Acolhimento e Classificação de Risco": {"vagas": 1, "sigla": "ACCR", "max": 2, "co": False},
    "Cardiotocografia": {"vagas": 1, "sigla": "CTB", "max": 2, "co": False},
    "Observação": {"vagas": 1, "sigla": "OBS", "max": 2, "co": False},
    "Pré-parto": {"vagas": 1, "sigla": "PP", "max": 2, "co": True},
    "Patologia": {"vagas": 1, "sigla": "PATO", "max": 2, "co": True},
    "Recém-nascido": {"vagas": 1, "sigla": "RN", "max": 2, "co": True}
}

# --- FOLGAS ---
folgas_tec = {}; rest_tec = {}; folgas_enf = {}; rest_enf = {}
with tab_folgas:
    sub_t, sub_e = st.tabs(["🩺 Técnicos", "👩‍⚕️ Enfermeiros"])
    with sub_t:
        for f in tecnicos_nomes:
            c1, c2 = st.columns(2)
            folgas_tec[f] = c1.multiselect(f"Folgas {f}", dias_plantao, key=f"f_t_{f}")
            rest_tec[f] = c2.multiselect(f"Proibidos {f}", list(setores_tec.keys()) + ["Apoio"], key=f"r_t_{f}")
    with sub_e:
        for f in enfermeiros_nomes:
            c1, c2 = st.columns(2)
            folgas_enf[f] = c1.multiselect(f"Folgas {f}", dias_plantao, key=f"f_e_{f}")
            rest_enf[f] = c2.multiselect(f"Proibidos {f}", list(setores_enf.keys()) + ["Apoio"], key=f"r_e_{f}")

# --- DIAGNÓSTICO PRÉ-CÁLCULO ---
def verificar_viabilidade(nomes, dias, folgas, setores_dict, label):
    vagas_por_dia = sum(s["vagas"] for s in setores_dict.values())
    for d in dias:
        disponiveis = [f for f in nomes if d not in folgas[f]]
        if len(disponiveis) < vagas_por_dia:
            st.error(f"🚨 **FALTA DE PESSOAL NO DIA {d:02d} ({label}):** Precisamos de {vagas_por_dia} funcionários para preencher os setores, mas apenas {len(disponiveis)} não estão de folga. Remova folgas desse dia.")
            return False
    return True

# --- MOTOR DE CÁLCULO FLEXÍVEL ---
def resolver_escala(nomes, setores_dict, folgas_dict, rest_dict, incompativeis, is_enf=False):
    if not nomes: return None, None
    prob = pulp.LpProblem("Escala", pulp.LpMinimize)
    setores_list = list(setores_dict.keys())
    
    x = pulp.LpVariable.dicts("x", [(f, d, s) for f in nomes for d in dias_plantao for s in setores_list], cat='Binary')
    
    # Variáveis de Penalidade (Tornam a escala flexível sem travar)
    passou = pulp.LpVariable.dicts("passou", [(f, s) for f in nomes for s in setores_list], cat='Binary')
    excedeu = pulp.LpVariable.dicts("excedeu", [(f, s) for f in nomes for s in setores_list], lowBound=0, cat='Integer')
    quebra_janela = pulp.LpVariable.dicts("quebra_janela", [(f, d, s) for f in nomes for d in dias_plantao for s in setores_list], lowBound=0, cat='Integer')
    rep_seg = pulp.LpVariable.dicts("rep_seg", [(f, d, s) for f in nomes for d in dias_plantao for s in setores_list], lowBound=0, cat='Integer')
    excesso_co = pulp.LpVariable.dicts("excesso_co", [(f, d) for f in nomes for d in dias_plantao], lowBound=0, cat='Integer')

    # RN para enfermeiros NÃO entra na premiação de rotatividade
    setores_rotacao = [s for s in setores_list if not (is_enf and s == "Recém-nascido")]

    # O sistema tenta evitar as penalidades, mas se for a unica opção (ex: Veronica), ele aceita e gera a escala.
    prob += -pulp.lpSum([passou[(f, s)] * 1000 for f in nomes for s in setores_rotacao]) + \
            pulp.lpSum([excedeu[(f, s)] * 500 for f in nomes for s in setores_list]) + \
            pulp.lpSum([quebra_janela[(f, d, s)] * 1000 for f in nomes for d in dias_plantao for s in setores_list]) + \
            pulp.lpSum([rep_seg[(f, d, s)] * 3000 for f in nomes for d in dias_plantao for s in setores_list]) + \
            pulp.lpSum([excesso_co[(f, d)] * 3000 for f in nomes for d in dias_plantao])

    # Regra Dura: As vagas precisam ser preenchidas
    for d in dias_plantao:
        for s in setores_list:
            prob += pulp.lpSum([x[(f, d, s)] for f in nomes]) == setores_dict[s]["vagas"]

    # Atribuição de Proibições e Folgas
    for f in nomes:
        for s in setores_list:
            prob += passou[(f, s)] <= pulp.lpSum([x[(f, d, s)] for d in dias_plantao])
            prob += pulp.lpSum([x[(f, d, s)] for d in dias_plantao]) - setores_dict[s]["max"] <= excedeu[(f, s)]

        for d in dias_plantao:
            if d in folgas_dict[f]:
                prob += pulp.lpSum([x[(f, d, s)] for s in setores_list]) == 0
            elif "Apoio" in rest_dict[f]:
                prob += pulp.lpSum([x[(f, d, s)] for s in setores_list]) == 1
            else:
                prob += pulp.lpSum([x[(f, d, s)] for s in setores_list]) <= 1

            for s_p in rest_dict[f]:
                if s_p in setores_list: prob += x[(f, d, s_p)] == 0

    for f1, f2 in incompativeis:
        if f1 in nomes and f2 in nomes:
            for d in dias_plantao:
                for s in setores_list: prob += x[(f1, d, s)] + x[(f2, d, s)] <= 1

    # Regras Flexíveis (Permitem repetição se for estritamente necessário)
    setores_co = [s for s in setores_list if setores_dict[s]["co"]]
    for f in nomes:
        for s in setores_list:
            for i in range(len(dias_plantao) - 1): 
                prob += x[(f, dias_plantao[i], s)] + x[(f, dias_plantao[i+1], s)] - 1 <= rep_seg[(f, dias_plantao[i], s)]
            for i in range(len(dias_plantao) - 3):
                prob += pulp.lpSum([x[(f, dias_plantao[i+k], s)] for k in range(min(4, len(dias_plantao)-i))]) - 1 <= quebra_janela[(f, dias_plantao[i], s)]
        for i in range(len(dias_plantao) - 2):
            prob += pulp.lpSum([x[(f, dias_plantao[i+k], s)] for k in range(3) for s in setores_co]) - 2 <= excesso_co[(f, dias_plantao[i])]

    prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=60))
    return prob, x

with tab_escala:
    if st.button("🚀 Gerar Escalas", type="primary"):
        # Verificando se há gente suficiente antes de tentar calcular
        v_t = verificar_viabilidade(tecnicos_nomes, dias_plantao, folgas_tec, setores_tec, "Técnicos")
        v_e = verificar_viabilidade(enfermeiros_nomes, dias_plantao, folgas_enf, setores_enf, "Enfermeiros")
        
        if v_t and v_e:
            with st.spinner("Processando..."):
                st_t, res_t = resolver_escala(tecnicos_nomes, setores_tec, folgas_tec, rest_tec, inc_tec)
                st_e, res_e = resolver_escala(enfermeiros_nomes, setores_enf, folgas_enf, rest_enf, inc_enf, is_enf=True)
                
                if (st_t and st_t.status > 0) or (st_e and st_e.status > 0):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        if st_t and st_t.status > 0:
                            df_t = pd.DataFrame(index=tecnicos_nomes, columns=[f"{d:02d}/{mes:02d}" for d in dias_plantao])
                            for f in tecnicos_nomes:
                                for d in dias_plantao:
                                    if d in folgas_tec[f]: df_t.at[f, f"{d:02d}/{mes:02d}"] = "F"
                                    else:
                                        at = False
                                        for s in setores_tec:
                                            if pulp.value(res_t[(f, d, s)]) == 1: df_t.at[f, f"{d:02d}/{mes:02d}"] = setores_tec[s]["sigla"]; at = True
                                        if not at: df_t.at[f, f"{d:02d}/{mes:02d}"] = "APOIO"
                            st.write("### Técnicos"); st.dataframe(df_t.reset_index(), use_container_width=True); df_t.to_excel(writer, sheet_name='Técnicos')
                        if st_e and st_e.status > 0:
                            df_e = pd.DataFrame(index=enfermeiros_nomes, columns=[f"{d:02d}/{mes:02d}" for d in dias_plantao])
                            for f in enfermeiros_nomes:
                                for d in dias_plantao:
                                    if d in folgas_enf[f]: df_e.at[f, f"{d:02d}/{mes:02d}"] = "F"
                                    else:
                                        at = False
                                        for s in setores_enf:
                                            if pulp.value(res_e[(f, d, s)]) == 1: df_e.at[f, f"{d:02d}/{mes:02d}"] = setores_enf[s]["sigla"]; at = True
                                        if not at: df_e.at[f, f"{d:02d}/{mes:02d}"] = "APOIO"
                            st.write("### Enfermeiros"); st.dataframe(df_e.reset_index(), use_container_width=True); df_e.to_excel(writer, sheet_name='Enfermeiros')
                    st.download_button("📥 Baixar Excel", output.getvalue(), f"escala_{mes}_{ano}.xlsx")
                else:
                    st.error("ERRO: A combinação de folgas e proibições de setores tornou a escala impossível. Verifique se alguém tem muitas proibições de setores.")