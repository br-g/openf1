"""A script to dynamically discover API methods and generate the `API methods` section of the documentation.    
   Automatically executed by Github Actions after each commit on branch `main`.
"""

import sys
import html
import requests
import json
from pathlib import Path
from attributes_descriptions import ATTRIBUTES_DESCRIPTIONS

sys.path.append('../query_api')
from util import get_api_methods

METHODS_DIR = Path('../query_api/methods')
OUTPUT_FILE = Path('source/includes/_api_methods.md')


def _get_method_documentation(url: str, method: 'BaseMethod') -> str:
    """Generates documentation for a given API method"""
    name = url.split('/')[-1]
    url = f'https://api.openf1.org/{url}'
    query_params = '&'.join(method.example_filters) if method.example_filters else ''

    attributes = (
        'Name | Description\n'
        + '--------- | -----------\n'
        + '\n'.join([f'{name} | {ATTRIBUTES_DESCRIPTIONS.get(name, "")}' for name in sorted(list(method.attributes))])
    )

    output = json.dumps(method.example_response, indent=2, sort_keys=True)
    url_full = f'{url}{"?" if query_params else ""}{query_params}'

    return f'''
## {name.capitalize().replace('_', ' ')}

{method.description}

```shell
curl "{url_full}"
```

```python
from urllib.request import urlopen
import json

response = urlopen('{url_full}')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('{url_full}')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch('{url_full}')
  .then(response => response.json())
  .then(jsonContent => console.log(jsonContent));
```

> Output:

```json
{output}
```

### HTTP Request
`GET {html.escape(url)}`

### Sample URL
<a href="{html.escape(url_full)}" target="_blank">{html.escape(url_full)}</a>

### Attributes
{attributes}

{"<br /><br />" if method.additional_info else ""}
{method.additional_info}
'''


def generate_documentation() -> None:
    """Generates the `API methods` section of the documentation and writes it to
       the source folder."""
    markdown = ['# API methods']
    for url, cls in sorted(list(get_api_methods(METHODS_DIR))):
        markdown.append(
            _get_method_documentation(url=url, method=cls)
        )

    with open(OUTPUT_FILE, 'w') as f:
        f.write('\n'.join(markdown))


if __name__ == '__main__':
    generate_documentation()
