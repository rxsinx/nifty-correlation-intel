def format_money(value):
    if value is None:
        return "-"
    if abs(value) >= 1e7:
        return f"₹{value/1e7:.1f} Cr"
    elif abs(value) >= 1e5:
        return f"₹{value/1e5:.1f} L"
    elif abs(value) >= 1e3:
        return f"₹{value/1e3:.1f} K"
    else:
        return f"₹{value:.0f}"

def flatten_dict(d, parent_key='', sep='_'):
    """Flatten nested dict for table display."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
