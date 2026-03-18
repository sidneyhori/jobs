"""
Story templates for the journalist agent.

Each template defines:
- id, category, tags, chart_type
- analysis_fn(data, summary) → dict with headline_stat, headline_label, chart_data, details
- prompt_template: string with {findings} placeholder for the LLM
"""

import statistics


def _fmt_pct(v):
    """Format a float as Brazilian percentage string: 37,7%"""
    return f"{v:.1f}%".replace(".", ",")


def _fmt_num(v):
    """Format an integer with dot thousands separator (Brazilian style)."""
    return f"{v:,}".replace(",", ".")


def _safe_avg(values):
    """Return average of non-None numeric values, or 0."""
    clean = [v for v in values if v is not None]
    return statistics.mean(clean) if clean else 0


# ─── Template 1: Gender Risk Gap ────────────────────────────────────────────

def _gender_risk_gap(data, summary):
    dem = summary["demographics"]
    pct_f = dem["pct_high_risk_feminino"]
    pct_m = dem["pct_high_risk_masculino"]
    total_f = dem["total_feminino"]
    total_m = dem["total_masculino"]
    hr_f = dem["high_risk_feminino"]
    hr_m = dem["high_risk_masculino"]

    return {
        "headline_stat": _fmt_pct(pct_f),
        "headline_label": "das mulheres em ocupações de alto risco de exposição à IA",
        "chart_data": [
            {"label": "Mulheres", "value": pct_f, "formatted": _fmt_pct(pct_f)},
            {"label": "Homens", "value": pct_m, "formatted": _fmt_pct(pct_m)},
        ],
        "details": {
            "total_feminino": _fmt_num(total_f),
            "total_masculino": _fmt_num(total_m),
            "high_risk_feminino": _fmt_num(hr_f),
            "high_risk_masculino": _fmt_num(hr_m),
            "pct_feminino": _fmt_pct(pct_f),
            "pct_masculino": _fmt_pct(pct_m),
            "gap_pp": _fmt_pct(pct_f - pct_m),
        },
    }


# ─── Template 2: Race Risk Gap ──────────────────────────────────────────────

def _race_risk_gap(data, summary):
    dem = summary["demographics"]
    pct_b = dem["pct_high_risk_branca"]
    pct_n = dem["pct_high_risk_negra"]
    total_b = dem["total_branca"]
    total_n = dem["total_negra"]
    hr_b = dem["high_risk_branca"]
    hr_n = dem["high_risk_negra"]

    return {
        "headline_stat": _fmt_pct(pct_b),
        "headline_label": "dos trabalhadores brancos em alto risco vs " + _fmt_pct(pct_n) + " dos negros",
        "chart_data": [
            {"label": "Branca", "value": pct_b, "formatted": _fmt_pct(pct_b)},
            {"label": "Negra", "value": pct_n, "formatted": _fmt_pct(pct_n)},
        ],
        "details": {
            "total_branca": _fmt_num(total_b),
            "total_negra": _fmt_num(total_n),
            "high_risk_branca": _fmt_num(hr_b),
            "high_risk_negra": _fmt_num(hr_n),
            "pct_branca": _fmt_pct(pct_b),
            "pct_negra": _fmt_pct(pct_n),
            "gap_pp": _fmt_pct(pct_b - pct_n),
        },
    }


# ─── Template 3: State Exposure Ranking ─────────────────────────────────────

def _state_exposure_ranking(data, summary):
    por_uf = summary["por_uf"]
    states = []
    for code, info in por_uf.items():
        states.append({
            "uf": info["nome"],
            "avg_exposicao": info["avg_exposicao"],
            "total_workers": info["total_workers"],
        })
    states.sort(key=lambda s: s["avg_exposicao"], reverse=True)
    top10 = states[:10]

    return {
        "headline_stat": str(top10[0]["avg_exposicao"]).replace(".", ","),
        "headline_label": f"exposição média em {top10[0]['uf']} — líder nacional",
        "chart_data": [
            {
                "label": s["uf"],
                "value": s["avg_exposicao"],
                "formatted": str(s["avg_exposicao"]).replace(".", ","),
                "workers": _fmt_num(s["total_workers"]),
            }
            for s in top10
        ],
        "details": {
            "top_state": top10[0]["uf"],
            "top_score": str(top10[0]["avg_exposicao"]).replace(".", ","),
            "bottom_state": states[-1]["uf"],
            "bottom_score": str(states[-1]["avg_exposicao"]).replace(".", ","),
            "national_avg": str(round(_safe_avg([s["avg_exposicao"] for s in states]), 1)).replace(".", ","),
            "top10": [{"uf": s["uf"], "score": str(s["avg_exposicao"]).replace(".", ",")} for s in top10],
        },
    }


# ─── Template 4: Most Exposed Top 10 ────────────────────────────────────────

def _most_exposed_top10(data, summary):
    # Filter occupations with both exposicao and empregados
    valid = [
        occ for occ in data
        if occ.get("exposicao") is not None and occ.get("empregados") and occ["empregados"] > 0
    ]
    # Sort by exposicao desc, then by empregados desc as tiebreaker
    valid.sort(key=lambda o: (o["exposicao"], o["empregados"]), reverse=True)
    top10 = valid[:10]

    return {
        "headline_stat": str(top10[0]["exposicao"]).replace(".", ","),
        "headline_label": f"exposição máxima — {top10[0]['titulo']}",
        "chart_data": [
            {
                "label": occ["titulo"],
                "value": occ["exposicao"],
                "formatted": str(occ["exposicao"]).replace(".", ","),
                "workers": _fmt_num(occ["empregados"]),
                "salary": _fmt_num(round(occ["salario"])) if occ.get("salario") else "N/D",
            }
            for occ in top10
        ],
        "details": {
            "top10": [
                {
                    "titulo": occ["titulo"],
                    "exposicao": occ["exposicao"],
                    "empregados": _fmt_num(occ["empregados"]),
                    "salario": _fmt_num(round(occ["salario"])) if occ.get("salario") else "N/D",
                }
                for occ in top10
            ],
            "total_workers_top10": _fmt_num(sum(o["empregados"] for o in top10)),
        },
    }


# ─── Template 5: Grande Grupo Comparison ─────────────────────────────────────

def _grupo_comparison(data, summary):
    grupos = {}
    for occ in data:
        gg = occ.get("grande_grupo")
        if not gg:
            continue
        if gg not in grupos:
            grupos[gg] = {"exposicoes": [], "salarios": [], "workers": 0}
        if occ.get("exposicao") is not None:
            grupos[gg]["exposicoes"].append(occ["exposicao"])
        if occ.get("salario") is not None:
            grupos[gg]["salarios"].append(occ["salario"])
        if occ.get("empregados"):
            grupos[gg]["workers"] += occ["empregados"]

    results = []
    for gg, vals in grupos.items():
        avg_exp = _safe_avg(vals["exposicoes"])
        avg_sal = _safe_avg(vals["salarios"])
        results.append({
            "grupo": gg,
            "avg_exposicao": round(avg_exp, 1),
            "avg_salario": round(avg_sal),
            "total_workers": vals["workers"],
            "n_occupations": len(vals["exposicoes"]),
        })
    results.sort(key=lambda r: r["avg_exposicao"], reverse=True)

    # Shorten grupo names for chart labels
    short_names = {
        "MEMBROS SUPERIORES DO PODER PÚBLICO, DIRIGENTES DE ORGANIZAÇÕES DE INTERESSE PÚBLICO E DE EMPRESAS, GERENTES": "Dirigentes e Gerentes",
        "PROFISSIONAIS DAS CIÊNCIAS E DAS ARTES": "Profissionais das Ciências",
        "TÉCNICOS DE NIVEL MÉDIO": "Técnicos de Nível Médio",
        "TRABALHADORES DE SERVIÇOS ADMINISTRATIVOS": "Serviços Administrativos",
        "TRABALHADORES DOS SERVIÇOS, VENDEDORES DO COMÉRCIO EM LOJAS E MERCADOS": "Serviços e Comércio",
        "TRABALHADORES AGROPECUÁRIOS, FLORESTAIS E DA PESCA": "Agropecuária e Pesca",
        "TRABALHADORES DA PRODUÇÃO DE BENS E SERVIÇOS INDUSTRIAIS": "Produção Industrial",
        "TRABALHADORES EM SERVIÇOS DE REPARAÇÃO E MANUTENÇÃO": "Reparação e Manutenção",
        "MEMBROS DAS FORÇAS ARMADAS, POLICIAIS E BOMBEIROS MILITARES": "Forças Armadas e Polícia",
    }

    return {
        "headline_stat": str(results[0]["avg_exposicao"]).replace(".", ","),
        "headline_label": f"exposição média — {short_names.get(results[0]['grupo'], results[0]['grupo'])}",
        "chart_data": [
            {
                "label": short_names.get(r["grupo"], r["grupo"]),
                "value": r["avg_exposicao"],
                "formatted": str(r["avg_exposicao"]).replace(".", ","),
                "workers": _fmt_num(r["total_workers"]),
                "salary": "R$ " + _fmt_num(r["avg_salario"]),
            }
            for r in results
        ],
        "details": {
            "grupos": [
                {
                    "nome": short_names.get(r["grupo"], r["grupo"]),
                    "avg_exposicao": r["avg_exposicao"],
                    "avg_salario": _fmt_num(r["avg_salario"]),
                    "total_workers": _fmt_num(r["total_workers"]),
                    "n_occupations": r["n_occupations"],
                }
                for r in results
            ],
        },
    }


# ─── Template 6: Growth vs Decline ──────────────────────────────────────────

def _growth_vs_decline(data, summary):
    growing = []
    declining = []
    for occ in data:
        if occ.get("saldo") is None or occ.get("exposicao") is None:
            continue
        entry = {
            "titulo": occ["titulo"],
            "saldo": occ["saldo"],
            "exposicao": occ["exposicao"],
            "empregados": occ.get("empregados") or 0,
        }
        if occ["saldo"] > 0:
            growing.append(entry)
        elif occ["saldo"] < 0:
            declining.append(entry)

    growing.sort(key=lambda o: o["saldo"], reverse=True)
    declining.sort(key=lambda o: o["saldo"])

    top_growing = growing[:5]
    top_declining = declining[:5]

    avg_exp_growing = _safe_avg([o["exposicao"] for o in growing]) if growing else 0
    avg_exp_declining = _safe_avg([o["exposicao"] for o in declining]) if declining else 0

    total_saldo_pos = sum(o["saldo"] for o in growing)
    total_saldo_neg = sum(o["saldo"] for o in declining)

    return {
        "headline_stat": _fmt_num(len(growing)),
        "headline_label": f"ocupações em crescimento vs {len(declining)} em declínio",
        "chart_data": [
            {"label": "Em crescimento", "value": len(growing), "formatted": _fmt_num(len(growing)),
             "detail": f"saldo total: +{_fmt_num(total_saldo_pos)}"},
            {"label": "Em declínio", "value": len(declining), "formatted": _fmt_num(len(declining)),
             "detail": f"saldo total: {_fmt_num(total_saldo_neg)}"},
        ],
        "details": {
            "n_growing": len(growing),
            "n_declining": len(declining),
            "avg_exposicao_growing": str(round(avg_exp_growing, 1)).replace(".", ","),
            "avg_exposicao_declining": str(round(avg_exp_declining, 1)).replace(".", ","),
            "total_saldo_pos": "+" + _fmt_num(total_saldo_pos),
            "total_saldo_neg": _fmt_num(total_saldo_neg),
            "top_growing": [
                {"titulo": o["titulo"], "saldo": "+" + _fmt_num(o["saldo"]), "exposicao": o["exposicao"]}
                for o in top_growing
            ],
            "top_declining": [
                {"titulo": o["titulo"], "saldo": _fmt_num(o["saldo"]), "exposicao": o["exposicao"]}
                for o in top_declining
            ],
        },
    }


# ─── Template Registry ──────────────────────────────────────────────────────

TEMPLATES = [
    {
        "id": "gender-risk-gap",
        "category": "Demografia",
        "tags": ["gênero", "risco", "exposição"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _gender_risk_gap,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a diferença de gênero na exposição à IA no mercado de trabalho brasileiro.

DADOS (use APENAS estes números, não invente dados):
- {pct_feminino} das mulheres ({high_risk_feminino} de {total_feminino}) estão em ocupações de alto risco
- {pct_masculino} dos homens ({high_risk_masculino} de {total_masculino}) estão em ocupações de alto risco
- Diferença: {gap_pp} pontos percentuais

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "race-risk-gap",
        "category": "Demografia",
        "tags": ["raça", "risco", "exposição"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _race_risk_gap,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a diferença racial na exposição à IA no mercado de trabalho brasileiro.

DADOS (use APENAS estes números, não invente dados):
- {pct_branca} dos trabalhadores brancos ({high_risk_branca} de {total_branca}) estão em alto risco
- {pct_negra} dos trabalhadores negros ({high_risk_negra} de {total_negra}) estão em alto risco
- Diferença: {gap_pp} pontos percentuais
- Nota: "negra" = preta + parda (classificação IBGE)

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "state-exposure-ranking",
        "category": "Regional",
        "tags": ["estados", "UF", "exposição", "regional"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _state_exposure_ranking,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre quais estados brasileiros têm maior exposição média à IA.

DADOS (use APENAS estes números, não invente dados):
- Estado líder: {top_state} com exposição média de {top_score}
- Último: {bottom_state} com {bottom_score}
- Média nacional: {national_avg}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "most-exposed-top10",
        "category": "Ocupações",
        "tags": ["ocupações", "exposição", "ranking"],
        "chart_type": "ranking_table",
        "analysis_fn": _most_exposed_top10,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as 10 ocupações mais expostas à IA no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Top 10 ocupações: {top10}
- Total de trabalhadores nestas 10 ocupações: {total_workers_top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "grupo-comparison",
        "category": "Setores",
        "tags": ["grande grupo", "setores", "comparação"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _grupo_comparison,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) comparando os grandes grupos ocupacionais (CBO) em termos de exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Grupos ordenados por exposição: {grupos}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "growth-vs-decline",
        "category": "Mercado",
        "tags": ["saldo", "crescimento", "declínio", "CAGED"],
        "chart_type": "comparison_pair",
        "analysis_fn": _growth_vs_decline,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o saldo de contratações (CAGED) e como se relaciona com a exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- {n_growing} ocupações com saldo positivo (total: {total_saldo_pos})
- {n_declining} ocupações com saldo negativo (total: {total_saldo_neg})
- Exposição média das que crescem: {avg_exposicao_growing}
- Exposição média das que declinam: {avg_exposicao_declining}
- Top 5 crescendo: {top_growing}
- Top 5 declinando: {top_declining}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
]


def get_templates():
    """Return the list of story templates."""
    return TEMPLATES
