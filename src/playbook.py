def generate_playbook(regime_label: str, clock_score: float,
                      actions: list, base_symbol: str) -> str:
    lines = []
    if clock_score > 80:
        lines.append(f"🔥 CRITICAL Clock {clock_score:.0f}/100 – Reduce size, cut leverage.")
    elif clock_score > 60:
        lines.append(f"⚠️ STRESSED Clock {clock_score:.0f}/100 – Trim concentration.")
    elif regime_label == "DECOUPLED":
        # Bug fix: was "diversifcation"
        lines.append(f"✅ DECOUPLED – Healthy diversification. RV strategies favored.")
    else:
        lines.append(f"ℹ️ {regime_label} regime. Monitor per-symbol signals.")

    if actions:
        top = actions[0]
        lines.append(
            f"Top trade: {top['type']} {top['target']} – "
            f"{top['direction']} (Score {top['score']:.0f})"
        )
    else:
        lines.append("No high-conviction trades now.")

    return "\n".join(lines)
