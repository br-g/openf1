# FAQ

### Can I access past data during an ongoing session?
Yes, real-time storage allows for instant access to past and current session data.

### What's the delay between live events and API updates?
The API typically updates about 3 seconds after a live event.
However, this time could be extended due to factors like serverless cold starts, which occur when the service is scaling up.    
As a point of reference, F1 TV typically has a 6-second delay.

### Is there a query timeout?
Queries are limited to a 1-minute timeout. If your request takes too long, consider breaking it down into smaller queries and then combining the results.
