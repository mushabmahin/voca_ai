def calculate_risk_assessment(base_score, triggers, conversation, emotion_intensity):

    score = base_score
    factors = []

    # Emotional intensity weighting
    if emotion_intensity == "High":
        score += 20
        factors.append("High emotional intensity")
    elif emotion_intensity == "Medium":
        score += 10
        factors.append("Moderate emotional intensity")

    # Trigger-based escalation
    for trigger in triggers:
        if trigger.lower() in conversation.lower():
            score += 15
            factors.append(f"{trigger} detected")

    score = min(score, 100)

    if score >= 75:
        level = "High"
    elif score >= 40:
        level = "Medium"
    else:
        level = "Low"

    return {
        "score": score,
        "level": level,
        "factors": factors
    }