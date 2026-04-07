#!/usr/bin/env python3
"""Generate insights.json for the US AI Jobs Impact site."""

import json
import os
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "site", "data.json")
SUMMARY_PATH = os.path.join(SCRIPT_DIR, "site", "summary.json")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "site", "insights.json")

TODAY = "2026-03-22"


def load_data():
    with open(DATA_PATH) as f:
        data = json.load(f)
    with open(SUMMARY_PATH) as f:
        summary = json.load(f)
    return data, summary


def fmt_num(n):
    """Format number with commas: 1234567 -> 1,234,567"""
    return f"{n:,.0f}"


def fmt_pct(n):
    """Format percentage with one decimal: 54.1 -> 54.1%"""
    return f"{n:.1f}%"


def fmt_money(n):
    """Format as dollar amount: 81680 -> $81,680"""
    return f"${n:,.0f}"


def fmt_millions(n):
    """Format large numbers as millions: 49009400 -> 49.0M"""
    m = n / 1_000_000
    if m >= 10:
        return f"{m:.0f}M"
    return f"{m:.1f}M"


def cat_label(slug):
    """Convert category slug to readable label."""
    labels = {
        "healthcare": "Healthcare",
        "office-and-administrative-support": "Office & Admin Support",
        "transportation-and-material-moving": "Transportation",
        "management": "Management",
        "food-preparation-and-serving": "Food Service",
        "sales": "Sales",
        "business-and-financial": "Business & Financial",
        "education-training-and-library": "Education",
        "construction-and-extraction": "Construction",
        "production": "Production",
        "installation-maintenance-and-repair": "Installation & Repair",
        "computer-and-information-technology": "Computer & IT",
        "building-and-grounds-cleaning": "Cleaning & Grounds",
        "personal-care-and-service": "Personal Care",
        "protective-service": "Protective Service",
        "community-and-social-service": "Community & Social",
        "architecture-and-engineering": "Architecture & Engineering",
        "legal": "Legal",
        "media-and-communication": "Media & Communication",
        "life-physical-and-social-science": "Life & Physical Science",
        "farming-fishing-and-forestry": "Farming & Forestry",
        "entertainment-and-sports": "Entertainment & Sports",
        "arts-and-design": "Arts & Design",
        "math": "Math & Statistics",
        "military": "Military",
    }
    return labels.get(slug, slug.replace("-", " ").title())


def generate_insights(data, summary):
    insights = []

    # Filter out occupations with missing data
    data = [o for o in data if o.get("jobs") is not None and o.get("pay") is not None]

    # ══════════════════════════════════════════════════════════════
    # DEMOGRAPHICS (5-6 insights)
    # ══════════════════════════════════════════════════════════════

    demo = summary["demographics"]

    # 1. Gender risk gap
    pct_hr_m = demo["pct_high_risk_male"]
    pct_hr_f = demo["pct_high_risk_female"]
    hr_m = demo["high_risk_male"]
    hr_f = demo["high_risk_female"]
    total_m = demo["total_male"]
    total_f = demo["total_female"]

    insights.append({
        "id": "gender-risk-parity",
        "category": "Demographics",
        "title": "Men and Women Face Nearly Identical AI Exposure Rates",
        "subtitle": f"About {fmt_pct(pct_hr_m)} of both male and female workers are in high-risk occupations.",
        "body_html": (
            f"<p>Across the 342 occupations tracked in this dataset, <strong>{fmt_pct(pct_hr_m)}</strong> of male workers "
            f"and <strong>{fmt_pct(pct_hr_f)}</strong> of female workers hold jobs with elevated AI exposure. "
            f"That translates to roughly <strong>{fmt_millions(hr_m)}</strong> men and <strong>{fmt_millions(hr_f)}</strong> women "
            f"in occupations where artificial intelligence could substantially reshape day-to-day tasks.</p>"
            f"<p>This near-parity challenges a common assumption that AI displacement will fall disproportionately on one gender. "
            f"The risk is remarkably evenly distributed, though the <em>types</em> of exposed jobs differ sharply: "
            f"women are concentrated in administrative and financial roles, while men dominate exposed positions in IT and engineering.</p>"
        ),
        "headline_stat": fmt_pct(pct_hr_m),
        "headline_label": "of both men and women in high-exposure occupations",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": "Male workers", "value": pct_hr_m, "formatted": fmt_pct(pct_hr_m)},
                {"label": "Female workers", "value": pct_hr_f, "formatted": fmt_pct(pct_hr_f)},
            ]
        },
        "generated_at": TODAY,
        "tags": ["gender", "exposure", "demographics"]
    })

    # 2. Racial composition of the workforce
    total_with_demo = demo["workers_with_demographics"]
    pct_white = demo["total_white"] / total_with_demo * 100
    pct_black = demo["total_black"] / total_with_demo * 100
    pct_asian = demo["total_asian"] / total_with_demo * 100
    pct_hispanic = demo["total_hispanic"] / total_with_demo * 100

    insights.append({
        "id": "racial-composition-workforce",
        "category": "Demographics",
        "title": "White Workers Hold 72% of Jobs Tracked for AI Exposure",
        "subtitle": "The racial composition of the AI-exposed workforce mirrors broader labor market demographics.",
        "body_html": (
            f"<p>Of the <strong>{fmt_millions(total_with_demo)}</strong> workers with demographic data across tracked occupations, "
            f"<strong>{fmt_pct(pct_white)}</strong> are white, <strong>{fmt_pct(pct_hispanic)}</strong> are Hispanic or Latino, "
            f"<strong>{fmt_pct(pct_black)}</strong> are Black, and <strong>{fmt_pct(pct_asian)}</strong> are Asian. "
            f"These proportions largely track national labor force averages, but the distribution within high-exposure "
            f"occupations is not uniform.</p>"
            f"<p>Asian workers are overrepresented in the highest-exposure category -- computer and information technology -- "
            f"where average exposure scores reach 8.5 out of 10. Meanwhile, Hispanic workers are more concentrated in "
            f"construction, food service, and farming, sectors where AI exposure remains low. The uneven distribution "
            f"means that while overall risk rates appear balanced, specific communities face very different futures.</p>"
        ),
        "headline_stat": fmt_pct(pct_white),
        "headline_label": "of tracked workforce is white",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": "White", "value": pct_white, "formatted": fmt_pct(pct_white)},
                {"label": "Hispanic/Latino", "value": pct_hispanic, "formatted": fmt_pct(pct_hispanic)},
                {"label": "Black", "value": pct_black, "formatted": fmt_pct(pct_black)},
                {"label": "Asian", "value": pct_asian, "formatted": fmt_pct(pct_asian)},
            ]
        },
        "generated_at": TODAY,
        "tags": ["race", "demographics", "equity"]
    })

    # 3. Women in high-exposure office jobs
    office_occs = [o for o in data if o["category"] == "office-and-administrative-support"]
    office_jobs = sum(o["jobs"] for o in office_occs)
    office_female = sum(o["demographics"].get("total_female", 0) for o in office_occs if o.get("demographics"))
    office_female_pct = office_female / sum(o["demographics"].get("total_female", 0) + o["demographics"].get("total_male", 0) for o in office_occs if o.get("demographics")) * 100 if office_occs else 0
    office_avg_exp = sum(o["exposure"] * o["jobs"] for o in office_occs) / office_jobs if office_jobs else 0

    insights.append({
        "id": "women-office-admin-risk",
        "category": "Demographics",
        "title": "Office Jobs: 16.5 Million Workers in AI's Direct Path",
        "subtitle": f"Administrative support occupations have an average exposure score of {office_avg_exp:.1f} out of 10.",
        "body_html": (
            f"<p>The office and administrative support sector employs <strong>{fmt_millions(office_jobs)}</strong> workers "
            f"and carries an average AI exposure score of <strong>{office_avg_exp:.1f}</strong>, among the highest of any "
            f"occupational category. These are the bookkeepers, data entry clerks, and administrative assistants whose "
            f"daily tasks overlap most directly with what large language models and automation tools already do well.</p>"
            f"<p>Women make up roughly <strong>{fmt_pct(office_female_pct)}</strong> of this workforce. "
            f"The category's average pay of <strong>{fmt_money(45433)}</strong> means these are predominantly middle-income jobs "
            f"-- exactly the kind of positions that AI tends to compress. For millions of workers, the question is not whether "
            f"their roles will change, but how quickly employers will restructure teams around AI-augmented workflows.</p>"
        ),
        "headline_stat": fmt_millions(office_jobs),
        "headline_label": "office & admin workers facing high AI exposure",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": "Office & Admin", "value": office_avg_exp, "formatted": f"{office_avg_exp:.1f}/10"},
                {"label": "Computer & IT", "value": 8.5, "formatted": "8.5/10"},
                {"label": "Legal", "value": 8.3, "formatted": "8.3/10"},
                {"label": "Business & Financial", "value": 7.6, "formatted": "7.6/10"},
            ]
        },
        "generated_at": TODAY,
        "tags": ["gender", "office", "exposure", "automation"]
    })

    # 4. 90 million workers with demographics data
    insights.append({
        "id": "demographic-data-coverage",
        "category": "Demographics",
        "title": "90 Million Workers: Inside the Demographic Data",
        "subtitle": f"BLS demographic breakdowns cover {fmt_num(total_with_demo)} workers across tracked occupations.",
        "body_html": (
            f"<p>The Bureau of Labor Statistics provides gender and racial breakdowns for <strong>{fmt_millions(total_with_demo)}</strong> "
            f"workers, covering the majority of the <strong>{fmt_millions(summary['total_workers'])}</strong> total jobs in tracked occupations. "
            f"These demographics reveal a workforce split almost exactly down the middle by gender: "
            f"<strong>{fmt_millions(total_m)}</strong> men and <strong>{fmt_millions(total_f)}</strong> women.</p>"
            f"<p>The near-equal split is noteworthy because it means AI's labor market effects will not be a gendered crisis "
            f"in aggregate, even if particular occupations skew heavily. The policy challenge lies in the details: "
            f"supporting the specific workers whose roles are being transformed, regardless of which demographic group they belong to.</p>"
        ),
        "headline_stat": fmt_millions(total_with_demo),
        "headline_label": "workers with demographic data in tracked occupations",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": "Male", "value": total_m / 1_000_000, "formatted": fmt_millions(total_m)},
                {"label": "Female", "value": total_f / 1_000_000, "formatted": fmt_millions(total_f)},
            ]
        },
        "generated_at": TODAY,
        "tags": ["demographics", "workforce", "data"]
    })

    # 5. Asian workers in tech
    it_occs = [o for o in data if o["category"] == "computer-and-information-technology"]
    it_asian = sum(o["demographics"].get("total_asian", 0) for o in it_occs if o.get("demographics"))
    it_total_demo = sum(o["demographics"].get("total_male", 0) + o["demographics"].get("total_female", 0) for o in it_occs if o.get("demographics"))
    it_asian_pct = it_asian / it_total_demo * 100 if it_total_demo else 0
    national_asian_pct = pct_asian

    insights.append({
        "id": "asian-workers-tech-exposure",
        "category": "Demographics",
        "title": f"Asian Workers Are {it_asian_pct / national_asian_pct:.1f}x Overrepresented in Highest-Exposure Sector",
        "subtitle": f"Asian workers make up {fmt_pct(it_asian_pct)} of IT workers vs. {fmt_pct(national_asian_pct)} of the overall workforce.",
        "body_html": (
            f"<p>Computer and information technology occupations have the highest average AI exposure score of any "
            f"sector at <strong>8.5 out of 10</strong>, and Asian workers make up <strong>{fmt_pct(it_asian_pct)}</strong> "
            f"of workers in these roles -- roughly <strong>{it_asian_pct / national_asian_pct:.1f} times</strong> their "
            f"share of the overall tracked workforce.</p>"
            f"<p>This concentration creates a paradox: the community most represented in AI-building roles is also the most "
            f"exposed to AI disruption. Software developers, data scientists, and systems analysts are seeing their own tools "
            f"automate significant portions of their work. The advantage score for IT occupations remains high, suggesting "
            f"these workers can leverage AI rather than be replaced by it, but the structural risk is real.</p>"
        ),
        "headline_stat": fmt_pct(it_asian_pct),
        "headline_label": "of IT workers are Asian",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": "IT sector", "value": it_asian_pct, "formatted": fmt_pct(it_asian_pct)},
                {"label": "All occupations", "value": national_asian_pct, "formatted": fmt_pct(national_asian_pct)},
            ]
        },
        "generated_at": TODAY,
        "tags": ["race", "technology", "exposure", "asian"]
    })

    # ══════════════════════════════════════════════════════════════
    # REGIONAL (5-6 insights)
    # ══════════════════════════════════════════════════════════════

    states = summary["by_state"]
    state_list = [(k, v) for k, v in states.items()]

    # 6. Highest exposure states
    states_by_exp = sorted(state_list, key=lambda x: x[1]["avg_exposure"], reverse=True)
    top5_exp = states_by_exp[:5]

    insights.append({
        "id": "highest-exposure-states",
        "category": "Regional",
        "title": f"D.C. Leads the Nation in AI Exposure at {states['DC']['avg_exposure']}/10",
        "subtitle": "Knowledge-economy hubs face the greatest concentration of AI-exposed occupations.",
        "body_html": (
            f"<p>The District of Columbia has the highest average AI exposure score of any state or territory at "
            f"<strong>{states['DC']['avg_exposure']}</strong> out of 10, driven by its concentration of lawyers, "
            f"management analysts, and public relations specialists. Utah (<strong>{states['UT']['avg_exposure']}</strong>), "
            f"with its booming tech corridor, ranks second.</p>"
            f"<p>The pattern is clear: places with dense white-collar, knowledge-economy workforces face higher aggregate "
            f"AI exposure. States dominated by agriculture, manufacturing, or extraction industries -- like Louisiana "
            f"(<strong>{states['LA']['avg_exposure']}</strong>) and Wyoming (<strong>{states['WY']['avg_exposure']}</strong>) "
            f"-- sit at the bottom. This geographic divide suggests that AI's labor market impact will be felt most acutely "
            f"in the nation's wealthiest metropolitan areas, not its industrial heartland.</p>"
        ),
        "headline_stat": f"{states['DC']['avg_exposure']}",
        "headline_label": "average exposure score for D.C. (highest in the nation)",
        "chart": {
            "type": "horizontal_bar",
            "data": [{"label": v["name"], "value": v["avg_exposure"], "formatted": f"{v['avg_exposure']}/10"} for _, v in top5_exp]
        },
        "generated_at": TODAY,
        "tags": ["states", "exposure", "regional"]
    })

    # 7. Highest paying states
    states_by_pay = sorted(state_list, key=lambda x: x[1]["avg_pay"], reverse=True)
    top5_pay = states_by_pay[:5]

    insights.append({
        "id": "highest-paying-states",
        "category": "Regional",
        "title": f"D.C. Workers Earn {fmt_money(states['DC']['avg_pay'])} on Average, Highest in the Nation",
        "subtitle": "High-pay states also tend to have higher AI exposure, creating a risk-reward dynamic.",
        "body_html": (
            f"<p>Workers in the District of Columbia earn an average of <strong>{fmt_money(states['DC']['avg_pay'])}</strong> "
            f"across tracked occupations, nearly double the national median. Massachusetts "
            f"(<strong>{fmt_money(states['MA']['avg_pay'])}</strong>) and Washington state "
            f"(<strong>{fmt_money(states['WA']['avg_pay'])}</strong>) round out the top three.</p>"
            f"<p>There is a strong correlation between average pay and average AI exposure at the state level. The highest-paying "
            f"states tend to have economies built on exactly the knowledge work that AI targets: legal services, finance, "
            f"software development, and consulting. Workers in these states earn more, but they also face a higher probability "
            f"of significant job restructuring. Mississippi, at <strong>{fmt_money(states['MS']['avg_pay'])}</strong>, pays the "
            f"least but also has lower exposure -- a trade-off that may look increasingly complicated.</p>"
        ),
        "headline_stat": fmt_money(states['DC']['avg_pay']),
        "headline_label": "average pay in D.C. (highest nationally)",
        "chart": {
            "type": "horizontal_bar",
            "data": [{"label": v["name"], "value": v["avg_pay"], "formatted": fmt_money(v["avg_pay"])} for _, v in top5_pay]
        },
        "generated_at": TODAY,
        "tags": ["states", "salary", "regional"]
    })

    # 8. Most workers by state
    states_by_workers = sorted(state_list, key=lambda x: x[1]["total_workers"], reverse=True)
    top5_workers = states_by_workers[:5]

    insights.append({
        "id": "largest-state-workforces",
        "category": "Regional",
        "title": f"California's {fmt_millions(states['CA']['total_workers'])} Workers Form the Largest Exposed Workforce",
        "subtitle": "The five largest states account for a disproportionate share of AI-exposed employment.",
        "body_html": (
            f"<p>California leads with <strong>{fmt_millions(states['CA']['total_workers'])}</strong> workers across tracked "
            f"occupations, followed by Texas (<strong>{fmt_millions(states['TX']['total_workers'])}</strong>) and "
            f"New York (<strong>{fmt_millions(states['NY']['total_workers'])}</strong>). Together, the top five states "
            f"account for roughly <strong>{sum(v['total_workers'] for _, v in top5_workers) / summary['total_workers'] * 100:.0f}%</strong> "
            f"of all tracked employment.</p>"
            f"<p>This concentration means that state-level policy responses to AI-driven labor disruption in just a handful "
            f"of states could affect tens of millions of workers. California's economy alone encompasses everything from "
            f"Silicon Valley software engineers (exposure: 8.5) to Central Valley farmworkers (exposure: 2.9), making "
            f"any single-state AI workforce policy inherently complex.</p>"
        ),
        "headline_stat": fmt_millions(states['CA']['total_workers']),
        "headline_label": "workers in California (largest state workforce)",
        "chart": {
            "type": "horizontal_bar",
            "data": [{"label": v["name"], "value": v["total_workers"] / 1_000_000, "formatted": fmt_millions(v["total_workers"])} for _, v in top5_workers]
        },
        "generated_at": TODAY,
        "tags": ["states", "workforce", "regional"]
    })

    # 9. Coastal vs inland exposure
    coastal = ["CA", "NY", "WA", "MA", "NJ", "CT", "OR", "MD", "VA", "FL"]
    inland = ["OH", "IN", "IA", "KS", "MO", "NE", "ND", "SD", "WY", "MT"]
    coastal_exp = sum(states[s]["avg_exposure"] * states[s]["total_workers"] for s in coastal) / sum(states[s]["total_workers"] for s in coastal)
    inland_exp = sum(states[s]["avg_exposure"] * states[s]["total_workers"] for s in inland) / sum(states[s]["total_workers"] for s in inland)
    coastal_pay = sum(states[s]["avg_pay"] * states[s]["total_workers"] for s in coastal) / sum(states[s]["total_workers"] for s in coastal)
    inland_pay = sum(states[s]["avg_pay"] * states[s]["total_workers"] for s in inland) / sum(states[s]["total_workers"] for s in inland)

    insights.append({
        "id": "coastal-vs-inland-exposure",
        "category": "Regional",
        "title": "Coastal States Average Higher AI Exposure Than the Interior",
        "subtitle": f"Coastal average: {coastal_exp:.1f}/10 vs. inland: {inland_exp:.1f}/10.",
        "body_html": (
            f"<p>Comparing ten major coastal states against ten interior states reveals a consistent gap: coastal workforces "
            f"average <strong>{coastal_exp:.1f}</strong> on the AI exposure scale vs. <strong>{inland_exp:.1f}</strong> for "
            f"inland states. The coastal states also pay significantly more, averaging <strong>{fmt_money(coastal_pay)}</strong> "
            f"compared to <strong>{fmt_money(inland_pay)}</strong> inland.</p>"
            f"<p>The divide reflects a structural difference in economic composition. Coastal economies are weighted toward "
            f"finance, technology, media, and professional services -- all sectors with exposure scores above 6. Interior "
            f"states rely more heavily on agriculture, manufacturing, and logistics, where physical tasks limit AI's reach. "
            f"The irony is that the states best positioned to <em>build</em> AI tools are also the most vulnerable to them.</p>"
        ),
        "headline_stat": f"{coastal_exp:.1f}",
        "headline_label": "average exposure score in coastal states",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": "Coastal states", "value": coastal_exp, "formatted": f"{coastal_exp:.1f}/10"},
                {"label": "Inland states", "value": inland_exp, "formatted": f"{inland_exp:.1f}/10"},
            ]
        },
        "generated_at": TODAY,
        "tags": ["states", "regional", "exposure"]
    })

    # 10. Lowest exposure states
    bottom5_exp = states_by_exp[-5:][::-1]
    insights.append({
        "id": "lowest-exposure-states",
        "category": "Regional",
        "title": f"Wyoming and Nevada Have the Nation's Lowest AI Exposure Scores",
        "subtitle": "States with economies built on physical labor and tourism face less AI disruption.",
        "body_html": (
            f"<p>Wyoming (<strong>{states['WY']['avg_exposure']}/10</strong>), Nevada (<strong>{states['NV']['avg_exposure']}/10</strong>), "
            f"and Louisiana (<strong>{states['LA']['avg_exposure']}/10</strong>) record the lowest average AI exposure. "
            f"These states share a common economic profile: heavy reliance on extraction industries, hospitality, physical labor, "
            f"and transportation.</p>"
            f"<p>Low exposure does not mean immunity. Even in Nevada, where the gaming and hospitality economy keeps the "
            f"state average down, customer service representatives (<strong>29,910</strong> workers) carry an exposure "
            f"score of 8 out of 10. The state-level average can mask significant pockets of vulnerable workers. "
            f"Still, the overall structural risk is meaningfully lower than in knowledge-economy hubs.</p>"
        ),
        "headline_stat": f"{states['WY']['avg_exposure']}",
        "headline_label": "average exposure in Wyoming (lowest nationally)",
        "chart": {
            "type": "horizontal_bar",
            "data": [{"label": v["name"], "value": v["avg_exposure"], "formatted": f"{v['avg_exposure']}/10"} for _, v in bottom5_exp]
        },
        "generated_at": TODAY,
        "tags": ["states", "exposure", "regional"]
    })

    # ══════════════════════════════════════════════════════════════
    # OCCUPATIONS (5-6 insights)
    # ══════════════════════════════════════════════════════════════

    sorted_by_exp = sorted(data, key=lambda x: x["exposure"], reverse=True)
    sorted_by_jobs = sorted(data, key=lambda x: x["jobs"], reverse=True)

    # 11. Most exposed occupations
    top_exp = [o for o in sorted_by_exp if o["exposure"] >= 9][:5]
    insights.append({
        "id": "most-exposed-occupations",
        "category": "Occupations",
        "title": "The Occupations in AI's Crosshairs: Exposure Scores of 9 or 10",
        "subtitle": f"{len([o for o in data if o['exposure'] >= 9])} occupations score 9 or higher on the AI exposure scale.",
        "body_html": (
            f"<p>At the extreme end of AI exposure, occupations scoring <strong>9 or 10 out of 10</strong> include "
            f"roles like <strong>{top_exp[0]['title']}</strong> (exposure: {top_exp[0]['exposure']}), "
            f"<strong>{top_exp[1]['title']}</strong> ({top_exp[1]['exposure']}), and "
            f"<strong>{top_exp[2]['title']}</strong> ({top_exp[2]['exposure']}). "
            f"These occupations share a common trait: their core tasks involve processing, analyzing, or generating "
            f"information in digital formats that AI models can handle with increasing competence.</p>"
            f"<p>Together, occupations scoring 9+ employ <strong>{fmt_num(sum(o['jobs'] for o in data if o['exposure'] >= 9))}</strong> "
            f"workers. Many of these are well-compensated positions -- the average pay across this group is "
            f"<strong>{fmt_money(sum(o['pay'] * o['jobs'] for o in data if o['exposure'] >= 9) / sum(o['jobs'] for o in data if o['exposure'] >= 9))}</strong>. "
            f"High pay has historically insulated workers from disruption, but AI does not follow the same rules as previous waves of automation.</p>"
        ),
        "headline_stat": f"{len([o for o in data if o['exposure'] >= 9])}",
        "headline_label": "occupations with exposure scores of 9 or higher",
        "chart": {
            "type": "table",
            "data": [{"label": o["title"], "value": o["exposure"], "formatted": f"{o['exposure']}/10", "workers": fmt_num(o["jobs"])} for o in top_exp]
        },
        "generated_at": TODAY,
        "tags": ["exposure", "occupations", "automation"]
    })

    # 12. Safest large occupations
    large_occs = [o for o in data if o["jobs"] >= 500_000]
    safest_large = sorted(large_occs, key=lambda x: x["exposure"])[:5]

    insights.append({
        "id": "safest-large-occupations",
        "category": "Occupations",
        "title": "Millions of Jobs in Occupations Where AI Has Limited Reach",
        "subtitle": "Physical, hands-on occupations with large workforces remain relatively insulated.",
        "body_html": (
            f"<p>Among occupations employing at least 500,000 workers, the lowest AI exposure belongs to "
            f"<strong>{safest_large[0]['title']}</strong> (exposure: {safest_large[0]['exposure']}, "
            f"{fmt_num(safest_large[0]['jobs'])} workers), followed by "
            f"<strong>{safest_large[1]['title']}</strong> ({safest_large[1]['exposure']}) and "
            f"<strong>{safest_large[2]['title']}</strong> ({safest_large[2]['exposure']}). "
            f"These roles share a dependence on physical presence, dexterity, and unpredictable real-world environments "
            f"that current AI systems cannot navigate.</p>"
            f"<p>Combined, the five safest large occupations employ <strong>{fmt_millions(sum(o['jobs'] for o in safest_large))}</strong> "
            f"workers. Their average pay is <strong>{fmt_money(sum(o['pay'] * o['jobs'] for o in safest_large) / sum(o['jobs'] for o in safest_large))}</strong>, "
            f"well below the national average for tracked occupations. Safety from AI disruption, in other words, "
            f"is correlated with lower wages -- a troubling dynamic for workforce planning.</p>"
        ),
        "headline_stat": str(safest_large[0]["exposure"]),
        "headline_label": f"exposure score for {safest_large[0]['title']} ({fmt_num(safest_large[0]['jobs'])} workers)",
        "chart": {
            "type": "table",
            "data": [{"label": o["title"], "value": o["exposure"], "formatted": f"{o['exposure']}/10", "workers": fmt_num(o["jobs"])} for o in safest_large]
        },
        "generated_at": TODAY,
        "tags": ["occupations", "safety", "physical-labor"]
    })

    # 13. Highest opportunity occupations
    sorted_by_opp = sorted(data, key=lambda x: x.get("opportunity", 0), reverse=True)
    top_opp = sorted_by_opp[:5]

    insights.append({
        "id": "highest-opportunity-occupations",
        "category": "Occupations",
        "title": "Where AI Creates More Than It Destroys: The Highest Opportunity Jobs",
        "subtitle": "Some occupations score high on both exposure and opportunity, suggesting augmentation over replacement.",
        "body_html": (
            f"<p>Not all AI exposure is bad news. Occupations like <strong>{top_opp[0]['title']}</strong> "
            f"(opportunity: {top_opp[0]['opportunity']:.0f}), <strong>{top_opp[1]['title']}</strong> "
            f"({top_opp[1]['opportunity']:.0f}), and <strong>{top_opp[2]['title']}</strong> ({top_opp[2]['opportunity']:.0f}) "
            f"score among the highest on the opportunity index, which measures the net potential for AI to enhance "
            f"rather than displace workers.</p>"
            f"<p>These roles tend to combine high exposure with strong advantage scores -- meaning workers can use AI tools "
            f"to become more productive rather than being replaced by them. The occupations also tend to have "
            f"positive growth outlooks from BLS projections, suggesting that demand for these workers will rise even as "
            f"AI reshapes what they do day-to-day. The key differentiator: human judgment, creativity, and relationship "
            f"management remain central to the work.</p>"
        ),
        "headline_stat": f"{top_opp[0]['opportunity']:.0f}",
        "headline_label": f"opportunity score for {top_opp[0]['title']}",
        "chart": {
            "type": "table",
            "data": [{"label": o["title"], "value": o["opportunity"], "formatted": f"{o['opportunity']:.0f}/10", "workers": fmt_num(o["jobs"])} for o in top_opp]
        },
        "generated_at": TODAY,
        "tags": ["opportunity", "occupations", "augmentation"]
    })

    # 14. Highest paid at risk
    high_exp_high_pay = sorted([o for o in data if o["exposure"] >= 7], key=lambda x: x["pay"], reverse=True)[:5]

    insights.append({
        "id": "highest-paid-at-risk",
        "category": "Occupations",
        "title": f"The {fmt_money(high_exp_high_pay[0]['pay'])} Question: When High Pay Meets High Exposure",
        "subtitle": "The most expensive jobs to displace are also among the most exposed to AI.",
        "body_html": (
            f"<p>Among occupations with AI exposure scores of 7 or higher, the highest-paid include "
            f"<strong>{high_exp_high_pay[0]['title']}</strong> ({fmt_money(high_exp_high_pay[0]['pay'])}), "
            f"<strong>{high_exp_high_pay[1]['title']}</strong> ({fmt_money(high_exp_high_pay[1]['pay'])}), and "
            f"<strong>{high_exp_high_pay[2]['title']}</strong> ({fmt_money(high_exp_high_pay[2]['pay'])}). "
            f"These positions represent exactly the kind of high-value knowledge work that AI is increasingly capable of performing.</p>"
            f"<p>The economic incentive for employers to adopt AI in these roles is enormous. A single "
            f"{high_exp_high_pay[0]['title'].lower()} earning {fmt_money(high_exp_high_pay[0]['pay'])} represents a significant "
            f"cost that AI could partially offset. The {fmt_num(high_exp_high_pay[0]['jobs'])} workers in that occupation alone "
            f"represent billions in annual compensation that firms are actively looking to optimize with AI tools.</p>"
        ),
        "headline_stat": fmt_money(high_exp_high_pay[0]["pay"]),
        "headline_label": f"median pay for {high_exp_high_pay[0]['title']} (exposure: {high_exp_high_pay[0]['exposure']}/10)",
        "chart": {
            "type": "table",
            "data": [{"label": o["title"], "value": o["pay"], "formatted": fmt_money(o["pay"]), "workers": f"Exp: {o['exposure']}/10"} for o in high_exp_high_pay]
        },
        "generated_at": TODAY,
        "tags": ["salary", "exposure", "occupations", "risk"]
    })

    # 15. Largest occupations by employment
    top5_by_jobs = sorted_by_jobs[:5]
    insights.append({
        "id": "largest-occupations-employment",
        "category": "Occupations",
        "title": f"The Big Five: {fmt_millions(sum(o['jobs'] for o in top5_by_jobs))} Workers in America's Largest Occupations",
        "subtitle": "The five biggest occupations span the full spectrum of AI exposure.",
        "body_html": (
            f"<p>The largest occupation by employment is <strong>{top5_by_jobs[0]['title']}</strong> with "
            f"<strong>{fmt_millions(top5_by_jobs[0]['jobs'])}</strong> workers and an exposure score of "
            f"<strong>{top5_by_jobs[0]['exposure']}/10</strong>. It is followed by "
            f"<strong>{top5_by_jobs[1]['title']}</strong> ({fmt_millions(top5_by_jobs[1]['jobs'])}, exposure: {top5_by_jobs[1]['exposure']}) "
            f"and <strong>{top5_by_jobs[2]['title']}</strong> ({fmt_millions(top5_by_jobs[2]['jobs'])}, exposure: {top5_by_jobs[2]['exposure']}).</p>"
            f"<p>What stands out is the variation: the largest occupations are not uniformly safe or exposed. "
            f"Some, like registered nurses, combine large employment with moderate exposure. Others, like customer service "
            f"representatives, sit squarely in AI's path. The sheer scale of these occupations means that even modest "
            f"productivity gains from AI could reshape millions of positions within a few years.</p>"
        ),
        "headline_stat": fmt_millions(top5_by_jobs[0]["jobs"]),
        "headline_label": f"workers in {top5_by_jobs[0]['title']} (largest occupation)",
        "chart": {
            "type": "table",
            "data": [{"label": o["title"], "value": o["jobs"], "formatted": fmt_num(o["jobs"]), "workers": f"Exp: {o['exposure']}/10"} for o in top5_by_jobs]
        },
        "generated_at": TODAY,
        "tags": ["occupations", "employment", "workforce"]
    })

    # ══════════════════════════════════════════════════════════════
    # SECTORS (4-5 insights)
    # ══════════════════════════════════════════════════════════════

    categories = summary["categories"]
    cats_sorted_exp = sorted(categories, key=lambda x: x["avg_exposure"], reverse=True)

    # 16. Category comparison
    insights.append({
        "id": "sector-exposure-ranking",
        "category": "Sectors",
        "title": "Math, IT, and Legal: The Three Most AI-Exposed Sectors",
        "subtitle": f"Average exposure ranges from {cats_sorted_exp[-1]['avg_exposure']}/10 to {cats_sorted_exp[0]['avg_exposure']}/10 across sectors.",
        "body_html": (
            f"<p>The math and statistics sector leads with an average exposure of <strong>{cats_sorted_exp[0]['avg_exposure']}/10</strong>, "
            f"followed by computer and IT (<strong>{cats_sorted_exp[1]['avg_exposure']}/10</strong>) and legal "
            f"(<strong>{cats_sorted_exp[2]['avg_exposure']}/10</strong>). At the other end, building and grounds cleaning "
            f"(<strong>{cats_sorted_exp[-1]['avg_exposure']}/10</strong>) is the least exposed sector.</p>"
            f"<p>The gap between the most and least exposed sectors is enormous: <strong>{cats_sorted_exp[0]['avg_exposure'] - cats_sorted_exp[-1]['avg_exposure']:.1f} points</strong> "
            f"on a 10-point scale. This divergence will reshape economic geography and career planning. A student choosing "
            f"between a career in IT (exposure: 8.5, avg pay: {fmt_money(108960)}) and construction (exposure: 1.8, avg pay: "
            f"{fmt_money(55528)}) faces a genuinely new kind of trade-off that did not exist a decade ago.</p>"
        ),
        "headline_stat": f"{cats_sorted_exp[0]['avg_exposure']}",
        "headline_label": f"average exposure for {cat_label(cats_sorted_exp[0]['name'])} (highest sector)",
        "chart": {
            "type": "horizontal_bar",
            "data": [{"label": cat_label(c["name"]), "value": c["avg_exposure"], "formatted": f"{c['avg_exposure']}/10"} for c in cats_sorted_exp[:5]]
        },
        "generated_at": TODAY,
        "tags": ["sectors", "exposure", "comparison"]
    })

    # 17. Healthcare sector
    hc = next(c for c in categories if c["name"] == "healthcare")
    insights.append({
        "id": "healthcare-sector-profile",
        "category": "Sectors",
        "title": f"Healthcare's 17.5 Million Workers Face Moderate AI Exposure",
        "subtitle": f"The largest sector by occupation count has an average exposure of just {hc['avg_exposure']}/10.",
        "body_html": (
            f"<p>Healthcare employs <strong>{fmt_millions(hc['total_workers'])}</strong> workers across "
            f"<strong>{hc['occupations']}</strong> tracked occupations, making it the most occupationally diverse sector. "
            f"Yet its average AI exposure is a modest <strong>{hc['avg_exposure']}/10</strong>, reflecting the physical, "
            f"interpersonal nature of most clinical work.</p>"
            f"<p>The sector is not monolithic, though. Radiologists and medical coders face exposure scores of 7 or higher, "
            f"while home health aides and surgical technologists score 2 or below. The average masks a widening internal "
            f"divide: AI is transforming diagnostics and documentation while leaving bedside care largely untouched. "
            f"With average pay of <strong>{fmt_money(hc['avg_pay'])}</strong>, healthcare workers are generally better "
            f"compensated than the overall workforce, adding another layer to the disruption calculus.</p>"
        ),
        "headline_stat": fmt_millions(hc["total_workers"]),
        "headline_label": "healthcare workers across 49 occupations",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": "Healthcare", "value": hc["avg_exposure"], "formatted": f"{hc['avg_exposure']}/10"},
                {"label": "Computer & IT", "value": 8.5, "formatted": "8.5/10"},
                {"label": "Construction", "value": 1.8, "formatted": "1.8/10"},
            ]
        },
        "generated_at": TODAY,
        "tags": ["healthcare", "sectors", "exposure"]
    })

    # 18. Tech paradox
    it_cat = next(c for c in categories if c["name"] == "computer-and-information-technology")
    insights.append({
        "id": "tech-paradox-builders-exposed",
        "category": "Sectors",
        "title": "The Tech Paradox: AI's Builders Are Also Its Most Exposed Workers",
        "subtitle": f"Computer and IT workers earn {fmt_money(it_cat['avg_pay'])} on average but face {it_cat['avg_exposure']}/10 exposure.",
        "body_html": (
            f"<p>The <strong>{fmt_millions(it_cat['total_workers'])}</strong> workers in computer and information technology "
            f"occupations sit at a unique intersection: they build the AI systems that could automate their own work. "
            f"With an average exposure score of <strong>{it_cat['avg_exposure']}/10</strong> and average pay of "
            f"<strong>{fmt_money(it_cat['avg_pay'])}</strong>, this sector has among the highest stakes in the AI transition.</p>"
            f"<p>The saving grace is the advantage score. IT workers generally have the skills and domain knowledge to "
            f"leverage AI as a productivity multiplier rather than a replacement. Code generation tools, automated testing, "
            f"and AI-assisted debugging are already reshaping workflows without eliminating positions. But the sector's "
            f"relatively small size -- just <strong>{it_cat['occupations']}</strong> occupations -- means that changes here "
            f"reverberate far beyond tech companies, as every industry depends on IT infrastructure.</p>"
        ),
        "headline_stat": f"{it_cat['avg_exposure']}/10",
        "headline_label": "average AI exposure for computer & IT occupations",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": "Exposure", "value": it_cat["avg_exposure"], "formatted": f"{it_cat['avg_exposure']}/10"},
                {"label": "Avg Pay ($K)", "value": it_cat["avg_pay"] / 1000, "formatted": fmt_money(it_cat["avg_pay"])},
            ]
        },
        "generated_at": TODAY,
        "tags": ["technology", "sectors", "paradox", "exposure"]
    })

    # 19. Admin jobs crisis
    admin_cat = next(c for c in categories if c["name"] == "office-and-administrative-support")
    insights.append({
        "id": "admin-jobs-crisis",
        "category": "Sectors",
        "title": f"The Administrative Jobs Crisis: {fmt_millions(admin_cat['total_workers'])} Workers, Exposure of {admin_cat['avg_exposure']}/10",
        "subtitle": "Office support is the largest high-exposure sector by total employment.",
        "body_html": (
            f"<p>Office and administrative support is the second-largest sector by employment at "
            f"<strong>{fmt_millions(admin_cat['total_workers'])}</strong> workers, and it has the fourth-highest "
            f"average AI exposure at <strong>{admin_cat['avg_exposure']}/10</strong>. No other sector combines "
            f"such massive scale with such high exposure.</p>"
            f"<p>The average pay of <strong>{fmt_money(admin_cat['avg_pay'])}</strong> positions these workers squarely "
            f"in the middle class, and the sector's <strong>{admin_cat['occupations']}</strong> occupations include roles "
            f"like data entry keyers, bookkeepers, and general office clerks -- jobs whose core tasks map almost perfectly "
            f"to what AI excels at. This sector may represent the single largest concentration of workers whose jobs "
            f"will be fundamentally reshaped by AI within the next decade.</p>"
        ),
        "headline_stat": fmt_millions(admin_cat["total_workers"]),
        "headline_label": "administrative support workers at high exposure",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": cat_label(c["name"]), "value": c["total_workers"] / 1_000_000, "formatted": fmt_millions(c["total_workers"])}
                for c in sorted(categories, key=lambda x: x["total_workers"], reverse=True)[:5]
            ]
        },
        "generated_at": TODAY,
        "tags": ["administrative", "sectors", "exposure", "middle-class"]
    })

    # 20. Food service: shielded sector
    food_cat = next(c for c in categories if c["name"] == "food-preparation-and-serving")
    insights.append({
        "id": "food-service-shielded",
        "category": "Sectors",
        "title": f"12 Million Food Service Workers Remain Largely Shielded From AI",
        "subtitle": f"Physical, in-person work keeps food service exposure at just {food_cat['avg_exposure']}/10.",
        "body_html": (
            f"<p>The food preparation and serving sector employs <strong>{fmt_millions(food_cat['total_workers'])}</strong> "
            f"workers with an average AI exposure of just <strong>{food_cat['avg_exposure']}/10</strong>. "
            f"These are the cooks, waiters, and food prep workers whose jobs demand physical presence, "
            f"real-time human interaction, and manual dexterity that AI cannot replicate.</p>"
            f"<p>But low exposure comes at a cost. The sector's average pay of <strong>{fmt_money(food_cat['avg_pay'])}</strong> "
            f"is among the lowest of any category, and it offers limited upward mobility. Workers in food service may be "
            f"safe from AI displacement, but they are also unlikely to benefit from the productivity gains that AI brings "
            f"to higher-paying sectors. In an AI-driven economy, being insulated from disruption may also mean being "
            f"insulated from its economic upside.</p>"
        ),
        "headline_stat": fmt_millions(food_cat["total_workers"]),
        "headline_label": "food service workers with low AI exposure",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": "Food Service", "value": food_cat["avg_exposure"], "formatted": f"{food_cat['avg_exposure']}/10"},
                {"label": "Cleaning & Grounds", "value": 1.0, "formatted": "1.0/10"},
                {"label": "Construction", "value": 1.8, "formatted": "1.8/10"},
                {"label": "National Average", "value": 5.3, "formatted": "5.3/10"},
            ]
        },
        "generated_at": TODAY,
        "tags": ["food-service", "sectors", "safety"]
    })

    # ══════════════════════════════════════════════════════════════
    # LABOR MARKET (5-6 insights)
    # ══════════════════════════════════════════════════════════════

    total_workers = summary["total_workers"]
    total_occs = summary["total_occupations"]

    # 21. Risk tier distribution
    high_risk = [o for o in data if o["exposure"] >= 7]
    med_risk = [o for o in data if 4 <= o["exposure"] < 7]
    low_risk = [o for o in data if o["exposure"] < 4]
    high_jobs = sum(o["jobs"] for o in high_risk)
    med_jobs = sum(o["jobs"] for o in med_risk)
    low_jobs = sum(o["jobs"] for o in low_risk)

    insights.append({
        "id": "risk-tier-distribution",
        "category": "Labor Market",
        "title": f"49 Million Workers in High-Exposure Occupations",
        "subtitle": f"{len(high_risk)} of {total_occs} occupations have exposure scores of 7 or higher.",
        "body_html": (
            f"<p><strong>{fmt_millions(high_jobs)}</strong> Americans work in occupations with AI exposure scores of 7 or "
            f"higher on a 10-point scale. Another <strong>{fmt_millions(med_jobs)}</strong> sit in the moderate zone (4-6), "
            f"and <strong>{fmt_millions(low_jobs)}</strong> work in low-exposure occupations (1-3).</p>"
            f"<p>The distribution is roughly even by worker count, but the occupational count tells a different story: "
            f"<strong>{len(high_risk)}</strong> occupations are high-exposure vs. <strong>{len(med_risk)}</strong> moderate "
            f"and <strong>{len(low_risk)}</strong> low. High-exposure jobs tend to be larger in employment, meaning "
            f"each one affects more workers. The median occupation in the high-risk tier has "
            f"<strong>{fmt_num(sorted([o['jobs'] for o in high_risk])[len(high_risk)//2])}</strong> workers.</p>"
        ),
        "headline_stat": fmt_millions(high_jobs),
        "headline_label": "workers in high-exposure occupations (7+ out of 10)",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": "High (7-10)", "value": high_jobs / 1_000_000, "formatted": fmt_millions(high_jobs)},
                {"label": "Moderate (4-6)", "value": med_jobs / 1_000_000, "formatted": fmt_millions(med_jobs)},
                {"label": "Low (1-3)", "value": low_jobs / 1_000_000, "formatted": fmt_millions(low_jobs)},
            ]
        },
        "generated_at": TODAY,
        "tags": ["risk", "exposure", "labor-market"]
    })

    # 22. Salary vs exposure correlation
    high_avg_pay = sum(o["pay"] * o["jobs"] for o in high_risk) / high_jobs if high_jobs else 0
    med_avg_pay = sum(o["pay"] * o["jobs"] for o in med_risk) / med_jobs if med_jobs else 0
    low_avg_pay = sum(o["pay"] * o["jobs"] for o in low_risk) / low_jobs if low_jobs else 0

    insights.append({
        "id": "salary-exposure-correlation",
        "category": "Labor Market",
        "title": "Higher Exposure, Higher Pay: AI Targets Well-Compensated Work",
        "subtitle": f"High-exposure occupations average {fmt_money(high_avg_pay)} vs. {fmt_money(low_avg_pay)} for low-exposure.",
        "body_html": (
            f"<p>Workers in high-exposure occupations (score 7+) earn an average of <strong>{fmt_money(high_avg_pay)}</strong>, "
            f"compared to <strong>{fmt_money(med_avg_pay)}</strong> for moderate-exposure roles and "
            f"<strong>{fmt_money(low_avg_pay)}</strong> for low-exposure positions. The pattern is unambiguous: "
            f"AI exposure increases with compensation.</p>"
            f"<p>This reverses the historical pattern of automation, which predominantly affected lower-wage manufacturing "
            f"and service jobs. AI is the first major technological disruption to target the upper half of the income "
            f"distribution. The economic incentive for adoption is clear -- automating a <strong>{fmt_money(high_avg_pay)}</strong> "
            f"task is far more attractive than automating a <strong>{fmt_money(low_avg_pay)}</strong> one. "
            f"For employers, the return on AI investment is highest precisely where salaries are highest.</p>"
        ),
        "headline_stat": fmt_money(high_avg_pay),
        "headline_label": "average pay in high-exposure occupations",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": "High exposure (7+)", "value": high_avg_pay / 1000, "formatted": fmt_money(high_avg_pay)},
                {"label": "Moderate (4-6)", "value": med_avg_pay / 1000, "formatted": fmt_money(med_avg_pay)},
                {"label": "Low exposure (1-3)", "value": low_avg_pay / 1000, "formatted": fmt_money(low_avg_pay)},
            ]
        },
        "generated_at": TODAY,
        "tags": ["salary", "exposure", "labor-market", "automation"]
    })

    # 23. Growth vs decline
    growing = [o for o in data if o["outlook"] >= 5]
    declining = [o for o in data if o["outlook"] <= 0]
    stable = [o for o in data if 1 <= o["outlook"] < 5]
    growing_jobs = sum(o["jobs"] for o in growing)
    declining_jobs = sum(o["jobs"] for o in declining)
    growing_avg_exp = sum(o["exposure"] * o["jobs"] for o in growing) / growing_jobs if growing_jobs else 0
    declining_avg_exp = sum(o["exposure"] * o["jobs"] for o in declining) / declining_jobs if declining_jobs else 0

    insights.append({
        "id": "growth-vs-decline-outlook",
        "category": "Labor Market",
        "title": "Growing Occupations Have Higher AI Exposure Than Declining Ones",
        "subtitle": f"Faster-growing occupations average {growing_avg_exp:.1f}/10 exposure vs. {declining_avg_exp:.1f}/10 for declining.",
        "body_html": (
            f"<p>Occupations with faster-than-average growth projections (BLS outlook 5+) employ "
            f"<strong>{fmt_millions(growing_jobs)}</strong> workers and have an average exposure of "
            f"<strong>{growing_avg_exp:.1f}/10</strong>. Meanwhile, occupations projected to decline employ "
            f"<strong>{fmt_millions(declining_jobs)}</strong> workers with average exposure of "
            f"<strong>{declining_avg_exp:.1f}/10</strong>.</p>"
            f"<p>This counterintuitive finding suggests that AI exposure does not necessarily mean job loss. "
            f"Many of the fastest-growing occupations -- software developers, data analysts, management consultants -- "
            f"are also the most AI-exposed. The growth in these fields reflects rising demand that more than offsets "
            f"AI's labor-saving effects. The occupations actually projected to shrink tend to be declining for older "
            f"reasons: changing consumer habits, offshoring, and structural economic shifts predating the AI revolution.</p>"
        ),
        "headline_stat": f"{growing_avg_exp:.1f}",
        "headline_label": "average exposure for growing occupations",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": f"Growing ({len(growing)} occ.)", "value": growing_avg_exp, "formatted": f"{growing_avg_exp:.1f}/10"},
                {"label": f"Stable ({len(stable)} occ.)", "value": sum(o['exposure']*o['jobs'] for o in stable)/sum(o['jobs'] for o in stable) if stable else 0, "formatted": f"{sum(o['exposure']*o['jobs'] for o in stable)/sum(o['jobs'] for o in stable):.1f}/10" if stable else "N/A"},
                {"label": f"Declining ({len(declining)} occ.)", "value": declining_avg_exp, "formatted": f"{declining_avg_exp:.1f}/10"},
            ]
        },
        "generated_at": TODAY,
        "tags": ["growth", "labor-market", "outlook"]
    })

    # 24. Middle class squeeze
    middle_class = [o for o in data if 40_000 <= o["pay"] <= 80_000]
    mc_jobs = sum(o["jobs"] for o in middle_class)
    mc_avg_exp = sum(o["exposure"] * o["jobs"] for o in middle_class) / mc_jobs if mc_jobs else 0
    mc_high_exp = [o for o in middle_class if o["exposure"] >= 7]
    mc_high_jobs = sum(o["jobs"] for o in mc_high_exp)

    insights.append({
        "id": "middle-class-squeeze",
        "category": "Labor Market",
        "title": f"The Middle-Class Squeeze: {fmt_millions(mc_high_jobs)} Mid-Salary Workers at High Exposure",
        "subtitle": f"Workers earning $40K-$80K average {mc_avg_exp:.1f}/10 exposure, with many in the danger zone.",
        "body_html": (
            f"<p>Among the <strong>{fmt_millions(mc_jobs)}</strong> workers earning between $40,000 and $80,000, "
            f"the average AI exposure score is <strong>{mc_avg_exp:.1f}/10</strong>. More concerning, "
            f"<strong>{fmt_millions(mc_high_jobs)}</strong> of these middle-income workers are in occupations "
            f"scoring 7 or higher -- squarely in the high-exposure zone.</p>"
            f"<p>These are the bookkeepers, insurance underwriters, and paralegal assistants who form the backbone "
            f"of America's middle class. Their jobs require enough skill to command decent wages but are structured "
            f"enough for AI to handle significant portions of the work. Unlike lower-paid service workers (who are "
            f"insulated by physical labor) or higher-paid professionals (who can pivot to strategic roles), "
            f"middle-income knowledge workers face the greatest structural pressure from AI adoption.</p>"
        ),
        "headline_stat": fmt_millions(mc_high_jobs),
        "headline_label": "mid-salary workers ($40K-$80K) with high AI exposure",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": "High exposure", "value": mc_high_jobs / 1_000_000, "formatted": fmt_millions(mc_high_jobs)},
                {"label": "Moderate", "value": (mc_jobs - mc_high_jobs - sum(o["jobs"] for o in middle_class if o["exposure"] < 4)) / 1_000_000, "formatted": fmt_millions(mc_jobs - mc_high_jobs - sum(o["jobs"] for o in middle_class if o["exposure"] < 4))},
                {"label": "Low exposure", "value": sum(o["jobs"] for o in middle_class if o["exposure"] < 4) / 1_000_000, "formatted": fmt_millions(sum(o["jobs"] for o in middle_class if o["exposure"] < 4))},
            ]
        },
        "generated_at": TODAY,
        "tags": ["middle-class", "labor-market", "salary", "exposure"]
    })

    # 25. 143 million workers overview
    nat_avg_exp = sum(o["exposure"] * o["jobs"] for o in data) / total_workers
    nat_avg_pay = sum(o["pay"] * o["jobs"] for o in data) / total_workers

    insights.append({
        "id": "national-workforce-overview",
        "category": "Labor Market",
        "title": f"143 Million Workers, 342 Occupations: The AI Exposure Landscape",
        "subtitle": f"The national weighted average exposure score is {nat_avg_exp:.1f} out of 10.",
        "body_html": (
            f"<p>Across <strong>{total_occs}</strong> tracked occupations, <strong>{fmt_millions(total_workers)}</strong> "
            f"American workers face an average AI exposure score of <strong>{nat_avg_exp:.1f} out of 10</strong>. "
            f"The weighted average pay is <strong>{fmt_money(nat_avg_pay)}</strong>. These figures represent one of the "
            f"most comprehensive snapshots of AI's potential labor market impact to date.</p>"
            f"<p>The occupations range from janitors (exposure: 1) to actuaries and translators (exposure: 10), "
            f"spanning every corner of the American economy. The data shows that AI exposure is not a niche concern -- "
            f"it touches the full breadth of the labor market, from minimum-wage food service to six-figure professional "
            f"roles. No sector is entirely immune, and no sector is entirely doomed.</p>"
        ),
        "headline_stat": fmt_millions(total_workers),
        "headline_label": f"workers across {total_occs} occupations tracked for AI exposure",
        "chart": {
            "type": "stat_card",
            "data": []
        },
        "generated_at": TODAY,
        "tags": ["overview", "labor-market", "workforce"]
    })

    # 26. Advantage vs exposure
    high_adv = [o for o in data if o.get("advantage", 0) >= 7 and o["exposure"] >= 7]
    high_adv_jobs = sum(o["jobs"] for o in high_adv)
    low_adv = [o for o in data if o.get("advantage", 0) <= 3 and o["exposure"] >= 7]
    low_adv_jobs = sum(o["jobs"] for o in low_adv)

    insights.append({
        "id": "advantage-vs-exposure",
        "category": "Labor Market",
        "title": "Not All Exposure Is Equal: High-Advantage Roles Can Thrive With AI",
        "subtitle": f"{fmt_millions(high_adv_jobs)} highly-exposed workers also have high advantage scores.",
        "body_html": (
            f"<p>Among occupations with high AI exposure (7+), there is a critical divide: "
            f"<strong>{fmt_millions(high_adv_jobs)}</strong> workers are in roles where AI also provides strong advantages "
            f"(advantage score 7+), meaning they can use AI tools to amplify their productivity. "
            f"By contrast, <strong>{fmt_millions(low_adv_jobs)}</strong> workers are in high-exposure roles with "
            f"low advantage scores (3 or below), meaning AI is more likely to replace than augment them.</p>"
            f"<p>The distinction matters enormously for policy. A software developer using AI to write code faster is "
            f"in a fundamentally different position from a data entry clerk whose entire job can be automated. Both "
            f"show high exposure, but the outcomes are vastly different. Workforce programs that treat all 'high-exposure' "
            f"workers the same will miss this crucial nuance.</p>"
        ),
        "headline_stat": fmt_millions(high_adv_jobs),
        "headline_label": "workers with both high exposure and high advantage",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": "High advantage + exposure", "value": high_adv_jobs / 1_000_000, "formatted": fmt_millions(high_adv_jobs)},
                {"label": "Low advantage + exposure", "value": low_adv_jobs / 1_000_000, "formatted": fmt_millions(low_adv_jobs)},
            ]
        },
        "generated_at": TODAY,
        "tags": ["advantage", "exposure", "labor-market", "augmentation"]
    })

    # ══════════════════════════════════════════════════════════════
    # EDUCATION (3-4 insights)
    # ══════════════════════════════════════════════════════════════

    # 27. Education vs exposure
    edu_groups = {}
    for o in data:
        edu = o.get("education", "")
        if not edu or edu == "See How to Become One":
            edu = "Other"
        if edu not in edu_groups:
            edu_groups[edu] = {"jobs": 0, "exp_weighted": 0, "pay_weighted": 0}
        edu_groups[edu]["jobs"] += o["jobs"]
        edu_groups[edu]["exp_weighted"] += o["exposure"] * o["jobs"]
        edu_groups[edu]["pay_weighted"] += o["pay"] * o["jobs"]

    edu_stats = []
    for edu, vals in edu_groups.items():
        if vals["jobs"] > 0 and edu != "Other":
            edu_stats.append({
                "education": edu,
                "jobs": vals["jobs"],
                "avg_exp": vals["exp_weighted"] / vals["jobs"],
                "avg_pay": vals["pay_weighted"] / vals["jobs"],
            })
    edu_stats.sort(key=lambda x: x["avg_exp"], reverse=True)

    insights.append({
        "id": "education-exposure-gradient",
        "category": "Education",
        "title": "The More Education Required, the Higher the AI Exposure",
        "subtitle": "Doctoral-level occupations have the highest average exposure, while no-credential jobs have the lowest.",
        "body_html": (
            f"<p>Occupations requiring a <strong>doctoral or professional degree</strong> have an average AI exposure of "
            f"<strong>{edu_stats[0]['avg_exp']:.1f}/10</strong>, while those requiring <strong>no formal credential</strong> "
            f"average just <strong>{[e for e in edu_stats if e['education'] == 'No formal educational credential'][0]['avg_exp']:.1f}/10</strong>. "
            f"The gradient is remarkably consistent: each step up the education ladder corresponds to higher AI exposure.</p>"
            f"<p>This pattern upends decades of workforce orthodoxy. The traditional advice -- 'get more education to protect "
            f"yourself from automation' -- no longer applies in the AI era. Advanced degrees lead to occupations whose "
            f"cognitive, analytical, and information-processing tasks are precisely what AI does best. "
            f"The workers with the least education are in physical, manual roles that AI struggles to replicate.</p>"
        ),
        "headline_stat": f"{edu_stats[0]['avg_exp']:.1f}",
        "headline_label": f"average exposure for doctoral-degree occupations",
        "chart": {
            "type": "horizontal_bar",
            "data": [{"label": e["education"][:30], "value": e["avg_exp"], "formatted": f"{e['avg_exp']:.1f}/10"} for e in edu_stats[:5]]
        },
        "generated_at": TODAY,
        "tags": ["education", "exposure", "degrees"]
    })

    # 28. Education vs pay
    insights.append({
        "id": "education-pay-premium",
        "category": "Education",
        "title": "Doctoral Degree Holders Earn the Most -- and Face the Highest AI Risk",
        "subtitle": "The education-pay premium remains strong, but so does the exposure premium.",
        "body_html": (
            f"<p>Workers in occupations requiring a doctoral or professional degree earn an average of "
            f"<strong>{fmt_money(edu_stats[0]['avg_pay'])}</strong>, the highest of any education tier. "
            f"Those in no-credential occupations earn just "
            f"<strong>{fmt_money([e for e in edu_stats if e['education'] == 'No formal educational credential'][0]['avg_pay'])}</strong>. "
            f"The pay premium for higher education remains enormous.</p>"
            f"<p>But the pay premium now comes with an exposure premium. The same cognitive complexity that commands "
            f"higher salaries also makes these jobs more amenable to AI augmentation and automation. Lawyers "
            f"(doctoral/professional degree, exposure: 8.3/10) earn well, but legal research, contract analysis, "
            f"and brief drafting are rapidly being handled by AI. The return on educational investment is shifting: "
            f"it is no longer enough to acquire knowledge -- workers must learn to work <em>alongside</em> AI.</p>"
        ),
        "headline_stat": fmt_money(edu_stats[0]["avg_pay"]),
        "headline_label": "average pay for doctoral-degree occupations",
        "chart": {
            "type": "horizontal_bar",
            "data": [{"label": e["education"][:30], "value": e["avg_pay"] / 1000, "formatted": fmt_money(e["avg_pay"])} for e in sorted(edu_stats, key=lambda x: x["avg_pay"], reverse=True)[:5]]
        },
        "generated_at": TODAY,
        "tags": ["education", "salary", "degrees"]
    })

    # 29. Bachelor's degree at risk
    bachelors = [o for o in data if o.get("education") == "Bachelor's degree"]
    ba_jobs = sum(o["jobs"] for o in bachelors)
    ba_avg_exp = sum(o["exposure"] * o["jobs"] for o in bachelors) / ba_jobs if ba_jobs else 0
    ba_high = [o for o in bachelors if o["exposure"] >= 7]
    ba_high_jobs = sum(o["jobs"] for o in ba_high)

    insights.append({
        "id": "bachelors-degree-risk",
        "category": "Education",
        "title": f"Bachelor's Degree Jobs: {fmt_millions(ba_high_jobs)} Workers in the High-Exposure Zone",
        "subtitle": f"Of {fmt_millions(ba_jobs)} bachelor's-level workers, {fmt_pct(ba_high_jobs/ba_jobs*100)} face high AI exposure.",
        "body_html": (
            f"<p>Occupations requiring a bachelor's degree employ <strong>{fmt_millions(ba_jobs)}</strong> workers "
            f"with an average AI exposure of <strong>{ba_avg_exp:.1f}/10</strong>. Of these, "
            f"<strong>{fmt_millions(ba_high_jobs)}</strong> -- or <strong>{fmt_pct(ba_high_jobs/ba_jobs*100)}</strong> -- "
            f"are in occupations scoring 7 or higher on the exposure scale.</p>"
            f"<p>The bachelor's degree has long been considered the baseline credential for professional success in America. "
            f"But {fmt_pct(ba_high_jobs/ba_jobs*100)} of bachelor's-level jobs are now in AI's high-exposure zone. "
            f"Accountants, market research analysts, and financial analysts -- all traditionally solid bachelor's-degree "
            f"careers -- face fundamental restructuring. The degree itself remains valuable, but the career paths "
            f"it unlocks are being reshaped faster than university curricula can adapt.</p>"
        ),
        "headline_stat": fmt_pct(ba_high_jobs / ba_jobs * 100),
        "headline_label": "of bachelor's-level workers in high-exposure occupations",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": "High exposure (7+)", "value": ba_high_jobs / 1_000_000, "formatted": fmt_millions(ba_high_jobs)},
                {"label": "Moderate (4-6)", "value": sum(o["jobs"] for o in bachelors if 4 <= o["exposure"] < 7) / 1_000_000, "formatted": fmt_millions(sum(o["jobs"] for o in bachelors if 4 <= o["exposure"] < 7))},
                {"label": "Low (1-3)", "value": sum(o["jobs"] for o in bachelors if o["exposure"] < 4) / 1_000_000, "formatted": fmt_millions(sum(o["jobs"] for o in bachelors if o["exposure"] < 4))},
            ]
        },
        "generated_at": TODAY,
        "tags": ["education", "bachelors", "exposure", "risk"]
    })

    # 30. High school diploma exposure
    hs = [o for o in data if o.get("education") == "High school diploma or equivalent"]
    hs_jobs = sum(o["jobs"] for o in hs)
    hs_avg_exp = sum(o["exposure"] * o["jobs"] for o in hs) / hs_jobs if hs_jobs else 0
    no_cred = [o for o in data if o.get("education") == "No formal educational credential"]
    nc_jobs = sum(o["jobs"] for o in no_cred)
    nc_avg_exp = sum(o["exposure"] * o["jobs"] for o in no_cred) / nc_jobs if nc_jobs else 0

    insights.append({
        "id": "high-school-diploma-insulation",
        "category": "Education",
        "title": f"High School Diploma Workers Average {hs_avg_exp:.1f}/10 Exposure -- Below the National Average",
        "subtitle": f"{fmt_millions(hs_jobs)} workers in high-school-level jobs face less AI disruption.",
        "body_html": (
            f"<p>The <strong>{fmt_millions(hs_jobs)}</strong> workers in occupations requiring a high school diploma "
            f"or equivalent have an average AI exposure of <strong>{hs_avg_exp:.1f}/10</strong>, below the national "
            f"weighted average of <strong>{nat_avg_exp:.1f}/10</strong>. Workers requiring no formal credential fare "
            f"even better at <strong>{nc_avg_exp:.1f}/10</strong> average exposure across "
            f"<strong>{fmt_millions(nc_jobs)}</strong> jobs.</p>"
            f"<p>These figures challenge the narrative that less-educated workers are most vulnerable to technological "
            f"disruption. For AI specifically, the opposite is true: the most exposed occupations are those requiring "
            f"college and professional degrees. High school-level and no-credential jobs tend to involve physical tasks, "
            f"customer-facing service, and unpredictable environments where AI has limited practical application. "
            f"This does not make these jobs <em>good</em> -- they remain low-paid -- but they are more durable in the face of AI.</p>"
        ),
        "headline_stat": f"{hs_avg_exp:.1f}",
        "headline_label": "average exposure for high-school-diploma occupations",
        "chart": {
            "type": "horizontal_bar",
            "data": [
                {"label": "No credential", "value": nc_avg_exp, "formatted": f"{nc_avg_exp:.1f}/10"},
                {"label": "High school diploma", "value": hs_avg_exp, "formatted": f"{hs_avg_exp:.1f}/10"},
                {"label": "Bachelor's degree", "value": ba_avg_exp, "formatted": f"{ba_avg_exp:.1f}/10"},
                {"label": "Doctoral/professional", "value": edu_stats[0]["avg_exp"], "formatted": f"{edu_stats[0]['avg_exp']:.1f}/10"},
            ]
        },
        "generated_at": TODAY,
        "tags": ["education", "high-school", "exposure"]
    })

    return insights


def main():
    data, summary = load_data()
    insights = generate_insights(data, summary)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)
    print(f"Generated {len(insights)} insights -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
