def calculate_risk_score(base_score: int, triggers: list, conversation: str):
    adjusted_score = base_score

    for trigger in triggers:
        if trigger.lower() in conversation.lower():
            adjusted_score += 10

    return min(adjusted_score, 100)