# System architecture

Our architecture is serverless, optimized for resilience, cost-efficiency and scalability.

<img src="https://storage.googleapis.com/openf1-public/images/archi.png" alt="architecture schema" style="
    max-width: 220px;
    display: block;
    margin-left: auto;
    margin-right: auto;
    margin-top: 35px;
    margin-bottom: 45px;
">

### Ingestor
The data ingestor runs every 5 minutes to check for new real-time data. During live sessions, at least two instances are active at any time to ensure reliable data recording. The ingestor also performs basic data normalization for efficient database indexing.

### Database
We use a MongoDB database with indexes for each collection, enabling faster query responses. The data is stored in JSON format. Direct database queries are also possible; the connection string can be found <a href="https://github.com/br-g/openf1/blob/d91a5a1b8fdf2e48fbbf579fe3b5bdfba1179817/query_api/db.py#L9" target="_blank">here</a>.

### Query API
The Query API serves as the intermediary between the user and the database. It processes user queries, fetches the relevant data from the database, and returns it in the requested format.
