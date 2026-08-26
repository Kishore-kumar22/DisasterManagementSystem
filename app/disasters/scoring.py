SEVERITY_VALUES = {"Low": 1, "Medium": 2, "High": 4, "Critical": 5}


def clamp(value, minimum=0.0, maximum=5.0):
    return max(minimum, min(maximum, float(value)))


def severity_component(severity):
    return float(SEVERITY_VALUES.get(severity, 1))


def population_component(affected_population):
    population = max(0, int(affected_population or 0))
    # Explainable thresholds keep the component on a 0–5 scale.
    if population == 0:
        return 0.0
    if population <= 100:
        return 1.0
    if population <= 500:
        return 2.0
    if population <= 1000:
        return 3.0
    if population <= 5000:
        return 4.0
    return 5.0


def shortage_component(shortage_ratio):
    return clamp((float(shortage_ratio or 0) * 5.0))


def priority_category(score):
    score = float(score)
    if score < 2.0:
        return "LOW"
    if score < 3.5:
        return "MEDIUM"
    if score < 4.25:
        return "HIGH"
    return "CRITICAL"


def calculate_priority(severity, affected_population, shortage_ratio=0.0):
    components = {
        "severity_component": clamp(severity_component(severity)),
        "population_component": population_component(affected_population),
        "shortage_component": shortage_component(shortage_ratio),
    }
    score = (
        0.50 * components["severity_component"]
        + 0.30 * components["population_component"]
        + 0.20 * components["shortage_component"]
    )
    components["priority_score"] = round(clamp(score), 2)
    components["priority_category"] = priority_category(components["priority_score"])
    return components
