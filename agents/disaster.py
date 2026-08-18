"""
Agent 3 — Disaster
Calculates 6 disaster risk scores + severity levels.
"""


def assess(temp: float, e: float, en: float, t: float, i: float, analysis: dict) -> dict:
    base = min(100, int((temp / 5.0) * 100))

    risks = {
        "flood":     min(100, int(base * 1.2 + (e * 0.15) + (i * 0.10))),
        "drought":   min(100, int(base * 1.1 + (en * 0.15) + (e * 0.10))),
        "wildfire":  min(100, int(base * 1.3 + (i * 0.15) + (t * 0.10))),
        "hurricane": min(100, int(base * 1.0 + (e * 0.20))),
        "heatwave":  min(100, int(base * 1.4 + (en * 0.20))),
        "sealevel":  min(100, int(base * 0.9 + (e * 0.25))),
    }

    highest = max(risks, key=risks.get)

    severity_map = {}
    for k, v in risks.items():
        if v < 30:   severity_map[k] = ("Low",      "green")
        elif v < 55: severity_map[k] = ("Moderate", "yellow")
        elif v < 75: severity_map[k] = ("High",     "orange")
        else:        severity_map[k] = ("Critical", "red")

    icons = {
        "flood":     "🌊",
        "drought":   "☀️",
        "wildfire":  "🔥",
        "hurricane": "🌀",
        "heatwave":  "🌡️",
        "sealevel":  "🌊",
    }

    return {
        "risks":        risks,
        "severity_map": severity_map,
        "highest":      highest,
        "icons":        icons,
        "base":         base,
    }
