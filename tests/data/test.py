import json
import os

def reformat_data(doc):
    if isinstance(doc, dict):
        reformatted_doc = {}
        for key, value in doc.items():
            # Handle specific MongoDB Extended JSON data types
            if isinstance(value, dict):
                if "$numberInt" in value:
                    reformatted_doc[key] = int(value["$numberInt"])
                elif "$numberLong" in value:
                    reformatted_doc[key] = int(value["$numberLong"])
                elif "$date" in value and "$numberLong" in value["$date"]:
                    reformatted_doc[key] = int(value["$date"]["$numberLong"])
                else:
                    reformatted_doc[key] = reformat_data(value)
            else:
                reformatted_doc[key] = value
        return reformatted_doc
    elif isinstance(doc, list):
        return [reformat_data(item) for item in doc]
    else:
        return doc

def main():
    # open each file and run operations
    files = [f for f in os.listdir('.') if f.endswith('.json')]
    for file in files:
        with open(file) as f:
            data = json.load(f)
        data = reformat_data(data[0:min(10, len(data))])
        with open(file+'2', 'w') as f:
            json.dump(data, f, indent=4)

if __name__ == '__main__':
    main()
