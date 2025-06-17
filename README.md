# Daily Energy Tracker

Custom Home Assistant integration that tracks **daily kWh** from any power sensor (in watts), resetting automatically at midnight.

## Features

- Converts W → kWh using trapezoidal integration
- Resets daily (at midnight)
- Works entirely via the Home Assistant UI
- Add multiple sensors via the integration panel

## Installation

1. Copy the `custom_components/daily_energy_tracker/` folder into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings → Devices & Services → Integrations → Add Integration**
4. Search for “Daily Energy Tracker”
5. Add any power (W) sensor — a kWh-per-day sensor will be created

## License

MIT
