"""
Agent 4 — Story
Generates a personalised 2050 climate narrative using full agent context.
"""


def narrate(
    username: str, country: str, temp: float,
    e: float, en: float, t: float, i: float,
    analysis: dict, disasters: dict, comparator: dict,
) -> dict:
    dominant  = analysis["dominant"]["name"]
    severity  = analysis["severity"]
    highest_d = disasters["highest"]
    trend     = comparator.get("trend", "stable")

    # Opening scene
    if temp >= 3.5:
        opening = (
            f"The year is 2050. {country} has changed beyond recognition. "
            f"The climate projections of the 2020s — once warnings — are now daily reality. "
            f"Temperatures have climbed +{temp:.1f}°C above pre-industrial levels."
        )
    elif temp >= 2.5:
        opening = (
            f"The year is 2050. {country} stands at a crossroads. "
            f"A +{temp:.1f}°C world has reshaped the landscape — coastlines redrawn, seasons shifted. "
            f"The decisions of the 2020s echo in every weather report."
        )
    elif temp >= 1.5:
        opening = (
            f"The year is 2050. {country} has navigated a turbulent transition. "
            f"At +{temp:.1f}°C, the climate is changed — but the worst was narrowly avoided. "
            f"The investments made in the 2020s are paying dividends."
        )
    else:
        opening = (
            f"The year is 2050. {country} is a model for the world. "
            f"At just +{temp:.1f}°C, the nation achieved what many said was impossible — "
            f"a prosperous, carbon-neutral economy within a generation."
        )

    # Dominant factor story
    factor_stories = {
        "Carbon Emissions": (
            f"The legacy of carbon-heavy industry from the 2020s left a long shadow. "
            f"With emissions once peaking at {e}/100 on the climate index, the air quality crisis of the 2030s "
            f"forced rapid industrial transformation — a painful but necessary reckoning."
        ),
        "Energy Use": (
            f"The energy grid tells the story. From an energy index of {en}/100, "
            f"{country}'s engineers spent a decade rebuilding — wind farms where coal plants once stood, "
            f"solar panels on every rooftop, batteries in every neighbourhood."
        ),
        "Transport": (
            f"The roads are quieter now. The transport index of {t}/100 in the 2020s "
            f"gave way to the Great EV Transition — electric buses, cycle superhighways, and "
            f"high-speed rail connecting cities that once choked on car exhaust."
        ),
        "Industry": (
            f"The factories that once drove {country}'s economy with an industry index of {i}/100 "
            f"have been reborn. Green steel, circular plastics, and zero-waste manufacturing "
            f"are now the norm — competitive advantage, not charity."
        ),
    }
    factor_para = factor_stories.get(dominant, "The industrial landscape has transformed dramatically.")

    # Disaster consequence
    disaster_paras = {
        "flood":     f"The coastal communities remember the floods of the 2030s. Entire neighbourhoods were relocated inland as {country}'s sea defences proved insufficient. Today, wetland restoration and smart flood barriers protect what remains.",
        "drought":   f"The dry years of the 2030s are etched in memory. Reservoirs ran low, harvests failed, and water rationing became normal. Now, desalination plants and smart irrigation sustain agriculture in a drier world.",
        "wildfire":  f"The smoke seasons became an annual ordeal. Wildfires scarred {country}'s forests in the 2030s, but also sparked a reforestation revolution — fire-resistant native species now cover land that was once barren.",
        "hurricane": f"The storms grew fiercer. {country} bore the cost of climate-supercharged hurricanes in the 2030s — billions in damage, communities displaced. Today, building codes and early warning systems have reduced human casualties dramatically.",
        "heatwave":  f"The heat became unbearable in summer. School closures, health emergencies, and worker strikes forced a fundamental rethinking of urban design — green roofs, shade canopies, and 24-hour cooling centres redefined city life.",
        "sealevel":  f"The tide lines moved. Low-lying areas of {country} saw permanent inundation in the 2040s. But the managed retreat — painful as it was — gave birth to restored coastal ecosystems and resilient inland communities.",
    }
    disaster_para = disaster_paras.get(highest_d, "Climate impacts reshaped the landscape across multiple dimensions.")

    # Progress note
    if trend == "improving":
        progress = f"The data shows hope. Your personal climate footprint has been trending downward — proof that individual and systemic action, taken together, can bend the curve."
    elif trend == "worsening":
        progress = f"The trajectory demands attention. The pattern of rising climate inputs, if unchecked, leads directly to the world described above. The 2020s remain a decade of choice."
    else:
        progress = f"The path forward is neither won nor lost. Stability now requires active effort — maintaining green gains while pushing for the deeper structural changes that make the 2050 story a hopeful one."

    # Closing
    if temp < 2.0:
        closing = f"{username}'s generation made the right choices. The 2050 they inherited is imperfect — but liveable, green, and full of possibility."
    else:
        closing = f"The 2050 story is still being written. Every input you reduce, every policy you support, every conversation you have — it all shapes the ending."

    return {
        "opening":      opening,
        "factor_para":  factor_para,
        "disaster_para": disaster_para,
        "progress":     progress,
        "closing":      closing,
        "dominant":     dominant,
        "severity":     severity,
        "temp":         temp,
    }
