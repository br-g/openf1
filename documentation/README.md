# Documentation

This project's documentation is built using <a href="https://github.com/slatedocs/slate" target="_blank">Slate</a> and automatically deployed to <a href="https://openf1.org" target="_blank">openf1.org</a> via <a href="https://github.com/br-g/openf1/actions/workflows/queryapi_documentation.yml" target="_blank">this Github Action</a> upon each commit to the `main` branch.    

The <a href="https://openf1.org/#api-methods" target="_blank">"API methods" section</a> is dynamically generated from the codebase through the <a href="https://github.com/br-g/openf1/blob/documentation/documentation/generate.py" target="_blank">generate.py</a> script.


## Building the documentation locally

Install the dependencies of the Query API module:
```
pip install -r ../query_api/requirements.txt
```

Generate the "API methods" section:
```
python generate.py
```

Build the documentation with Slate (cf. <a href="https://github.com/slatedocs/slate/wiki/Using-Slate-Natively" target="_blank">https://github.com/slatedocs/slate/wiki/Using-Slate-Natively</a>).
