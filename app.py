import streamlit as st
import pandas as pd
import pulp
import calendar
import io
import json
import os

st.set_page_config(layout="wide", page_title="Escala Hospitalar Profissional")

# --- SISTEMA DE PERSISTÊNCIA ---
FILE_CONFIG = "config_escala.json"

def carregar_config():
    # Deixei os dados dos seus PDFs como padrão aqui 
    padrao = {
        "tecnicos": "Andrea Rosalem, Angela Alberto dos Santos, Anivalda Caetano Gama, Bianca de Paula Rosa, Carla Maria Beck da Silva, Edicleide de Lima Silva, Fabiana de Alcantara Fernandes, Maria Ronilda Pereira Paz, Marinês Guimarães dos Santos Xavier, Marlúcia Gil de Sousa Louzada, Renata Aparecida Ribeiro, Marizete Cerqueira M. Santos, Pablo Henrique Ferreira da Silva, Rosimeire Alves Andrade Borges, Vanessa Pires de Souza, Vanuza Gonçalves Pereira",
        "enfermeiros": "Graciele Katia da Silva Camargo, Heloisa Gonçalves Silva, Kelly Priscila Azevedo Rodrigues, Larissa Aguiar de Sousa, Jessica Cristina Moraes De Souza, Raquel Rodrigues de Souza, Natalia Caitano de Lima Costa, Thaís Rodrigues Alves, Debora Maria Alves Gregorio, Veronica Martz Venancio da Silva",
        "incompativeis_tec": "Andrea Rosalem-Bianca de Paula Rosa",
        "incompativeis_enf": "",
        "mes": 4, "ano": 2026, "tipo_dias": "Todos",
        # Folgas extraídas do seu PDF [cite: 110, 114, 121, 123, 125, 127, 130, 148, 150, 152, 154, 157, 159, 164, 166, 168]
        "folgas_tec": {
            "Andrea Rosalem": [10, 18, 28], "Angela Alberto dos Santos": [4, 14, 28], "Anivalda Caetano Gama": [12, 20, 22],
            "Bianca de Paula Rosa": [2, 16, 30], "Carla Maria Beck da Silva": [8, 18, 30], "Edicleide de Lima Silva": [8, 12, 28],
            "Fabiana de Alcantara Fernandes": [8, 14, 26], "Maria Ronilda Pereira Paz": [6, 14, 26], "Marinês Guimarães dos Santos Xavier": [2, 18, 22],
            "Marlúcia Gil de Sousa Louzada": [4, 20, 24], "Renata Aparecida Ribeiro": [10, 24, 26, 28], "Marizete Cerqueira M. Santos": [2, 12, 30],
            "Pablo Henrique Ferreira da Silva": [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30], "Rosimeire Alves Andrade Borges": [10, 16, 30],
            "Vanessa Pires de Souza": [2, 4, 20], "Vanuza Gonçalves Pereira": [5, 16, 22]
        },
        "rest_tec": {
            "Carla Maria Beck da Silva": ["Recém-nascido"],
            "Rosimeire Alves Andrade Borges": ["Recém-nascido", "Pré-parto", "Patologia", "Sala 6", "Sala 7", "Apoio", "Medicação"]
        },
        # Folgas Enfermeiros [cite: 15, 17, 19, 22, 24, 26, 28, 48, 52, 56]
        "folgas_enf": {
            "Graciele Katia da Silva Camargo": [4, 20, 30], "Heloisa Gonçalves Silva": [6, 18, 24], "Kelly Priscila Azevedo Rodrigues": [4, 16, 22],
            "Larissa Aguiar de Sousa": [6, 16, 26], "Jessica Cristina Moraes De Souza": [2, 12, 22], "Raquel Rodrigues de Souza": [8, 12, 28],
            "Natalia Caitano de Lima Costa": [10, 28, 30], "Thaís Rodrigues Alves": [2, 14, 24], "Debora Maria Alves Gregorio": [8, 14, 26],
            "Veronica Martz Venancio da Silva": [12, 20, 30]
        },
        "rest_enf": {
            "Veronica Martz Venancio da Silva": ["Acolhimento e Classificação de Risco", "Cardiotocografia", "Observação", "Pré-parto", "Patologia", "Apoio"]
        }
    }
    if os.path.exists(FILE_CONFIG):
        with open(FILE_CONFIG, "r", encoding="utf-8") as f:
            try:
                dados = json.load(f)
                for k, v in padrao.items():
                    if k not in dados: dados[k] = v
                return dados
            except: return padrao
    return padrao

def salvar_config(dados):
    with open(FILE_CONFIG, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

config = carregar_config()

st.title("Gestão de Escala Hospitalar")

# --- INTERFACE DE DATA ---
col_cfg1, col_cfg2 = st.columns(2)
with col_cfg1:
    mes = st.number_input("Mês", min_value=1, max_value=12, value=config["mes"])
    ano = st.number_input("Ano", min_value=2026, max_value=2040, value=config["ano"])
with col_cfg2:
    idx_tipo = ["Pares", "Ímpares", "Todos"].index(config["tipo_dias"]) if config["tipo_dias"] in ["Pares", "Ímpares", "Todos"] else 2
    tipo_dias = st.radio("Dias do Plantão", ["Pares", "Ímpares", "Todos"], index=idx_tipo, horizontal=True)

_, num_dias = calendar.monthrange(ano, mes)
dias_mes = list(range(1, num_dias + 1))
dias_plantao = [d for d in dias_mes if (tipo_dias == "Pares" and d % 2 == 0) or (tipo_dias == "Ímpares" and d % 2 != 0) or (tipo_dias == "Todos")]

tab_escala, tab_folgas, tab_config = st.tabs(["📅 Gerar Escala", "🏥 Folgas e Proibições", "⚙️ Configurações Mestres"])

with tab_config:
    st.subheader("Configurações Permanentes")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        new_tec = st.text_area("Técnicos:", value=config["tecnicos"], height=150)
        new_inc_tec = st.text_area("Incompatíveis (Setor):", value=config["incompativeis_tec"], height=100)
    with col_c2:
        new_enf = st.text_area("Enfermeiros:", value=config["enfermeiros"], height=150)
        new_inc_enf = st.text_area("Incompatíveis (Grupo CO):", value=config["incompativeis_enf"], height=100)
    if st.button("💾 Salvar Equipe"):
        config.update({"tecnicos": new_tec, "enfermeiros": new_enf, "incompativeis_tec": new_inc_tec, "incompativeis_enf": new_inc_enf})
        salvar_config(config); st.rerun()

tecnicos_nomes = [n.strip() for n in config["tecnicos"].split(",") if n.strip()]
enfermeiros_nomes = [n.strip() for n in config["enfermeiros"].split(",") if n.strip()]

# --- DEFINIÇÃO DE SETORES ---
setores_tec = {
    "Puerpério": {"vagas": 2, "sigla": "P", "max": 2, "co": True}, "Recém-nascido": {"vagas": 1, "sigla": "RN", "max": 2, "co": True},
    "Pré-parto": {"vagas": 1, "sigla": "PP", "max": 2, "co": True}, "Patologia": {"vagas": 1, "sigla": "PATO", "max": 2, "co": True},
    "Observação": {"vagas": 2, "sigla": "OBS", "max": 2, "co": False}, "Medicação": {"vagas": 2, "sigla": "MED", "max": 2, "co": False},
    "Sala 6": {"vagas": 1, "sigla": "S6", "max": 2, "co": True}, "Sala 7": {"vagas": 1, "sigla": "S7", "max": 2, "co": True}
}
setores_enf = {
    "Acolhimento e Classificação de Risco": {"vagas": 1, "sigla": "ACCR", "max": 2, "co": False}, "Cardiotocografia": {"vagas": 1, "sigla": "CTB", "max": 2, "co": False},
    "Observação": {"vagas": 1, "sigla": "OBS", "max": 2, "co": False}, "Pré-parto": {"vagas": 1, "sigla": "PP", "max": 2, "co": True},
    "Patologia": {"vagas": 1, "sigla": "PATO", "max": 2, "co": True}, "Recém-nascido": {"vagas": 1, "sigla": "RN", "max": 2, "co": True}
}

folgas_tec = {}; rest_tec = {}; folgas_enf = {}; rest_enf = {}
with tab_folgas:
    st.write("Verifique as folgas importadas do PDF abaixo.")
    sub_t, sub_e = st.tabs(["🩺 Técnicos", "👩‍⚕️ Enfermeiros"])
    with sub_t:
        for f in tecnicos_nomes:
            c1, c2 = st.columns(2)
            folgas_tec[f] = c1.multiselect(f"Folgas {f}", dias_plantao, default=[d for d in config["folgas_tec"].get(f, []) if d in dias_plantao], key=f"f_t_{f}")
            rest_tec[f] = c2.multiselect(f"Proibidos {f}", list(setores_tec.keys()) + ["Apoio"], default=[s for s in config["rest_tec"].get(f, []) if s in list(setores_tec.keys())+["Apoio"]], key=f"r_t_{f}")
    with sub_e:
        for f in enfermeiros_nomes:
            c1, c2 = st.columns(2)
            folgas_enf[f] = c1.multiselect(f"Folgas {f}", dias_plantao, default=[d for d in config["folgas_enf"].get(f, []) if d in dias_plantao], key=f"f_e_{f}")
            rest_enf[f] = c2.multiselect(f"Proibidos {f}", list(setores_enf.keys()) + ["Apoio"], default=[s for s in config["rest_enf"].get(f, []) if s in list(setores_enf.keys())+["Apoio"]], key=f"r_e_{f}")
    
    if st.button("💾 Salvar Estado Atual"):
        config.update({"mes": mes, "ano": ano, "tipo_dias": tipo_dias, "folgas_tec": folgas_tec, "rest_tec": rest_tec, "folgas_enf": folgas_enf, "rest_enf": rest_enf})
        salvar_config(config); st.success("Estado salvo na nuvem!")

def resolver_escala(nomes, setores_dict, folgas_dict, rest_dict, incompativeis, is_enf=False):
    if not nomes: return None, None
    prob = pulp.LpProblem("Escala", pulp.LpMinimize)
    setores_list = list(setores_dict.keys())
    x = pulp.LpVariable.dicts("x", [(f, d, s) for f in nomes for d in dias_plantao for s in setores_list], cat='Binary')
    
    passou = pulp.LpVariable.dicts("passou", [(f, s) for f in nomes for s in setores_list], cat='Binary')
    excedeu = pulp.LpVariable.dicts("excedeu", [(f, s) for f in nomes for s in setores_list], lowBound=0, cat='Integer')
    rep_seg = pulp.LpVariable.dicts("rep_seg", [(f, d, s) for f in nomes for d in dias_plantao for s in setores_list], lowBound=0, cat='Integer')

    setores_rotacao = [s for s in setores_list if not (is_enf and s == "Recém-nascido")]
    prob += -pulp.lpSum([passou[(f, s)] * 1000 for f in nomes for s in setores_rotacao]) + \
            pulp.lpSum([excedeu[(f, s)] * 500 for f in nomes for s in setores_list]) + \
            pulp.lpSum([rep_seg[(f, d, s)] * 3000 for f in nomes for d in dias_plantao for s in setores_list])

    for d in dias_plantao:
        for s in setores_list:
            prob += pulp.lpSum([x[(f, d, s)] for f in nomes]) == setores_dict[s]["vagas"]

    for f in nomes:
        for s in setores_list:
            prob += passou[(f, s)] <= pulp.lpSum([x[(f, d, s)] for d in dias_plantao])
            prob += pulp.lpSum([x[(f, d, s)] for d in dias_plantao]) - setores_dict[s]["max"] <= excedeu[(f, s)]
        for d in dias_plantao:
            if d in folgas_dict[f]: prob += pulp.lpSum([x[(f, d, s)] for s in setores_list]) == 0
            elif "Apoio" in rest_dict[f]: prob += pulp.lpSum([x[(f, d, s)] for s in setores_list]) == 1
            else: prob += pulp.lpSum([x[(f, d, s)] for s in setores_list]) <= 1
            for s_p in rest_dict[f]:
                if s_p in setores_list: prob += x[(f, d, s_p)] == 0

    setores_co = [s for s in setores_list if setores_dict[s]["co"]]
    # Incompatibilidade
    pares = [tuple(p.split("-")) for p in [i.strip() for i in config["incompativeis_tec" if not is_enf else "incompativeis_enf"].split(",") if i.strip()] if "-" in p]
    for f1, f2 in pares:
        if f1 in nomes and f2 in nomes:
            for d in dias_plantao:
                if is_enf: prob += pulp.lpSum([x[(f1, d, s)] for s in setores_co]) + pulp.lpSum([x[(f2, d, s)] for s in setores_co]) <= 1
                else: 
                    for s in setores_list: prob += x[(f1, d, s)] + x[(f2, d, s)] <= 1

    for f in nomes:
        for s in setores_list:
            for i in range(len(dias_plantao)-1): 
                prob += x[(f, dias_plantao[i], s)] + x[(f, dias_plantao[i+1], s)] - 1 <= rep_seg[(f, dias_plantao[i], s)]

    prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=45))
    return prob, x

with tab_escala:
    if st.button("🚀 Gerar Escalas", type="primary"):
        with st.spinner("Calculando..."):
            st_t, res_t = resolver_escala(tecnicos_nomes, setores_tec, folgas_tec, rest_tec, [], is_enf=False)
            st_e, res_e = resolver_escala(enfermeiros_nomes, setores_enf, folgas_enf, rest_enf, [], is_enf=True)
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
