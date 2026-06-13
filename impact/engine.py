def compute_impact(location, repair_option):
    total_violations = len(location['violations'])
    resolved_ids = repair_option.get('resolves', [])
    resolved_count = len(resolved_ids)
    remaining_count = total_violations - resolved_count

    compliance_changes = []
    for viol in location['violations']:
        dim = viol['dimension']
        is_resolved = dim in resolved_ids

        after_val = "Fixed / Compliant"
        if dim == 'ramp_slope': after_val = "≤8.33%"
        elif dim == 'cross_slope': after_val = "≤2.0%"
        elif dim == 'surface_integrity': after_val = "Smooth (Score > 85)"
        elif dim == 'clear_width': after_val = "≥36 inches"

        change = {
            "dimension": dim,
            "label": dim.replace('_', ' ').title(),
            "before_status": "fail",
            "after_status": "pass" if is_resolved else "fail",
            "before_value": viol['detail'],
            "after_value": after_val if is_resolved else "Unchanged",
            "ada_section": viol['ada_section']
        }
        compliance_changes.append(change)

    tier = repair_option.get('permit_tier', 'minor_repair')
    if tier == 'minor_repair':
        permit_label = "No permit required (under $10k)"
    elif tier == 'standard':
        permit_label = "Building permit required"
    else:
        permit_label = "MassDOT review / Major Site Plan triggered"

    grant_eligible = (resolved_count == total_violations)
    grant_note = "Full remediation qualifies for MassDOT Chapter 90 funding." if grant_eligible else "Partial repairs rarely qualify for state funding."
    liability_change = f"Removes {resolved_count} of {total_violations} active ADA Title II exposure points."

    return {
        "cost_low": repair_option['cost_low'], "cost_high": repair_option['cost_high'],
        "violations_total": total_violations, "violations_resolved": resolved_count,
        "violations_remaining": remaining_count, "compliance_changes": compliance_changes,
        "permit_tier": tier, "permit_label": permit_label,
        "liability_change": liability_change, "grant_eligible": grant_eligible,
        "grant_note": grant_note
    }
