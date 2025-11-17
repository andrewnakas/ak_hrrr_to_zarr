"""Base template configuration for datasets."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Generic, TypeVar

import numpy as np
import pandas as pd
import xarray as xr
from pydantic import BaseModel, ConfigDict

DataVarT = TypeVar("DataVarT")


class CoordinateConfig(BaseModel):
    """Configuration for a coordinate variable."""

    model_config = ConfigDict(frozen=True)

    dtype: str
    chunks: dict[str, int] | None = None
    compression: str = "zstd"
    compression_level: int = 3
    units: str | None = None
    long_name: str | None = None
    standard_name: str | None = None


class DataVariableConfig(BaseModel):
    """Configuration for a data variable."""

    model_config = ConfigDict(frozen=True)

    name: str
    dtype: str = "float32"
    chunks: dict[str, int]
    compression: str = "zstd"
    compression_level: int = 3
    units: str | None = None
    long_name: str | None = None
    standard_name: str | None = None
    fill_value: float = np.nan
    # Bit rounding for compression (mantissa bits to keep)
    keepbits: int | None = None


class DatasetAttributes(BaseModel):
    """Dataset-level attributes."""

    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    description: str
    version: str
    provider: str
    model: str
    variant: str


class TemplateConfig(BaseModel, ABC, Generic[DataVarT]):
    """Base configuration for dataset templates."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    # Dimension definitions
    dimensions: tuple[str, ...]
    append_dim: str  # The dimension to append to (e.g., "init_time")
    append_dim_start: datetime
    append_dim_freq: str  # Pandas frequency string (e.g., "3h", "6h")

    @property
    @abstractmethod
    def dataset_attributes(self) -> DatasetAttributes:
        """Return dataset-level attributes."""
        ...

    @abstractmethod
    def dimension_coordinates(self, append_dim_end: datetime) -> dict[str, np.ndarray]:
        """
        Return dimension coordinate arrays.

        Args:
            append_dim_end: End time for the append dimension

        Returns:
            Dictionary mapping dimension names to coordinate arrays
        """
        ...

    @abstractmethod
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
        ...

    @property
    @abstractmethod
    def coords(self) -> dict[str, CoordinateConfig]:
        """Return coordinate configurations."""
        ...

    @property
    @abstractmethod
    def data_vars(self) -> list[DataVarT]:
        """Return data variable configurations."""
        ...

    def append_dim_coordinates(self, end: datetime) -> pd.DatetimeIndex:
        """Generate DatetimeIndex for the append dimension."""
        return pd.date_range(
            start=self.append_dim_start,
            end=end,
            freq=self.append_dim_freq,
        )

    def get_template(self, end: datetime) -> xr.Dataset:
        """
        Create an empty template dataset.

        Args:
            end: End time for the append dimension

        Returns:
            Empty xarray Dataset with structure defined
        """
        # Generate dimension coordinates
        dim_coords = self.dimension_coordinates(end)

        # Create coordinate DataArrays
        coords = {}
        for name, values in dim_coords.items():
            coord_config = self.coords.get(name)
            attrs = {}
            if coord_config:
                if coord_config.units:
                    attrs["units"] = coord_config.units
                if coord_config.long_name:
                    attrs["long_name"] = coord_config.long_name
                if coord_config.standard_name:
                    attrs["standard_name"] = coord_config.standard_name
            coords[name] = xr.DataArray(values, dims=[name], attrs=attrs)

        # Add derived coordinates
        derived = self.derive_coordinates(dim_coords)
        coords.update(derived)

        # Create data variables
        data_vars = {}
        for var in self.data_vars:
            var_config = var if isinstance(var, DataVariableConfig) else var
            shape = tuple(len(dim_coords[d]) for d in self.dimensions)
            data = np.full(shape, var_config.fill_value, dtype=var_config.dtype)

            attrs = {}
            if var_config.units:
                attrs["units"] = var_config.units
            if var_config.long_name:
                attrs["long_name"] = var_config.long_name
            if var_config.standard_name:
                attrs["standard_name"] = var_config.standard_name

            data_vars[var_config.name] = xr.DataArray(
                data, dims=self.dimensions, attrs=attrs
            )

        # Create dataset
        ds = xr.Dataset(data_vars=data_vars, coords=coords)

        # Add dataset attributes
        attrs_dict = self.dataset_attributes.model_dump()
        ds.attrs.update(attrs_dict)

        return ds

    def template_path(self) -> Path:
        """Return the path to store/load the template."""
        # Store relative to the module location
        module_path = Path(__file__).parent.parent
        templates_dir = module_path / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        dataset_id = self.dataset_attributes.id.replace("-", "_")
        return templates_dir / f"{dataset_id}.zarr"
