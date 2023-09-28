# Data filtering

Refine your query by including parameters directly in the URL.    
Results can be filtered by any attribute, except arrays.

**Example**    
To fetch pit-out laps for driver number 55 (Carlos Sainz) that last at least 2 minutes, use:
<a href="https://api.openf1.org/v1/laps?driver_number=55&amp;is_pit_out_lap=true&amp;lap_duration%3E%3D120" target="_blank">https://api.openf1.org/v1/laps?driver_number=55&amp;is_pit_out_lap=true&amp;lap_duration&gt;=120</a>

## Time-Based Filtering
You can narrow down your results using time ranges.

**Example**    
To get all sessions in September 2023, use:
<a href="https://api.openf1.org/v1/sessions?date_start%3E%3D2023-09-01&amp;date_end%3C%3D2023-09-30" target="_blank">https://api.openf1.org/v1/sessions?date_start>=2023-09-01&date_end<=2023-09-30</a>

The API supports a wide range of date formats (those compatible with Python's <code>dateutil.parser.parse</code> method). Examples include:    
<ul>
  <li>"2021-09-10"</li>
  <li>"2021-09-10T14:30:20"</li>
  <li>"2021-09-10T14:30:20+00:00"</li>
  <li>"09/10/2021"</li>
  <li>"09-10-2021"</li>
  <li>"Fri Sep 10 14:30:20 2021"</li>
  <li>"10 September 2021"</li>
  <li>"Sep 10, 2021"</li>
  <li>"2021-09-10 14:30:20 UTC"</li>
  <li>"2021-09-10 14:30:20+00:00"</li>
  <li>"2021-09-10 14:30:20 EST"</li>
  <li>...and many more.</li>
</ul>

<aside class="notice">
If you include the <code>+</code> character to specify a timezone in the URL, make sure to URL-encode it as <code>%2B</code> to ensure proper parsing.
</aside>
