"""Constants for the WillyWeather Radar integration."""

DOMAIN = "willyradar"

CONF_API_KEY = "api_key"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_UPSCALE = "upscale"
CONF_SMOOTH = "smooth"
CONF_SCALE_FACTOR = "scale_factor"
CONF_BLUR_RADIUS = "blur_radius"

DEFAULT_UPSCALE = False
DEFAULT_SMOOTH = False
DEFAULT_SCALE_FACTOR = 1.5
DEFAULT_BLUR_RADIUS = 1.0

API_BASE_URL = "https://api.willyweather.com.au/v2"

ATTR_BOUNDS_SOUTH = "bounds_south"
ATTR_BOUNDS_WEST = "bounds_west"
ATTR_BOUNDS_NORTH = "bounds_north"
ATTR_BOUNDS_EAST = "bounds_east"
