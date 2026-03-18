"""
Build a CSV summary of all Brazilian occupations by merging CBO + CAGED + RAIS data.

Merges:
- brazil/data/cbo_occupations.json (structure, hierarchy, activities)
- brazil/data/caged_stats.json (salary flows, admissions/terminations)
- brazil/data/rais_stats.json (employment stock, market salary, education)

Output: brazil/occupations_br.csv

Usage:
    uv run python brazil/make_csv_br.py
"""

import csv
import json
import os


DATA_DIR = "brazil/data"


def main():
    # Load CBO families
    with open(os.path.join(DATA_DIR, "cbo_occupations.json"), encoding="utf-8") as f:
        familias = json.load(f)

    # Load CAGED stats, index by family code
    caged_path = os.path.join(DATA_DIR, "caged_stats.json")
    caged_by_code = {}
    if os.path.exists(caged_path):
        with open(caged_path, encoding="utf-8") as f:
            caged_stats = json.load(f)
        for s in caged_stats:
            caged_by_code[s["codigo_familia"]] = s
    else:
        print(f"WARNING: {caged_path} not found. CSV will have empty CAGED columns.")

    # Load RAIS stats, index by family code
    rais_path = os.path.join(DATA_DIR, "rais_stats.json")
    rais_by_code = {}
    if os.path.exists(rais_path):
        with open(rais_path, encoding="utf-8") as f:
            rais_stats = json.load(f)
        for s in rais_stats:
            rais_by_code[s["codigo_familia"]] = s
    else:
        print(f"WARNING: {rais_path} not found. CSV will have empty RAIS columns.")

    # Build rows
    fieldnames = [
        "codigo_cbo", "titulo", "slug",
        "grande_grupo_codigo", "grande_grupo",
        "subgrupo_principal_codigo", "subgrupo_principal",
        "subgrupo_codigo", "subgrupo",
        # RAIS (stock)
        "empregados",  # vinculos_ativos from RAIS
        "salario_mediano_rais",  # true market median
        "escolaridade_tipica",
        # CAGED (flow)
        "salario_mediano_caged",  # admission salary
        "admissoes", "desligamentos", "saldo_periodo",
        # CBO metadata
        "n_ocupacoes",
        "n_areas_atividade",
        "n_atividades",
    ]

    rows = []
    matched_caged = 0
    matched_rais = 0
    for fam in familias:
        codigo = fam["codigo"]
        caged = caged_by_code.get(codigo, {})
        rais = rais_by_code.get(codigo, {})

        # Count activities (deduplicated)
        atividades = fam.get("atividades", [])
        areas = fam.get("areas_de_atividade", [])
        unique_atividades = set()
        for at in atividades:
            unique_atividades.add(at.get("atividade", ""))

        row = {
            "codigo_cbo": codigo,
            "titulo": fam["titulo"],
            "slug": fam["slug"],
            "grande_grupo_codigo": fam["grande_grupo_codigo"],
            "grande_grupo": fam["grande_grupo"],
            "subgrupo_principal_codigo": fam["subgrupo_principal_codigo"],
            "subgrupo_principal": fam["subgrupo_principal"],
            "subgrupo_codigo": fam["subgrupo_codigo"],
            "subgrupo": fam["subgrupo"],
            # RAIS
            "empregados": rais.get("vinculos_ativos", ""),
            "salario_mediano_rais": rais.get("salario_mediano_rais", ""),
            "escolaridade_tipica": rais.get("escolaridade_tipica", ""),
            # CAGED
            "salario_mediano_caged": caged.get("salario_mediano", ""),
            "admissoes": caged.get("admissoes", ""),
            "desligamentos": caged.get("desligamentos", ""),
            "saldo_periodo": caged.get("saldo_periodo", ""),
            # CBO
            "n_ocupacoes": 0,
            "n_areas_atividade": len(areas),
            "n_atividades": len(unique_atividades),
        }

        if caged:
            matched_caged += 1
        if rais:
            matched_rais += 1

        rows.append(row)

    # Count sub-occupations per family from the ocupacao CSV
    occ_path = os.path.join(DATA_DIR, "cbo2002-ocupacao.csv")
    if os.path.exists(occ_path):
        occ_count = {}
        with open(occ_path, encoding="latin-1") as f:
            for occ_row in csv.DictReader(f, delimiter=";"):
                fam_code = occ_row["CODIGO"].strip()[:4]
                occ_count[fam_code] = occ_count.get(fam_code, 0) + 1
        for row in rows:
            row["n_ocupacoes"] = occ_count.get(row["codigo_cbo"], 0)

    # Write CSV
    out_path = "brazil/occupations_br.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")
    print(f"  With CAGED data: {matched_caged}/{len(rows)}")
    print(f"  With RAIS data: {matched_rais}/{len(rows)}")

    # Spot checks
    print(f"\nSample rows:")
    checks = ["2124", "7152", "5211", "2251", "7823"]
    for code in checks:
        match = [r for r in rows if r["codigo_cbo"] == code]
        if match:
            r = match[0]
            emp = f"{int(r['empregados']):,}" if r['empregados'] else "N/A"
            sal_r = f"R${float(r['salario_mediano_rais']):,.0f}" if r['salario_mediano_rais'] else "N/A"
            sal_c = f"R${float(r['salario_mediano_caged']):,.0f}" if r['salario_mediano_caged'] else "N/A"
            print(f"  {r['codigo_cbo']} {r['titulo']}: emp={emp}, sal_rais={sal_r}, sal_caged={sal_c}, saldo={r['saldo_periodo']}, escol={r['escolaridade_tipica']}")


if __name__ == "__main__":
    main()
