# List of keys to be used for sorting, in order of priority
_SORT_KEYS = [
    "date",
    "date_start",
    "meeting_key",
    "session_key",
    "lap_start",
    "lap_number",
    "lap_end",
    "date_end",
    "stint_number",
    "driver_number",
]


def sort_results(results: list[dict]) -> list[dict]:
    """
    Sorts a list of results based on predefined keys. It only uses keys that are present
    in all dictionaries and have non-None values.
    """
    if len(results) <= 1:
        return results

    selected_sort_keys = [
        key
        for key in _SORT_KEYS
        if all(key in r and r[key] is not None for r in results)
    ]

    return (
        sorted(results, key=lambda r: tuple(r[key] for key in selected_sort_keys))
        if selected_sort_keys
        else results
    )
