import pytest
from datetime import datetime
from typing import Any

from dateutil.tz import tzutc

from openf1.util.type_casting import (_try_parse_date, _try_parse_number,
                                       _try_parse_boolean, _cast, cast)

def test_cast():
    """Test the cast function."""
    # strings to test with
    string1 = "123"         # number
    string2 = "a string"    # string
    string3 = "true"        # boolean
    string4 = "2020-03-13T12:00:00Z" # date
    # results for each string
    string1_result = 123
    string2_result = "a string"
    string3_result = True
    string4_result = datetime(2020, 3, 13, 12, 0, 0, tzinfo=tzutc())
    # objects to test with
    obj1 = datetime(2020, 12, 22, 8, 0, 0) # datetime object
    # results for each object
    obj1_result = obj1
    # test with a string
    assert cast(string1) == string1_result
    assert cast(string2) == string2_result
    assert cast(string3) == string3_result
    assert cast(string4) == string4_result
    # test with list of strings
    assert cast([string1, string2, string3, string4]) == [string1_result,
                                                          string2_result,
                                                          string3_result,
                                                          string4_result]
    # test with dict of strings
    assert cast({"string1": string1, "string2": string2, "string3": string3,
                 "string4": string4}) == {"string1": string1_result, 
                                           "string2": string2_result,
                                           "string3": string3_result,
                                           "string4": string4_result}
    # test with list of dicts
    assert cast([{"string1": string1, "string2": string2}, {"string3": string3,
                  "string4": string4}]) == [{"string1": string1_result,
                                              "string2": string2_result},
                                            {"string3": string3_result,
                                              "string4": string4_result}]
    # test with dict of lists
    assert cast({"list1": [string1, string2], "list2": [string3, string4]}) == \
           {"list1": [string1_result, string2_result],
            "list2": [string3_result, string4_result]}
    # test with dict of dicts
    assert cast({"dict1": {"string1": string1, "string2": string2},
                 "dict2": {"string3": string3, "string4": string4}}) == \
           {"dict1": {"string1": string1_result, "string2": string2_result},
            "dict2": {"string3": string3_result, "string4": string4_result}}
    # test with list of lists
    assert cast([[string1, string2], [string3, string4]]) == \
           [[string1_result, string2_result], [string3_result, string4_result]]


