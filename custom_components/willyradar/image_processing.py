"""Optional server-side image processing for radar overlays.

This module is designed to run in an executor via
``hass.async_add_executor_job`` because Pillow operations are CPU-bound.
"""

from __future__ import annotations

import logging
from io import BytesIO

_LOGGER = logging.getLogger(__name__)


def process_radar_image(
    image_data: bytes,
    upscale: bool = False,
    smooth: bool = False,
    scale_factor: float = 1.5,
    blur_radius: float = 1.0,
) -> bytes:
    """Apply optional upscale and Gaussian blur to a radar overlay PNG.

    Returns the original bytes unchanged when both upscale and smooth are
    False.  Raises ``ImportError`` if Pillow is not installed and processing
    is requested.
    """
    if not upscale and not smooth:
        return image_data

    from PIL import Image, ImageFilter  # noqa: E402 - lazy import

    img = Image.open(BytesIO(image_data))

    if upscale:
        new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
        img = img.resize(new_size, Image.LANCZOS)
        _LOGGER.debug("Upscaled image by %.1fx to %s", scale_factor, new_size)

    if smooth:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        _LOGGER.debug("Applied Gaussian blur (radius=%.1f)", blur_radius)

    output = BytesIO()
    img.save(output, format="PNG", optimize=True)
    return output.getvalue()
