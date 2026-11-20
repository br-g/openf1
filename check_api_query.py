import asyncio
from openf1.util.db import get_documents
from openf1.services.query_api.query_params import query_params_to_mongo_filters, parse_query_params
from openf1.services.query_api.query_params import QueryParam

async def test():
    # 1. Test raw database query with manual filters
    filters = {
        'session_key': [{'$eq': 11322}],
        'driver_number': [{'$eq': 1}]
    }
    print("Testing get_documents with manual filters...")
    res = await get_documents('car_data', filters)
    print("  Result length:", len(res))
    if res:
        print("  Sample:", res[0])
        
    # 2. Test parse_query_params and query_params_to_mongo_filters
    print("\nTesting filter parser...")
    raw_params = {
        'session_key': ['11322'],
        'driver_number': ['1']
    }
    parsed = parse_query_params(raw_params)
    print("  Parsed query params:", parsed)
    mongo_filters = query_params_to_mongo_filters(parsed)
    print("  Mongo filters:", mongo_filters)
    
    res2 = await get_documents('car_data', mongo_filters)
    print("  Result length from parsed filters:", len(res2))

if __name__ == '__main__':
    asyncio.run(test())
