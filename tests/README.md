# openf1 Python Tests

## Running the tests

Run the tests using pytest:

```bash
pytest
```

Be sure to install any required dependencies before running the tests. For
example, when using poetry run the following command to install base and
development dependencies:

```bash
poetry install --with=dev
```

## Type of Tests

Many different types of tests allow us to subdivide the tests for each moduling
into the type of test that is being run.

### Unit Tests

Unit tests cover single functions or methods in isolation. For example, most of
the utility functions in the `openf1` package have unit tests.

### Integration Tests

Integration tests cover multiple functions or methods working together.

### Endpoint Tests

Endpoint tests cover the endpoints of the API. These tests are run against known
data to ensure that the API is working as expected and returns complete data.
Unfortunately, these tests cannot garuntee that the data is correct nor
complete, only that the known portions of the data are returned as expected.

## Fixtures

Fixtures are used to setup the environment for the tests. For instance, setting
up the credentials for external services if using them in the tests. Most of the
time, you'll run the mock-fixtures though which create mock services for each
external service.

When writing tests, include one of these fixtures as an parameter to the test
function. For example if you need the `mock_mongodb` fixture, include it in the
function signature:

```python
def test_example(mock_mongodb):
    ...
```

### MongoDB

The `mock_mongodb` fixture is used to setup a MongoDB instance for testing. This
fixture pulls data from the `data.json` file in the `tests/fixtures` directory.
To include new data, simply add it to this file and your tests will have access
to it when making MongoDB queries.

## Future Tests

Some types of future tests that may be implemented down the road.

 1. Performance tests to measure impact on performance of servers (both ingestor
    and API).
 2. Security tests to ensure that the API is secure and that the data is
    protected. Right now this isn't super applicable as the data is public.
 3. Regression tests to ensure that new changes do not break existing
    functionality.


