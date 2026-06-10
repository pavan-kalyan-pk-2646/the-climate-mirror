"""
Agent 6 — Forecast
Multi-point trend analysis with linear regression projection.
"""


def project(records: list, current_temp: float, current_score: int) -> dict:
    if len(records) < 2:
        if current_temp > 3.0:
            label = "⚠️ First run shows critical trajectory. Immediate intervention needed."
        elif current_temp > 2.0:
            label = "📊 First run recorded. Run more simulations to unlock trend analysis."
        else:
            label = "✅ Good start! Run more simulations to track your progress over time."
        return {"label": label, "trend": "insufficient data", "projection": [], "weeks": []}

    temps  = [r["temp"]  for r in records[-8:]]
    scores = [r["score"] for r in records[-8:] if r.get("score")]
    avg    = round(sum(temps) / len(temps), 2)
    trend_val = round(temps[-1] - temps[0], 2) if len(temps) > 1 else 0

    n = len(temps)
    x_mean = (n - 1) / 2
    y_mean = avg
    num = sum((idx - x_mean) * (temps[idx] - y_mean) for idx in range(n))
    den = sum((idx - x_mean) ** 2 for idx in range(n)) or 1
    slope = num / den

    projection = [round(temps[-1] + slope * (idx + 1), 2) for idx in range(4)]
    weeks      = ["Next", "+2 runs", "+3 runs", "+4 runs"]

    if trend_val > 0.5:
        trend = "worsening"
        label = f"📈 WORSENING — Temperatures rising {trend_val:.2f}°C across your last {n} runs. Projected next: +{projection[0]}°C. Urgent changes needed."
    elif trend_val < -0.5:
        trend = "improving"
        label = f"📉 IMPROVING — Great progress! Down {abs(trend_val):.2f}°C across {n} runs. Projected next: +{projection[0]}°C. Keep optimising."
    elif trend_val > 0.2:
        trend = "slightly worsening"
        label = f"➡️ SLIGHT INCREASE — +{trend_val:.2f}°C drift. Avg: +{avg}°C. Projected: +{projection[0]}°C. Minor adjustments can reverse this."
    elif trend_val < -0.2:
        trend = "slightly improving"
        label = f"➡️ SLIGHT IMPROVEMENT — Down {abs(trend_val):.2f}°C. Projected: +{projection[0]}°C. You're on the right path."
    else:
        trend = "stable"
        label = f"➡️ STABLE — Holding at ~+{avg}°C average. Projection: +{projection[0]}°C. Push one factor lower to see improvement."

    score_trend = ""
    if len(scores) >= 2:
        s_trend = scores[0] - scores[-1]
        if s_trend < -5:  score_trend = f" Eco score improving: +{abs(int(s_trend))} pts."
        elif s_trend > 5: score_trend = f" Eco score declining: {int(s_trend)} pts — review your inputs."

    return {
        "label":      label + score_trend,
        "trend":      trend,
        "projection": projection,
        "weeks":      weeks,
        "avg":        avg,
        "slope":      round(slope, 3),
        "n":          n,
    }
