"""
Agent 2 — Advisor
Generates a prioritised action plan using Analyzer context.
"""


def advise(e: float, en: float, t: float, i: float, temp: float, country: str, analysis: dict) -> dict:
    priority = analysis["dominant"]["name"]
    actions  = []

    actions.append({
        "priority": "P1 — CRITICAL",
        "icon": "🎯",
        "title": f"Address {priority} First",
        "detail": (
            f"Your dominant factor ({priority} at {analysis['dominant']['value']}/100) contributes the most "
            f"to the +{temp}°C rise. Reducing it by 20% alone could lower projected temperature by ~0.3°C."
        ),
        "timeframe": "Immediate (0–2 years)",
    })

    if e > 60:
        actions.append({"priority": "P1", "icon": "🏭", "title": "Industrial Carbon Capture & Switch",
            "detail": f"Emissions at {e}/100. Deploy carbon capture systems and mandate 30% hydrogen fuel substitution by 2030. Implement a $50/tonne carbon tax.",
            "timeframe": "1–3 years"})
    elif e > 30:
        actions.append({"priority": "P2", "icon": "🏭", "title": "Carbon Trading & Efficiency",
            "detail": f"Emissions at {e}/100. Join or create a regional carbon trading scheme — factory energy audits can yield 20–35% efficiency gains.",
            "timeframe": "2–4 years"})

    if en > 60:
        actions.append({"priority": "P1", "icon": "⚡", "title": "Emergency Renewable Grid Transition",
            "detail": f"Energy index at {en}/100. Shut down coal plants on an accelerated schedule. Deploy utility-scale solar/wind — target 80% renewable grid by 2035.",
            "timeframe": "1–5 years"})
    elif en > 30:
        actions.append({"priority": "P2", "icon": "⚡", "title": "Smart Grid & Efficiency Standards",
            "detail": f"Energy at {en}/100. Mandatory building energy ratings, LED street lighting, and smart meters can cut consumption 15–25%.",
            "timeframe": "2–4 years"})

    if t > 60:
        actions.append({"priority": "P1", "icon": "🚗", "title": "National EV Emergency Programme",
            "detail": f"Transport at {t}/100. Ban new petrol/diesel vehicle sales by 2030. Subsidise EV purchase — 50% cost reduction achievable with scale.",
            "timeframe": "Immediate"})
    elif t > 30:
        actions.append({"priority": "P2", "icon": "🚗", "title": "Green Transport Shift",
            "detail": f"Transport at {t}/100. Expand cycle lanes, public transit, and EV charging infrastructure. Incentivise remote work policies.",
            "timeframe": "2–5 years"})

    if i > 60:
        actions.append({"priority": "P1", "icon": "🏗️", "title": "Industrial Green Transformation",
            "detail": f"Industry at {i}/100. Mandate ISO 50001 energy management. Implement circular economy laws — 40% of industrial emissions are avoidable with current technology.",
            "timeframe": "1–4 years"})
    elif i > 30:
        actions.append({"priority": "P2", "icon": "🏗️", "title": "Green Manufacturing Standards",
            "detail": f"Industry at {i}/100. Voluntary green certification with tax incentives. Supply chain decarbonisation audits can reduce scope 3 emissions 30%.",
            "timeframe": "3–6 years"})

    actions.append({"priority": "P3", "icon": "🌲", "title": "Nature-Based Carbon Offsets",
        "detail": "Reforestation and rewilding as a supplement — not substitute — for direct emission cuts. 1 billion trees sequester ~2.5 Gt CO₂/year globally.",
        "timeframe": "Ongoing"})

    return {"priority": priority, "actions": actions, "severity": analysis["severity"]}
