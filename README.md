# WillyWeather Radar

Home Assistant custom component that provides Australian weather radar imagery from WillyWeather as a camera entity. Radar images are fetched on-demand when the Lovelace UI requests them, minimising API calls and bandwidth.

## Features

- Native HA camera entity -- works with picture cards, picture-entity cards, etc.
- On-demand fetching -- zero API calls until the camera is viewed
- In-memory caching -- same overlay is never downloaded twice
- Optional server-side image processing (upscale + smoothing) gated by config
- Async throughout (aiohttp, executor for Pillow)

## Requirements

- WillyWeather API key ([free tier available](https://www.willyweather.com.au/info/api.html))
- Home Assistant 2024.1+
- Pillow (included with HA, only required if image processing is enabled)

## Installation

Copy the `custom_components/willyradar` directory into your Home Assistant `config/custom_components/` directory and restart.

## Configuration

Add to your `configuration.yaml`:

```yaml
# Required: domain config with API key
willyradar:
  api_key: "YOUR_WILLYWEATHER_API_KEY"

# Camera platform
camera:
  - platform: willyradar
    name: "Sydney Radar"          # optional, default: "willy_radar"
    latitude: -33.8688            # optional, defaults to HA home location
    longitude: 151.2093           # optional, defaults to HA home location
    upscale: false                # optional, default: false
    smooth: false                 # optional, default: false
    scale_factor: 1.5             # optional, 1.0-3.0, default: 1.5
    blur_radius: 1.0              # optional, 0.5-3.0, default: 1.0
```

### Configuration options

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `api_key` | string | *required* | Your WillyWeather API key |
| `name` | string | `willy_radar` | Entity friendly name |
| `latitude` | float | HA home latitude | Radar centre latitude |
| `longitude` | float | HA home longitude | Radar centre longitude |
| `upscale` | boolean | `false` | Enable Pillow LANCZOS upscaling |
| `smooth` | boolean | `false` | Enable Gaussian blur smoothing |
| `scale_factor` | float | `1.5` | Upscale multiplier (1.0-3.0) |
| `blur_radius` | float | `1.0` | Gaussian blur radius (0.5-3.0) |

### Multiple cameras

You can add multiple camera entities with different locations:

```yaml
camera:
  - platform: willyradar
    name: "Sydney Radar"
    latitude: -33.8688
    longitude: 151.2093

  - platform: willyradar
    name: "Melbourne Radar"
    latitude: -37.8136
    longitude: 144.9631
    upscale: true
    smooth: true
```

## State attributes

After the first image fetch, the camera entity exposes radar geographic bounds:

| Attribute | Description |
|-----------|-------------|
| `bounds_south` | Southern latitude boundary |
| `bounds_west` | Western longitude boundary |
| `bounds_north` | Northern latitude boundary |
| `bounds_east` | Eastern longitude boundary |

## Development

### Running tests

```bash
pip install pytest pytest-homeassistant-custom-component Pillow PyTurboJPEG
pytest tests/ -v
```

## Attribution

This component is based on [willyweather-radar-addon](https://github.com/safepay/willyweather-radar-addon) by [@safepay](https://github.com/safepay).
