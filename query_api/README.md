# Query API
The Query API serves as the intermediary between the user and the database.
It processes user queries, fetches the relevant data from the MongoDB database, and returns it in the requested format.    
The service is hosted on Google Cloud Run and is built using Python 3.9 and FastAPI.

## Running the service locally
Install dependencies:
```shell
pip install -r requirements.txt
```

Launch the server:
```shell
uvicorn main:app
```

You can test the service by navigating to this URL in your web browser: <a href="http://127.0.0.1:8000/v1/sessions?year=2023" target="_blank">http://127.0.0.1:8000/v1/sessions?year=2023</a>.

## Creating a new API method
We're always open to contributions that enhance the project.

### Initial discussion
Before you begin developing a new API method, it's advisable to initiate a discussion on <a href="https://github.com/br-g/openf1/discussions" target="_blank">Github Discussions</a>.

### Method creation
To add a new API method, simply create a new Python file within the <a href="https://github.com/br-g/openf1/tree/main/query_api/methods/v1" target="_blank">methods/v1/</a> directory. You don't need to manually register the new method; it will be automatically discovered during runtime.

### Automated testing and documentation
The API methods go through automated testing, and their documentation is automatically generated via a <a href="https://github.com/br-g/openf1/actions/workflows/queryapi_documentation.yml" target="_blank">Github Action</a>.

For ease of development, it is recommended to use existing methods as templates.

### Database connection
You can query the MongoDB directly for data exploration. The connection string can be found <a href="https://github.com/br-g/openf1/blob/d91a5a1b8fdf2e48fbbf579fe3b5bdfba1179817/query_api/db.py#L9" target="_blank">here</a>.
