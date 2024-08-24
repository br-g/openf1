# OpenF1 API

**OpenF1** is a free and open-source API that offers real-time and historical Formula 1 data. Whether you're a developer, data analyst, or F1 enthusiast, OpenF1 provides comprehensive access to lap timings, car telemetry, driver information, race control messages, and more.

Explore the data through JSON or CSV formats to build dashboards, analyze races, or integrate F1 data into your projects.

For full API documentation, visit [openf1.org](https://openf1.org).

## Key Features

- **Real-Time Data**: Stay updated with live lap times, speeds, and driver positioning.
- **Historical Data**: Analyze past races, compare performance over seasons, and dive deep into race strategy.
- **Car Telemetry**: Access in-depth car data, including throttle, brake, DRS, and gear information.
- **Driver Information**: Get details on F1 drivers, including team affiliations and performance metrics.

## Example Usage

Here’s a quick example of how to fetch lap data for a specific driver using the API:

```bash
curl "https://api.openf1.org/v1/laps?session_key=9161&driver_number=63&lap_number=8"
```

For more detailed examples and documentation, visit the [API Documentation](https://openf1.org).

## Supporting OpenF1

If you find this project useful, consider supporting its long-term sustainability:

<a href="https://www.buymeacoffee.com/openf1" target="_blank"><img src="https://storage.googleapis.com/openf1-public/images/bmec_button.png" alt="Buy Me A Coffee" style="height: 32px;"></a>
&thinsp;
<a href="https://github.com/sponsors/br-g"><img src="https://camo.githubusercontent.com/83d0bc6fee65b88ce9311c6b68844b0bd86453fc599ad3ed0f6a27ee669c50d7/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f73706f6e736f72732f62722d673f7374796c653d666f722d7468652d6261646765" alt="GitHub Sponsors" data-canonical-src="https://img.shields.io/github/sponsors/br-g?style=for-the-badge" style="max-width: 100%; height: 30px;"></a>

## Disclaimer

OpenF1 is an unofficial project and is not affiliated with Formula 1 companies. All F1-related trademarks are owned by Formula One Licensing B.V.
