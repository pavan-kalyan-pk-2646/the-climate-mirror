"""
Agent 1 — Analyzer
Deep analysis of all 4 climate factors with severity classification.
"""


def analyze(e: float, en: float, t: float, i: float, temp: float, country: str) -> dict:
    factors = [
        {"name": "Carbon Emissions", "key": "emission",  "value": e,  "weight": 0.25},
        {"name": "Energy Use",       "key": "energy",    "value": en, "weight": 0.35},
        {"name": "Transport",        "key": "transport", "value": t,  "weight": 0.10},
        {"name": "Industry",         "key": "industry",  "value": i,  "weight": 0.30},
    ]
    dominant = max(factors, key=lambda x: x["value"] * x["weight"])
    ranked   = sorted(factors, key=lambda x: x["value"] * x["weight"], reverse=True)
    total_weighted = sum(f["value"] * f["weight"] for f in factors)

    if   total_weighted < 20: severity = "Minimal"
    elif total_weighted < 40: severity = "Low"
    elif total_weighted < 60: severity = "Moderate"
    elif total_weighted < 75: severity = "High"
    else:                     severity = "Critical"

    insights = []
    # Emissions insights
    if e > 80:   insights.append(f"Carbon emissions ({e}/100) at EXTREME level — industrial decarbonisation is the single most urgent action.")
    elif e > 60: insights.append(f"Carbon emissions ({e}/100) are a major driver — carbon pricing and CCS technology deployment needed.")
    elif e > 40: insights.append(f"Emissions ({e}/100) are elevated — efficiency improvements and clean fuel transitions can reduce this.")
    else:        insights.append(f"Emissions ({e}/100) are within acceptable range — maintain current controls.")

    # Energy insights
    if en > 80:   insights.append(f"Energy consumption ({en}/100) is at crisis level — immediate grid transition to 100% renewables required.")
    elif en > 60: insights.append(f"Energy index ({en}/100) is high — coal phase-out and smart grid investment are critical priorities.")
    elif en > 40: insights.append(f"Energy use ({en}/100) needs improvement — renewable subsidies and efficiency mandates recommended.")
    else:         insights.append(f"Energy consumption ({en}/100) is well-managed — scale up green energy for further gains.")

    # Transport insights
    if t > 80:   insights.append(f"Transport sector ({t}/100) is critically high — emergency EV transition and fossil fuel vehicle ban required.")
    elif t > 60: insights.append(f"Transport ({t}/100) is a major contributor — expand public transit and EV infrastructure now.")
    elif t > 40: insights.append(f"Transport ({t}/100) shows room for improvement — EV incentives and urban mobility planning needed.")
    else:        insights.append(f"Transport ({t}/100) is relatively clean — focus on last-mile EV and cycle infrastructure.")

    # Industry insights
    if i > 80:   insights.append(f"Industry ({i}/100) is at maximum risk — mandatory ISO 50001 and circular economy transition required immediately.")
    elif i > 60: insights.append(f"Industrial activity ({i}/100) needs major reform — green manufacturing and energy audits are essential.")
    elif i > 40: insights.append(f"Industry ({i}/100) has significant headroom — lean manufacturing and waste reduction can lower this index.")
    else:        insights.append(f"Industry ({i}/100) is performing well — pursue green certification and supply chain optimisation.")

    reduction_needed = max(0, round(temp - 1.5, 2))
    return {
        "dominant":         dominant,
        "ranked":           ranked,
        "severity":         severity,
        "total_weighted":   round(total_weighted, 2),
        "insights":         insights,
        "reduction_needed": reduction_needed,
        "safe":             temp <= 1.5,
    }
