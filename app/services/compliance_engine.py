def rule_based_compliance_check(conversation: str, policies: list):
    violations = []

    if "guaranteed return" in conversation.lower():
        violations.append("Agent mentioned guaranteed returns (policy violation)")

    if "skip kyc" in conversation.lower():
        violations.append("KYC process bypassed")

    return violations