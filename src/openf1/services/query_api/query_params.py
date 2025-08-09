import re
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum

from dateutil.parser import parse as parse_date
from pydantic import BaseModel

from openf1.util.schedule import get_latest_meeting_key, get_latest_session_key
from openf1.util.type_casting import cast


# Operators allowed in the URL for filtering results
class ComparisonOperator(str, Enum):
    EQ = "="
    LTE = "<="
    GTE = ">="
    LT = "<"
    GT = ">"


COMPARISON_OPERATORS_TO_MONGO = {
    ComparisonOperator.GTE: "$gte",
    ComparisonOperator.LTE: "$lte",
    ComparisonOperator.EQ: "$eq",
    ComparisonOperator.GT: "$gt",
    ComparisonOperator.LT: "$lt",
}


class QueryParam(BaseModel):
    """Represents a single query parameter (for example: 'lap_start>=3')"""

    field: str
    op: ComparisonOperator
    value: str | bool | int | float | datetime


def _split_query_params(query_params_raw: dict[str, list[str]]) -> list[str]:
    """Splits query parameters into a list of filter strings.
    Handles special cases for date parameters with timezones.
    """
    filters = []
    for key, values in query_params_raw.items():
        for value in values:
            filter_str = f"{key}={value}" if value else key

            # Handle timezones which are not parsed properly
            if "date" in filter_str and re.search(r" \d{2}:\d{2}$", filter_str):
                filter_str = filter_str.replace(" ", "+", 1)
            
            filters.append(filter_str)

    return filters


def _has_time_info(date_str: str) -> bool:
    """Returns whether the date string has time info.
    eg.
        - "2021-09-10" -> False
        - "2021-09-10T14:30:20" -> True
    """
    # Parse the string with the first default datetime
    default_datetime1 = datetime(1, 1, 1, 5, 0)  # 5:00
    dt1 = parse_date(date_str, default=default_datetime1)

    # Parse the string with the second default datetime
    default_datetime2 = datetime(1, 1, 1, 10, 0)  # 10:00
    dt2 = parse_date(date_str, default=default_datetime2)

    # Check if hours are the same
    return dt1.hour == dt2.hour


def _adjust_time_param(param: QueryParam) -> list[QueryParam]:
    """
    Adjusts time param to ensure consistent behavior when time information is not
    specified (cf. function '_has_time_info').

    This function modifies time-based query params to handle cases where only the date
    is provided, without specific time information. It adjusts the param operations and
    values to include the full day when necessary.

    Examples:
        date>2023-01-01 --> date>=2023-01-02
        date<2023-01-01 --> date<2023-01-01 (no change)
        date=2023-01-01 --> date>=2023-01-01 AND date<2023-01-02
        date>=2023-01-01 --> date>=2023-01-01 (no change)
        date<=2023-01-01 --> date<2023-01-02
        date>2023-01-01 12:00:00 --> date>2023-01-01 12:00:00 (no change)
    """
    adjusted_params = []

    if param.op == ">":
        adjusted_params.append(
            QueryParam(
                field=param.field, op=">=", value=param.value + timedelta(days=1)
            )
        )
    elif param.op == "<":
        adjusted_params.append(param)
    elif param.op in {"=", ">=", "<="}:
        if param.op in {"=", ">="}:
            adjusted_params.append(
                QueryParam(field=param.field, op=">=", value=param.value)
            )
        if param.op in {"=", "<="}:
            adjusted_params.append(
                QueryParam(
                    field=param.field, op="<", value=param.value + timedelta(days=1)
                )
            )

    return adjusted_params


def _str_to_query_params(s: str) -> list[QueryParam]:
    for op in COMPARISON_OPERATORS_TO_MONGO:
        if op in s:
            field, _, value = s.partition(op)
            if field not in {"gmt_offset", "team_colour"}:
                value_casted = cast(value)
            else:
                value_casted = value
            query_param = QueryParam(field=field.lower(), op=op, value=value_casted)

            # Adjust time params to ensure consistent behavior when time information is not specified
            if isinstance(value_casted, datetime) and not _has_time_info(value):
                query_params_adjusted = _adjust_time_param(query_param)
                return query_params_adjusted
            else:
                return [query_param]

    raise ValueError(f"No valid operator found in `{s}`.")


def _replace_latest_by_actual_value(param: QueryParam) -> QueryParam:
    if param.field == "meeting_key" and param.value == "latest":
        param.value = get_latest_meeting_key()
    elif param.field == "session_key" and param.value == "latest":
        param.value = get_latest_session_key()
    return param


def parse_query_params(query_params_raw: dict[str, list[str]]) -> dict[str, list[QueryParam]]:
    query_params_str = _split_query_params(query_params_raw)
    query_params = sum((_str_to_query_params(s) for s in query_params_str), [])
    query_params = [_replace_latest_by_actual_value(p) for p in query_params]

    params_by_field = defaultdict(list)
    for param in query_params:
        params_by_field[param.field].append(param)

    return dict(params_by_field)


def query_params_to_mongo_filters(
    query_params: dict[str, list[QueryParam]],
) -> dict[str, list[dict]]:
    return {
        key: [{COMPARISON_OPERATORS_TO_MONGO[param.op]: param.value} for param in params]
        for key, params in query_params.items()
    }


def query_params_raw_items_to_raw_dict(query_params_raw_items: list[list[str]]) -> dict[str, list[str]]:
    """
    Given a list of query param key-value pairs,
    create a mapping of query param keys to all associated values.

    Examples:
        [["driver_number", "1"]] --> {"driver_number": ["1"]}
        [["driver_number", "4"], ["driver_number", "81"]] --> {"driver_number": ["4", "81"]}
        [["driver_number", "16"], ["position", "20"]] --> {"driver_number": ["16"], "position": ["20"]}
    """
    query_params_raw_dict = defaultdict(list)

    for item in query_params_raw_items:
        key = item[0]
        value = item[1]

        query_params_raw_dict[key].append(value)
    
    return dict(query_params_raw_dict)