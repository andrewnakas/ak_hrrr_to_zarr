"""Template configuration for Alaska HRRR forecast data."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pyproj
import xarray as xr
from pydantic import ConfigDict

from ak_hrrr_to_zarr.base.template_config import (
    CoordinateConfig,
    DatasetAttributes,
    DataVariableConfig,
    TemplateConfig,
)


class AlaskaHrrrTemplateConfig(TemplateConfig[DataVariableConfig]):
    """Template configuration for Alaska HRRR forecast data."""

    model_config = ConfigDict(frozen=True)

    # Alaska HRRR grid dimensions: 1299 x 919
    dimensions: tuple[str, ...] = ("time", "step", "y", "x")
    append_dim: str = "time"
    # Start from July 2018 (when Alaska HRRR became operational)
    append_dim_start: datetime = datetime(2018, 7, 13, 0, 0, 0)
    # Alaska HRRR updates every 3 hours
    append_dim_freq: str = "3h"

    @property
    def dataset_attributes(self) -> DatasetAttributes:
        """Return dataset-level attributes."""
        return DatasetAttributes(
            id="noaa-hrrr-alaska-forecast",
            title="NOAA HRRR Alaska Forecast",
            description="High-Resolution Rapid Refresh (HRRR) forecast data for Alaska domain. "
            "3km resolution, polar stereographic projection, updated every 3 hours. "
            "48-hour forecasts for 00/06/12/18 UTC cycles, 18-hour forecasts for 03/09/15/21 UTC cycles.",
            version="1.0.0",
            provider="NOAA",
            model="HRRR",
            variant="alaska-forecast",
        )

    def dimension_coordinates(self, append_dim_end: datetime) -> dict[str, np.ndarray]:
        """
        Return dimension coordinate arrays.

        Args:
            append_dim_end: End time for the append dimension

        Returns:
            Dictionary mapping dimension names to coordinate arrays
        """
        # Time coordinates
        times = self.append_dim_coordinates(append_dim_end).values

        # Step times: 0-48 hours (we'll store max 48h, actual may be 18h for some cycles)
        steps = np.arange(0, 49, dtype="timedelta64[h]")

        # Spatial coordinates (Alaska HRRR grid: 1299 x 919)
        # Polar stereographic projection
        # Grid spacing: 3km (3000m)
        x = np.arange(1299, dtype=np.float64) * 3000.0  # meters
        y = np.arange(919, dtype=np.float64) * 3000.0  # meters

        return {
            "time": times,
            "step": steps,
            "y": y,
            "x": x,
        }

    def derive_coordinates(
        self, dim_coords: dict[str, np.ndarray]
    ) -> dict[str, xr.DataArray]:
        """
        Derive non-dimension coordinates from dimension coordinates.

        Args:
            dim_coords: Dimension coordinate arrays

        Returns:
            Dictionary of derived coordinate DataArrays
        """
        coords = {}

        # Valid time = time + step
        times = dim_coords["time"]
        steps = dim_coords["step"]

        # Create 2D grid of valid times
        valid_time = times[:, np.newaxis] + steps[np.newaxis, :]
        coords["valid_time"] = xr.DataArray(
            valid_time,
            dims=("time", "step"),
            attrs={
                "long_name": "Valid forecast time",
                "standard_name": "time",
            },
        )

        # Expected forecast length (48h for main cycles, 18h for intermediate)
        # Cycles at 00/06/12/18 UTC have 48h forecasts
        # Cycles at 03/09/15/21 UTC have 18h forecasts
        init_hours = np.array(
            [np.datetime64(t, "h").astype("datetime64[h]").astype(int) % 24
             for t in times]
        )
        expected_length = np.where(
            np.isin(init_hours, [0, 6, 12, 18]),
            48,  # 48-hour forecasts
            18,  # 18-hour forecasts
        )
        coords["expected_forecast_length"] = xr.DataArray(
            expected_length,
            dims=("time",),
            attrs={
                "long_name": "Expected forecast length",
                "units": "hours",
            },
        )

        # Latitude and longitude grids (2D arrays due to projection)
        x = dim_coords["x"]
        y = dim_coords["y"]
        xx, yy = np.meshgrid(x, y, indexing="xy")

        # Alaska HRRR polar stereographic projection parameters
        proj = pyproj.Proj(
            proj="stere",
            lat_0=90.0,  # North Pole
            lon_0=225.0,  # -135 degrees
            lat_ts=60.0,  # Standard parallel
            x_0=0.0,
            y_0=0.0,
            R=6371229.0,  # Earth radius in meters
        )

        # Transform to lat/lon
        lon, lat = proj(xx, yy, inverse=True)

        coords["latitude"] = xr.DataArray(
            lat.astype(np.float32),
            dims=("y", "x"),
            attrs={
                "long_name": "Latitude",
                "standard_name": "latitude",
                "units": "degrees_north",
            },
        )

        coords["longitude"] = xr.DataArray(
            lon.astype(np.float32),
            dims=("y", "x"),
            attrs={
                "long_name": "Longitude",
                "standard_name": "longitude",
                "units": "degrees_east",
            },
        )

        # Spatial reference (CF grid mapping)
        coords["spatial_ref"] = xr.DataArray(
            0,
            attrs={
                "grid_mapping_name": "polar_stereographic",
                "straight_vertical_longitude_from_pole": 225.0,
                "latitude_of_projection_origin": 90.0,
                "standard_parallel": 60.0,
                "false_easting": 0.0,
                "false_northing": 0.0,
                "earth_radius": 6371229.0,
                "crs_wkt": proj.crs.to_wkt(),
            },
        )

        return coords

    @property
    def coords(self) -> dict[str, CoordinateConfig]:
        """Return coordinate configurations."""
        return {
            "time": CoordinateConfig(
                dtype="datetime64[ns]",
                chunks={"time": 1},
                units="seconds since 1970-01-01",
                long_name="Forecast initialization time",
                standard_name="forecast_reference_time",
            ),
            "step": CoordinateConfig(
                dtype="timedelta64[ns]",
                units="hours",
                long_name="Forecast lead time",
            ),
            "y": CoordinateConfig(
                dtype="float64",
                units="meters",
                long_name="Y coordinate (polar stereographic projection)",
                standard_name="projection_y_coordinate",
            ),
            "x": CoordinateConfig(
                dtype="float64",
                units="meters",
                long_name="X coordinate (polar stereographic projection)",
                standard_name="projection_x_coordinate",
            ),
        }

    @property
    def data_vars(self) -> list[DataVariableConfig]:
        """Return data variable configurations."""
        # Chunk sizes: 1 time x 49 steps x ~265 y x ~300 x
        # This gives ~15-20MB chunks uncompressed, ~3-5MB compressed
        chunk_config = {
            "time": 1,
            "step": 49,
            "y": 265,
            "x": 300,
        }

        # Core surface variables following dynamical.org CONUS HRRR pattern
        variables = [
            # Temperature and moisture
            DataVariableConfig(
                name="t2m",
                chunks=chunk_config,
                units="K",
                long_name="2 meter temperature",
                standard_name="air_temperature",
                keepbits=12,
            ),
            DataVariableConfig(
                name="d2m",
                chunks=chunk_config,
                units="K",
                long_name="2 meter dewpoint temperature",
                standard_name="dew_point_temperature",
                keepbits=12,
            ),
            DataVariableConfig(
                name="r2",
                chunks=chunk_config,
                units="%",
                long_name="2 meter relative humidity",
                standard_name="relative_humidity",
                keepbits=10,
            ),
            # Wind
            DataVariableConfig(
                name="u10",
                chunks=chunk_config,
                units="m/s",
                long_name="10 meter U wind component",
                standard_name="eastward_wind",
                keepbits=12,
            ),
            DataVariableConfig(
                name="v10",
                chunks=chunk_config,
                units="m/s",
                long_name="10 meter V wind component",
                standard_name="northward_wind",
                keepbits=12,
            ),
            DataVariableConfig(
                name="u80",
                chunks=chunk_config,
                units="m/s",
                long_name="80 meter U wind component",
                keepbits=12,
            ),
            DataVariableConfig(
                name="v80",
                chunks=chunk_config,
                units="m/s",
                long_name="80 meter V wind component",
                keepbits=12,
            ),
            DataVariableConfig(
                name="gust",
                chunks=chunk_config,
                units="m/s",
                long_name="Wind gust",
                standard_name="wind_speed_of_gust",
                keepbits=10,
            ),
            # Precipitation
            DataVariableConfig(
                name="prate",
                chunks=chunk_config,
                units="kg/m^2/s",
                long_name="Precipitation rate",
                keepbits=10,
            ),
            DataVariableConfig(
                name="crain",
                chunks=chunk_config,
                units="categorical",
                long_name="Categorical rain",
                keepbits=1,
            ),
            DataVariableConfig(
                name="csnow",
                chunks=chunk_config,
                units="categorical",
                long_name="Categorical snow",
                keepbits=1,
            ),
            DataVariableConfig(
                name="cfrzr",
                chunks=chunk_config,
                units="categorical",
                long_name="Categorical freezing rain",
                keepbits=1,
            ),
            DataVariableConfig(
                name="cicep",
                chunks=chunk_config,
                units="categorical",
                long_name="Categorical ice pellets",
                keepbits=1,
            ),
            # Clouds and radiation
            DataVariableConfig(
                name="tcc",
                chunks=chunk_config,
                units="%",
                long_name="Total cloud cover",
                standard_name="cloud_area_fraction",
                keepbits=8,
            ),
            DataVariableConfig(
                name="dswrf",
                chunks=chunk_config,
                units="W/m^2",
                long_name="Downward short-wave radiation flux",
                standard_name="surface_downwelling_shortwave_flux_in_air",
                keepbits=10,
            ),
            DataVariableConfig(
                name="dlwrf",
                chunks=chunk_config,
                units="W/m^2",
                long_name="Downward long-wave radiation flux",
                standard_name="surface_downwelling_longwave_flux_in_air",
                keepbits=10,
            ),
            # Pressure and other
            DataVariableConfig(
                name="sp",
                chunks=chunk_config,
                units="Pa",
                long_name="Surface pressure",
                standard_name="surface_air_pressure",
                keepbits=14,
            ),
            DataVariableConfig(
                name="msl",
                chunks=chunk_config,
                units="Pa",
                long_name="Mean sea level pressure",
                standard_name="air_pressure_at_mean_sea_level",
                keepbits=14,
            ),
            DataVariableConfig(
                name="vis",
                chunks=chunk_config,
                units="m",
                long_name="Visibility",
                standard_name="visibility_in_air",
                keepbits=10,
            ),
            DataVariableConfig(
                name="refc",
                chunks=chunk_config,
                units="dBZ",
                long_name="Composite radar reflectivity",
                keepbits=10,
            ),
            # Additional variables to match dynamical.org catalog
            DataVariableConfig(
                name="ceiling",
                chunks=chunk_config,
                units="m",
                long_name="Geopotential height at cloud ceiling",
                standard_name="geopotential_height_at_cloud_ceiling",
                keepbits=10,
            ),
            DataVariableConfig(
                name="cpofp",
                chunks=chunk_config,
                units="%",
                long_name="Percent frozen precipitation",
                keepbits=8,
            ),
            DataVariableConfig(
                name="pwat",
                chunks=chunk_config,
                units="kg/m^2",
                long_name="Precipitable water",
                standard_name="atmosphere_mass_content_of_water_vapor",
                keepbits=10,
            ),
            DataVariableConfig(
                name="acpcp",
                chunks=chunk_config,
                units="kg/m^2",
                long_name="Total precipitation (accumulated)",
                standard_name="precipitation_amount",
                keepbits=10,
            ),
        ]

        return variables
