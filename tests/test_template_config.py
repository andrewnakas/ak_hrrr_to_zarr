"""Tests for template configuration."""

from datetime import datetime

import numpy as np
import pytest

from ak_hrrr_to_zarr.noaa.hrrr_alaska.forecast.template_config import (
    AlaskaHrrrTemplateConfig,
)


def test_template_config_initialization() -> None:
    """Test that template config initializes correctly."""
    config = AlaskaHrrrTemplateConfig()

    assert config.dimensions == ("init_time", "lead_time", "y", "x")
    assert config.append_dim == "init_time"
    assert config.append_dim_freq == "3h"


def test_dataset_attributes() -> None:
    """Test dataset attributes."""
    config = AlaskaHrrrTemplateConfig()
    attrs = config.dataset_attributes

    assert attrs.id == "noaa-hrrr-alaska-forecast"
    assert attrs.provider == "NOAA"
    assert attrs.model == "HRRR"
    assert attrs.variant == "alaska-forecast"


def test_dimension_coordinates() -> None:
    """Test dimension coordinate generation."""
    config = AlaskaHrrrTemplateConfig()
    end = datetime(2024, 1, 1, 12, 0, 0)

    coords = config.dimension_coordinates(end)

    # Check dimensions exist
    assert "init_time" in coords
    assert "lead_time" in coords
    assert "y" in coords
    assert "x" in coords

    # Check grid dimensions (Alaska HRRR: 1299 x 919)
    assert len(coords["x"]) == 1299
    assert len(coords["y"]) == 919

    # Check lead times (0-48 hours)
    assert len(coords["lead_time"]) == 49


def test_data_vars() -> None:
    """Test data variable configuration."""
    config = AlaskaHrrrTemplateConfig()
    data_vars = config.data_vars

    assert len(data_vars) > 0

    # Check that key variables exist
    var_names = [v.name for v in data_vars]
    assert "t2m" in var_names
    assert "u10" in var_names
    assert "v10" in var_names
    assert "tp" in var_names


def test_get_template() -> None:
    """Test template dataset creation."""
    config = AlaskaHrrrTemplateConfig()
    end = datetime(2018, 7, 13, 6, 0, 0)  # Just a few timesteps

    template_ds = config.get_template(end)

    # Check dimensions
    assert "init_time" in template_ds.dims
    assert "lead_time" in template_ds.dims
    assert "y" in template_ds.dims
    assert "x" in template_ds.dims

    # Check grid size
    assert template_ds.dims["x"] == 1299
    assert template_ds.dims["y"] == 919

    # Check coordinates
    assert "latitude" in template_ds.coords
    assert "longitude" in template_ds.coords
    assert "valid_time" in template_ds.coords

    # Check data variables
    assert "t2m" in template_ds.data_vars

    # Check attributes
    assert "id" in template_ds.attrs
    assert template_ds.attrs["id"] == "noaa-hrrr-alaska-forecast"
