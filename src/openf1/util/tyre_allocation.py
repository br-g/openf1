# Mapping of Pirelli C-Codes for Formula 1 Grand Prix weekends.
# This resolves Issue #412: Compound with actual Pirelli-C-Code
# The mapping array represents the [HARD, MEDIUM, SOFT] compounds.
# Maintainers can expand this dictionary over time for historical meetings.

MEETING_KEY_ALLOCATIONS = {
    # Example Allocations (Maintainers: Please update with actual meeting keys and allocations)
    # 1286: ["C3", "C4", "C5"], # Monaco 2026 example
}

def append_c_codes_to_stints(stints_results: list[dict]) -> list[dict]:
    """
    Takes the raw /stints API output and appends the `compound_c_code` property
    if the meeting_key's allocation is known in MEETING_KEY_ALLOCATIONS.
    Returns the mutated list of dictionaries.
    """
    for stint in stints_results:
        meeting_key = stint.get("meeting_key")
        compound = stint.get("compound")
        
        # Default to None so the API consumer knows we don't have the C-Code
        stint["compound_c_code"] = None
        
        if meeting_key in MEETING_KEY_ALLOCATIONS and compound:
            allocation = MEETING_KEY_ALLOCATIONS[meeting_key] # [HARD, MEDIUM, SOFT]
            
            compound_upper = str(compound).upper()
            if compound_upper == "HARD":
                stint["compound_c_code"] = allocation[0]
            elif compound_upper == "MEDIUM":
                stint["compound_c_code"] = allocation[1]
            elif compound_upper == "SOFT":
                stint["compound_c_code"] = allocation[2]
                
    return stints_results
