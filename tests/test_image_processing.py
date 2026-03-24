"""Tests for image processing module."""

from __future__ import annotations

from io import BytesIO
from unittest.mock import patch

import pytest
from PIL import Image

from custom_components.willyradar.image_processing import process_radar_image

from .conftest import MOCK_PNG_BYTES


def _make_png(width: int = 4, height: int = 4) -> bytes:
    """Create a simple RGBA PNG of the given size."""
    img = Image.new("RGBA", (width, height), (255, 0, 0, 128))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_no_processing_returns_original() -> None:
    """When both upscale and smooth are False, return input unchanged."""
    data = _make_png()
    result = process_radar_image(data, upscale=False, smooth=False)
    assert result is data  # identity check, not just equality


def test_upscale_increases_dimensions() -> None:
    """Upscaling by 2x should double width and height."""
    data = _make_png(4, 4)
    result = process_radar_image(data, upscale=True, scale_factor=2.0)
    img = Image.open(BytesIO(result))
    assert img.width == 8
    assert img.height == 8


def test_smooth_returns_valid_png() -> None:
    """Smoothing should return a valid PNG."""
    data = _make_png(4, 4)
    result = process_radar_image(data, smooth=True, blur_radius=1.0)
    assert result[:4] == b"\x89PNG"
    img = Image.open(BytesIO(result))
    assert img.width == 4
    assert img.height == 4


def test_upscale_and_smooth_combined() -> None:
    """Both processing options applied together."""
    data = _make_png(4, 4)
    result = process_radar_image(
        data, upscale=True, smooth=True, scale_factor=1.5, blur_radius=1.0
    )
    img = Image.open(BytesIO(result))
    assert img.width == 6  # 4 * 1.5
    assert img.height == 6


def test_scale_factor_boundary_min() -> None:
    """Scale factor of 1.0 should not change dimensions."""
    data = _make_png(4, 4)
    result = process_radar_image(data, upscale=True, scale_factor=1.0)
    img = Image.open(BytesIO(result))
    assert img.width == 4
    assert img.height == 4


def test_pillow_import_error_when_processing_requested() -> None:
    """ImportError propagates when Pillow is missing and processing requested."""
    with patch.dict("sys.modules", {"PIL": None, "PIL.Image": None, "PIL.ImageFilter": None}):
        with pytest.raises(ImportError):
            # Force reimport by calling with processing enabled
            # The lazy import inside the function will fail
            from importlib import reload
            import custom_components.willyradar.image_processing as mod
            reload(mod)
            mod.process_radar_image(MOCK_PNG_BYTES, upscale=True)
