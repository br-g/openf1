# FAQ

### How to access real-time data?

Real-time data can be accessed via REST API, MQTT, or WebSockets, and requires a paid account.
Apply by filling out <a href="https://tally.so/r/w2yWDb" target="_blank">this form</a>.

### What's the delay between live events and API updates?

The API typically updates about 3 seconds after a live event.
However, this time could be extended due to factors like serverless cold starts, which occur when the service is scaling up.  
As a point of reference, F1 TV typically has a 6-second delay.

### Is there a query timeout?

Queries are limited to a 10 seconds timeout. If your request takes too long, consider breaking it down into smaller queries and then combining the results.
