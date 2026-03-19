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


# ─── Template 7: Safest Large Occupations ───────────────────────────────────

def _safest_large_occupations(data, summary):
    valid = [
        o for o in data
        if o.get("exposicao") is not None and o.get("empregados") and o["empregados"] >= 5000
    ]
    valid.sort(key=lambda o: (o["exposicao"], -o["empregados"]))
    top10 = valid[:10]
    total = sum(o["empregados"] for o in top10)

    return {
        "headline_stat": str(top10[0]["exposicao"]).replace(".", ","),
        "headline_label": f"exposição mínima — {top10[0]['titulo']}",
        "chart_data": [
            {
                "label": o["titulo"],
                "value": o["exposicao"],
                "formatted": str(o["exposicao"]).replace(".", ","),
                "workers": _fmt_num(o["empregados"]),
            }
            for o in top10
        ],
        "details": {
            "top10": [
                {"titulo": o["titulo"], "exposicao": o["exposicao"], "empregados": _fmt_num(o["empregados"]),
                 "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                for o in top10
            ],
            "total_workers": _fmt_num(total),
        },
    }


# ─── Template 8: Highest Opportunity ────────────────────────────────────────

def _highest_opportunity(data, summary):
    valid = [
        o for o in data
        if o.get("oportunidade") is not None and o.get("empregados") and o["empregados"] > 0
    ]
    valid.sort(key=lambda o: (o["oportunidade"], o["empregados"]), reverse=True)
    top10 = valid[:10]

    return {
        "headline_stat": str(top10[0]["oportunidade"]).replace(".", ","),
        "headline_label": f"oportunidade máxima — {top10[0]['titulo']}",
        "chart_data": [
            {
                "label": o["titulo"],
                "value": o["oportunidade"],
                "formatted": str(o["oportunidade"]).replace(".", ","),
                "workers": _fmt_num(o["empregados"]),
                "salary": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D",
            }
            for o in top10
        ],
        "details": {
            "top10": [
                {"titulo": o["titulo"], "oportunidade": o["oportunidade"],
                 "exposicao": o["exposicao"], "empregados": _fmt_num(o["empregados"]),
                 "salario": "R$ " + _fmt_num(round(o["salario"])) if o.get("salario") else "N/D"}
                for o in top10
            ],
            "total_workers": _fmt_num(sum(o["empregados"] for o in top10)),
        },
    }


# ─── Template 9: Salary vs Exposure ─────────────────────────────────────────

def _salary_vs_exposure(data, summary):
    high_exp = [o for o in data if o.get("exposicao") and o["exposicao"] >= 7 and o.get("salario")]
    low_exp = [o for o in data if o.get("exposicao") is not None and o["exposicao"] <= 3 and o.get("salario")]

    avg_sal_high = round(_safe_avg([o["salario"] for o in high_exp]))
    avg_sal_low = round(_safe_avg([o["salario"] for o in low_exp]))

    return {
        "headline_stat": "R$ " + _fmt_num(avg_sal_high),
        "headline_label": f"salário médio nas ocupações de alta exposição vs R$ {_fmt_num(avg_sal_low)} nas de baixa",
        "chart_data": [
            {"label": "Alta exposição (≥7)", "value": avg_sal_high,
             "formatted": "R$ " + _fmt_num(avg_sal_high),
             "detail": f"{len(high_exp)} ocupações"},
            {"label": "Baixa exposição (≤3)", "value": avg_sal_low,
             "formatted": "R$ " + _fmt_num(avg_sal_low),
             "detail": f"{len(low_exp)} ocupações"},
        ],
        "details": {
            "avg_salary_high": "R$ " + _fmt_num(avg_sal_high),
            "avg_salary_low": "R$ " + _fmt_num(avg_sal_low),
            "n_high": len(high_exp),
            "n_low": len(low_exp),
            "ratio": str(round(avg_sal_high / avg_sal_low, 1)).replace(".", ",") if avg_sal_low else "N/D",
        },
    }


# ─── Template 10: Augmented vs Automated ────────────────────────────────────

def _augmented_vs_automated(data, summary):
    augmented = []  # high exposure + high advantage (AI helps workers)
    automated = []  # high exposure + low advantage (AI replaces workers)
    for o in data:
        if o.get("exposicao") is None or o["exposicao"] < 7:
            continue
        if o.get("vantagem") is None:
            continue
        entry = {
            "titulo": o["titulo"],
            "exposicao": o["exposicao"],
            "vantagem": o["vantagem"],
            "empregados": o.get("empregados") or 0,
            "salario": o.get("salario"),
        }
        if o["vantagem"] >= 7:
            augmented.append(entry)
        elif o["vantagem"] <= 4:
            automated.append(entry)

    augmented.sort(key=lambda o: o["empregados"], reverse=True)
    automated.sort(key=lambda o: o["empregados"], reverse=True)

    total_aug = sum(o["empregados"] for o in augmented)
    total_auto = sum(o["empregados"] for o in automated)

    return {
        "headline_stat": _fmt_num(len(augmented)),
        "headline_label": f"ocupações potencializadas pela IA vs {len(automated)} ameaçadas",
        "chart_data": [
            {"label": "Potencializadas", "value": len(augmented), "formatted": _fmt_num(len(augmented)),
             "detail": _fmt_num(total_aug) + " trabalhadores"},
            {"label": "Ameaçadas", "value": len(automated), "formatted": _fmt_num(len(automated)),
             "detail": _fmt_num(total_auto) + " trabalhadores"},
        ],
        "details": {
            "n_augmented": len(augmented),
            "n_automated": len(automated),
            "total_augmented": _fmt_num(total_aug),
            "total_automated": _fmt_num(total_auto),
            "top_augmented": [
                {"titulo": o["titulo"], "vantagem": o["vantagem"], "empregados": _fmt_num(o["empregados"])}
                for o in augmented[:5]
            ],
            "top_automated": [
                {"titulo": o["titulo"], "vantagem": o["vantagem"], "empregados": _fmt_num(o["empregados"])}
                for o in automated[:5]
            ],
        },
    }


# ─── Template 11: Female-Dominated High-Risk ────────────────────────────────

def _female_dominated_high_risk(data, summary):
    results = []
    for o in data:
        dem = o.get("demographics")
        if not dem or o.get("exposicao") is None or o["exposicao"] < 7:
            continue
        tf = dem.get("total_feminino", 0)
        tm = dem.get("total_masculino", 0)
        total = tf + tm
        if total < 100:
            continue
        pct_f = round(tf / total * 100, 1)
        if pct_f > 55:
            results.append({
                "titulo": o["titulo"],
                "pct_feminino": pct_f,
                "exposicao": o["exposicao"],
                "total_workers": total,
                "salario": o.get("salario"),
            })
    results.sort(key=lambda r: r["total_workers"], reverse=True)
    top10 = results[:10]
    total_workers = sum(r["total_workers"] for r in results)
    total_fem = sum(round(r["total_workers"] * r["pct_feminino"] / 100) for r in results)

    return {
        "headline_stat": _fmt_num(total_fem),
        "headline_label": "mulheres em ocupações feminizadas de alto risco de IA",
        "chart_data": [
            {
                "label": r["titulo"],
                "value": r["pct_feminino"],
                "formatted": _fmt_pct(r["pct_feminino"]),
                "workers": _fmt_num(r["total_workers"]),
            }
            for r in top10
        ],
        "details": {
            "total_occupations": len(results),
            "total_workers": _fmt_num(total_workers),
            "total_women": _fmt_num(total_fem),
            "top10": [
                {"titulo": r["titulo"], "pct_feminino": _fmt_pct(r["pct_feminino"]),
                 "exposicao": r["exposicao"], "workers": _fmt_num(r["total_workers"])}
                for r in top10
            ],
        },
    }


# ─── Template 12: Hiring Into Risk ──────────────────────────────────────────

def _hiring_into_risk(data, summary):
    risky = [
        o for o in data
        if o.get("saldo") and o["saldo"] > 0
        and o.get("exposicao") and o["exposicao"] >= 7
        and o.get("empregados")
    ]
    risky.sort(key=lambda o: o["saldo"], reverse=True)
    top10 = risky[:10]
    total_saldo = sum(o["saldo"] for o in risky)

    return {
        "headline_stat": _fmt_num(total_saldo),
        "headline_label": "contratações líquidas em ocupações de alto risco de IA",
        "chart_data": [
            {
                "label": o["titulo"],
                "value": o["saldo"],
                "formatted": "+" + _fmt_num(o["saldo"]),
                "workers": _fmt_num(o["empregados"]),
            }
            for o in top10
        ],
        "details": {
            "total_occupations": len(risky),
            "total_saldo": "+" + _fmt_num(total_saldo),
            "top10": [
                {"titulo": o["titulo"], "saldo": "+" + _fmt_num(o["saldo"]),
                 "exposicao": o["exposicao"], "empregados": _fmt_num(o["empregados"])}
                for o in top10
            ],
        },
    }


# ─── Template 13: State Salary vs Exposure ──────────────────────────────────

def _state_salary_exposure(data, summary):
    por_uf = summary["por_uf"]
    states = []
    for code, info in por_uf.items():
        states.append({
            "uf": info["nome"],
            "avg_exposicao": info["avg_exposicao"],
            "avg_salary": info["avg_salary"],
            "total_workers": info["total_workers"],
        })

    # "Worst positioned": high exposure + low salary
    states.sort(key=lambda s: s["avg_exposicao"] / max(s["avg_salary"], 1), reverse=True)
    worst = states[:10]

    return {
        "headline_stat": worst[0]["uf"],
        "headline_label": "estado mais vulnerável: alta exposição, baixo salário",
        "chart_data": [
            {
                "label": s["uf"],
                "value": s["avg_exposicao"],
                "formatted": str(s["avg_exposicao"]).replace(".", ","),
                "workers": "R$ " + _fmt_num(s["avg_salary"]),
            }
            for s in worst
        ],
        "details": {
            "worst10": [
                {"uf": s["uf"], "exposicao": str(s["avg_exposicao"]).replace(".", ","),
                 "salario": "R$ " + _fmt_num(s["avg_salary"]),
                 "workers": _fmt_num(s["total_workers"])}
                for s in worst
            ],
        },
    }


# ─── Template 14: Education and Exposure ─────────────────────────────────────

def _education_exposure(data, summary):
    edu_map = {
        "Analfabeto": 0, "Até 5ª Incompleto": 1, "6ª a 9ª Fundamental": 2,
        "Médio Completo": 3, "Superior Completo": 4, "Mestrado": 5, "Doutorado": 6,
    }
    buckets = {}
    for o in data:
        esc = o.get("escolaridade")
        if not esc or esc not in edu_map or o.get("exposicao") is None:
            continue
        if esc not in buckets:
            buckets[esc] = {"exposicoes": [], "salarios": [], "count": 0}
        buckets[esc]["exposicoes"].append(o["exposicao"])
        if o.get("salario"):
            buckets[esc]["salarios"].append(o["salario"])
        buckets[esc]["count"] += 1

    results = []
    for esc, vals in buckets.items():
        avg_exp = round(_safe_avg(vals["exposicoes"]), 1)
        avg_sal = round(_safe_avg(vals["salarios"]))
        results.append({"escolaridade": esc, "avg_exposicao": avg_exp,
                        "avg_salario": avg_sal, "n_occupations": vals["count"],
                        "order": edu_map[esc]})
    results.sort(key=lambda r: r["order"])

    highest = max(results, key=lambda r: r["avg_exposicao"])
    lowest = min(results, key=lambda r: r["avg_exposicao"])

    return {
        "headline_stat": str(highest["avg_exposicao"]).replace(".", ","),
        "headline_label": f"exposição média — {highest['escolaridade']} (maior nível)",
        "chart_data": [
            {
                "label": r["escolaridade"],
                "value": r["avg_exposicao"],
                "formatted": str(r["avg_exposicao"]).replace(".", ","),
                "workers": f"{r['n_occupations']} ocupações",
            }
            for r in results
        ],
        "details": {
            "levels": [
                {"escolaridade": r["escolaridade"], "avg_exposicao": r["avg_exposicao"],
                 "avg_salario": "R$ " + _fmt_num(r["avg_salario"]),
                 "n_occupations": r["n_occupations"]}
                for r in results
            ],
            "highest": highest["escolaridade"],
            "highest_score": str(highest["avg_exposicao"]).replace(".", ","),
            "lowest": lowest["escolaridade"],
            "lowest_score": str(lowest["avg_exposicao"]).replace(".", ","),
        },
    }


# ─── Template 15: Entry Salary Gap ──────────────────────────────────────────

def _entry_salary_gap(data, summary):
    high = [o for o in data if o.get("exposicao") and o["exposicao"] >= 7
            and o.get("salario_admissao") and o.get("salario")]
    low = [o for o in data if o.get("exposicao") is not None and o["exposicao"] <= 3
           and o.get("salario_admissao") and o.get("salario")]

    avg_entry_high = round(_safe_avg([o["salario_admissao"] for o in high]))
    avg_full_high = round(_safe_avg([o["salario"] for o in high]))
    avg_entry_low = round(_safe_avg([o["salario_admissao"] for o in low]))
    avg_full_low = round(_safe_avg([o["salario"] for o in low]))

    gap_high = round((avg_full_high - avg_entry_high) / avg_entry_high * 100, 1) if avg_entry_high else 0
    gap_low = round((avg_full_low - avg_entry_low) / avg_entry_low * 100, 1) if avg_entry_low else 0

    return {
        "headline_stat": "R$ " + _fmt_num(avg_entry_high),
        "headline_label": f"salário de entrada em ocupações de alta exposição à IA",
        "chart_data": [
            {"label": "Entrada (alta exp.)", "value": avg_entry_high,
             "formatted": "R$ " + _fmt_num(avg_entry_high)},
            {"label": "Mediano (alta exp.)", "value": avg_full_high,
             "formatted": "R$ " + _fmt_num(avg_full_high)},
            {"label": "Entrada (baixa exp.)", "value": avg_entry_low,
             "formatted": "R$ " + _fmt_num(avg_entry_low)},
            {"label": "Mediano (baixa exp.)", "value": avg_full_low,
             "formatted": "R$ " + _fmt_num(avg_full_low)},
        ],
        "details": {
            "entry_high": "R$ " + _fmt_num(avg_entry_high),
            "full_high": "R$ " + _fmt_num(avg_full_high),
            "gap_high_pct": _fmt_pct(gap_high),
            "entry_low": "R$ " + _fmt_num(avg_entry_low),
            "full_low": "R$ " + _fmt_num(avg_full_low),
            "gap_low_pct": _fmt_pct(gap_low),
            "n_high": len(high),
            "n_low": len(low),
        },
    }


# ─── Template 16: AI Winners (High Opportunity + High Salary) ───────────────

def _ai_winners(data, summary):
    valid = [
        o for o in data
        if o.get("oportunidade") and o["oportunidade"] >= 7
        and o.get("salario") and o["salario"] >= 5000
        and o.get("empregados") and o["empregados"] > 0
    ]
    valid.sort(key=lambda o: o["oportunidade"] * o["salario"], reverse=True)
    top10 = valid[:10]

    return {
        "headline_stat": _fmt_num(len(valid)),
        "headline_label": "ocupações com alta oportunidade e salário acima de R$ 5.000",
        "chart_data": [
            {
                "label": o["titulo"],
                "value": o["oportunidade"],
                "formatted": str(o["oportunidade"]).replace(".", ","),
                "workers": "R$ " + _fmt_num(round(o["salario"])),
            }
            for o in top10
        ],
        "details": {
            "total_occupations": len(valid),
            "total_workers": _fmt_num(sum(o["empregados"] for o in valid)),
            "top10": [
                {"titulo": o["titulo"], "oportunidade": o["oportunidade"],
                 "salario": "R$ " + _fmt_num(round(o["salario"])),
                 "empregados": _fmt_num(o["empregados"])}
                for o in top10
            ],
        },
    }


# ─── Template 17: North-South Divide ────────────────────────────────────────

def _north_south_divide(data, summary):
    por_uf = summary["por_uf"]
    north_ne = {"RO", "AC", "AM", "RR", "PA", "AP", "TO", "MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"}
    south_se = {"MG", "ES", "RJ", "SP", "PR", "SC", "RS"}
    center = {"MS", "MT", "GO", "DF"}

    regions = {"Norte/Nordeste": [], "Sul/Sudeste": [], "Centro-Oeste": []}
    for code, info in por_uf.items():
        uf = info["nome"]
        if uf in north_ne:
            regions["Norte/Nordeste"].append(info)
        elif uf in south_se:
            regions["Sul/Sudeste"].append(info)
        elif uf in center:
            regions["Centro-Oeste"].append(info)

    results = []
    for region, states in regions.items():
        total_w = sum(s["total_workers"] for s in states)
        avg_exp = round(sum(s["avg_exposicao"] * s["total_workers"] for s in states) / total_w, 1) if total_w else 0
        avg_sal = round(sum(s["avg_salary"] * s["total_workers"] for s in states) / total_w) if total_w else 0
        results.append({"region": region, "avg_exposicao": avg_exp,
                        "avg_salary": avg_sal, "total_workers": total_w,
                        "n_states": len(states)})

    return {
        "headline_stat": str(results[0]["avg_exposicao"]).replace(".", ",") + " vs " + str(results[1]["avg_exposicao"]).replace(".", ","),
        "headline_label": "exposição média: Norte/Nordeste vs Sul/Sudeste",
        "chart_data": [
            {
                "label": r["region"],
                "value": r["avg_exposicao"],
                "formatted": str(r["avg_exposicao"]).replace(".", ","),
                "workers": "R$ " + _fmt_num(r["avg_salary"]),
            }
            for r in results
        ],
        "details": {
            "regions": [
                {"region": r["region"], "avg_exposicao": str(r["avg_exposicao"]).replace(".", ","),
                 "avg_salary": "R$ " + _fmt_num(r["avg_salary"]),
                 "total_workers": _fmt_num(r["total_workers"]),
                 "n_states": r["n_states"]}
                for r in results
            ],
        },
    }


# ─── Template 18: Telemarketing Deep Dive ───────────────────────────────────

def _telemarketing_spotlight(data, summary):
    tele = None
    for o in data:
        if "telemarketing" in o.get("titulo", "").lower():
            tele = o
            break
    if not tele:
        tele = max((o for o in data if o.get("exposicao") and o.get("empregados")),
                   key=lambda o: o["exposicao"] * (o["empregados"] or 0))

    dem = tele.get("demographics", {})
    tf = dem.get("total_feminino", 0)
    tm = dem.get("total_masculino", 0)
    total_dem = tf + tm
    pct_f = round(tf / total_dem * 100, 1) if total_dem else 0

    # Top 5 states
    por_uf = tele.get("por_uf", {})
    states = [{"uf": k, "ativos": v["ativos"], "salario": v.get("salario_mediano", 0)}
              for k, v in (por_uf or {}).items() if v.get("ativos")]
    states.sort(key=lambda s: s["ativos"], reverse=True)

    uf_names = summary.get("uf_codes", {})

    return {
        "headline_stat": _fmt_num(tele.get("empregados", 0)),
        "headline_label": f"trabalhadores em {tele['titulo'].lower()} — exposição {tele['exposicao']}/10",
        "chart_data": [
            {
                "label": uf_names.get(s["uf"], s["uf"]),
                "value": s["ativos"],
                "formatted": _fmt_num(s["ativos"]),
            }
            for s in states[:8]
        ],
        "details": {
            "titulo": tele["titulo"],
            "empregados": _fmt_num(tele.get("empregados", 0)),
            "exposicao": tele["exposicao"],
            "salario": "R$ " + _fmt_num(round(tele["salario"])) if tele.get("salario") else "N/D",
            "saldo": _fmt_num(tele.get("saldo", 0)),
            "pct_feminino": _fmt_pct(pct_f),
            "top_states": [{"uf": uf_names.get(s["uf"], s["uf"]), "ativos": _fmt_num(s["ativos"])} for s in states[:5]],
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
    # ── New templates 7-18 ──────────────────────────────────────────────────
    {
        "id": "safest-large-occupations",
        "category": "Ocupações",
        "tags": ["ocupações", "baixo risco", "segurança"],
        "chart_type": "ranking_table",
        "analysis_fn": _safest_large_occupations,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações grandes (>5.000 trabalhadores) mais protegidas da IA no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Top 10 ocupações mais seguras: {top10}
- Total de trabalhadores nestas ocupações: {total_workers}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "highest-opportunity",
        "category": "Ocupações",
        "tags": ["oportunidade", "vantagem", "crescimento"],
        "chart_type": "ranking_table",
        "analysis_fn": _highest_opportunity,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as 10 ocupações com maior oportunidade de IA no Brasil — onde a IA mais beneficia os trabalhadores.

DADOS (use APENAS estes números, não invente dados):
- Top 10 por oportunidade: {top10}
- Total de trabalhadores: {total_workers}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "salary-vs-exposure",
        "category": "Mercado",
        "tags": ["salário", "exposição", "desigualdade"],
        "chart_type": "comparison_pair",
        "analysis_fn": _salary_vs_exposure,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a relação entre salário e exposição à IA: ocupações mais expostas pagam mais ou menos?

DADOS (use APENAS estes números, não invente dados):
- Salário médio em ocupações de alta exposição (≥7): {avg_salary_high} ({n_high} ocupações)
- Salário médio em ocupações de baixa exposição (≤3): {avg_salary_low} ({n_low} ocupações)
- Razão: {ratio}x

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "augmented-vs-automated",
        "category": "Setores",
        "tags": ["automação", "potencialização", "vantagem"],
        "chart_type": "comparison_pair",
        "analysis_fn": _augmented_vs_automated,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a diferença entre ocupações potencializadas pela IA (alta exposição + alta vantagem) e ameaçadas (alta exposição + baixa vantagem).

DADOS (use APENAS estes números, não invente dados):
- {n_augmented} ocupações potencializadas ({total_augmented} trabalhadores)
- {n_automated} ocupações ameaçadas ({total_automated} trabalhadores)
- Top 5 potencializadas: {top_augmented}
- Top 5 ameaçadas: {top_automated}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "female-dominated-high-risk",
        "category": "Demografia",
        "tags": ["gênero", "feminização", "risco"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _female_dominated_high_risk,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre ocupações majoritariamente femininas que enfrentam alto risco de IA.

DADOS (use APENAS estes números, não invente dados):
- {total_occupations} ocupações feminizadas (>55%% mulheres) com exposição ≥7
- {total_women} mulheres afetadas de {total_workers} trabalhadores total
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "hiring-into-risk",
        "category": "Mercado",
        "tags": ["contratação", "risco", "CAGED", "paradoxo"],
        "chart_type": "ranking_table",
        "analysis_fn": _hiring_into_risk,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre o paradoxo: o Brasil está contratando em massa para ocupações com alto risco de disrupção por IA.

DADOS (use APENAS estes números, não invente dados):
- {total_occupations} ocupações com saldo positivo E exposição ≥7
- Saldo total nestas ocupações: {total_saldo}
- Top 10 contratando para o risco: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "state-vulnerability",
        "category": "Regional",
        "tags": ["estados", "vulnerabilidade", "salário", "exposição"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _state_salary_exposure,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre quais estados são mais vulneráveis à IA: alta exposição combinada com salários baixos.

DADOS (use APENAS estes números, não invente dados):
- Top 10 estados mais vulneráveis (alta exposição / baixo salário): {worst10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "education-exposure",
        "category": "Educação",
        "tags": ["escolaridade", "exposição", "formação"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _education_exposure,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre como o nível de escolaridade se relaciona com a exposição à IA no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Níveis de escolaridade e exposição média: {levels}
- Maior exposição: {highest} com score {highest_score}
- Menor exposição: {lowest} com score {lowest_score}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "entry-salary-gap",
        "category": "Mercado",
        "tags": ["salário", "entrada", "admissão", "jovens"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _entry_salary_gap,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre os salários de entrada em ocupações de alta vs baixa exposição à IA.

DADOS (use APENAS estes números, não invente dados):
- Salário de entrada (alta exposição): {entry_high} → mediano: {full_high} (gap de {gap_high_pct})
- Salário de entrada (baixa exposição): {entry_low} → mediano: {full_low} (gap de {gap_low_pct})
- {n_high} ocupações de alta exposição, {n_low} de baixa

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "ai-winners",
        "category": "Ocupações",
        "tags": ["oportunidade", "salário", "vencedores"],
        "chart_type": "ranking_table",
        "analysis_fn": _ai_winners,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre as ocupações "vencedoras" da IA: alta oportunidade E salário acima de R$ 5.000.

DADOS (use APENAS estes números, não invente dados):
- {total_occupations} ocupações com oportunidade ≥7 e salário ≥R$ 5.000
- Total de trabalhadores: {total_workers}
- Top 10: {top10}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "north-south-divide",
        "category": "Regional",
        "tags": ["regional", "desigualdade", "Norte", "Sul"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _north_south_divide,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) sobre a divisão regional na exposição à IA: Norte/Nordeste vs Sul/Sudeste vs Centro-Oeste.

DADOS (use APENAS estes números, não invente dados):
- Regiões comparadas: {regions}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
    {
        "id": "telemarketing-spotlight",
        "category": "Ocupações",
        "tags": ["telemarketing", "caso", "feminização", "automação"],
        "chart_type": "horizontal_bar",
        "analysis_fn": _telemarketing_spotlight,
        "prompt_template": """Você é um jornalista de dados escrevendo para uma publicação como The Economist ou Folha de S.Paulo.

Escreva um artigo curto (150-200 palavras) como um estudo de caso profundo sobre operadores de telemarketing — uma das ocupações mais expostas à IA no Brasil.

DADOS (use APENAS estes números, não invente dados):
- Ocupação: {titulo}
- Trabalhadores: {empregados}
- Exposição: {exposicao}/10
- Salário mediano: {salario}
- Saldo CAGED: {saldo}
- Porcentagem feminina: {pct_feminino}
- Top estados: {top_states}

Retorne JSON com exatamente estes campos:
{{"title": "título impactante (máx 10 palavras)", "subtitle": "subtítulo explicativo (máx 15 palavras)", "body": "texto do artigo em HTML com <p> tags"}}""",
    },
]


def get_templates():
    """Return the list of story templates."""
    return TEMPLATES
