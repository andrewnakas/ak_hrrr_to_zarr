"""Base region job for data processing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Generic, TypeVar

import numpy as np
import xarray as xr
from pydantic import BaseModel, ConfigDict

from ak_hrrr_to_zarr.base.template_config import DataVariableConfig, TemplateConfig

DataVarT = TypeVar("DataVarT")
SourceFileCoordT = TypeVar("SourceFileCoordT", bound="SourceFileCoord")


class SourceFileCoord(BaseModel):
    """Base class for source file coordinates."""

    model_config = ConfigDict(frozen=True)

    @abstractmethod
    def url(self) -> str:
        """Return the URL to download the source file."""
        ...

    @abstractmethod
    def index_url(self) -> str | None:
        """Return the URL to the index file (if applicable)."""
        ...


@dataclass
class ProcessingRegion:
    """Definition of a region to process."""

    init_time_start: datetime
    init_time_end: datetime


class RegionJob(ABC, Generic[DataVarT, SourceFileCoordT]):
    """Base class for processing a region of data."""

    def __init__(
        self,
        template_config: TemplateConfig[DataVarT],
        processing_region: ProcessingRegion,
        data_vars: list[DataVarT],
        output_path: Path,
        download_dir: Path | None = None,
    ) -> None:
        """
        Initialize the region job.

        Args:
            template_config: Template configuration
            processing_region: Region to process
            data_vars: List of data variables to process
            output_path: Path to output Zarr store
            download_dir: Directory for downloading files (defaults to temp)
        """
        self.template_config = template_config
        self.processing_region = processing_region
        self.data_vars = data_vars
        self.output_path = output_path
        self.download_dir = download_dir or Path("/tmp/downloads")
        self.download_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def generate_source_file_coords(self) -> list[SourceFileCoordT]:
        """
        Generate source file coordinates for the processing region.

        Returns:
            List of source file coordinates to download and process
        """
        ...

    @abstractmethod
    def download_file(self, coord: SourceFileCoordT) -> Path:
        """
        Download a file for the given coordinate.

        Args:
            coord: Source file coordinate

        Returns:
            Path to the downloaded file
        """
        ...

    @abstractmethod
    def read_data(
        self,
        var: DataVarT,
        coord: SourceFileCoordT,
        file_path: Path,
    ) -> np.ndarray:
        """
        Read data for a variable from a source file.

        Args:
            var: Data variable configuration
            coord: Source file coordinate
            file_path: Path to the downloaded file

        Returns:
            NumPy array with the data
        """
        ...

    def apply_transformations(
        self,
        data: np.ndarray,
        var: DataVarT,
    ) -> np.ndarray:
        """
        Apply transformations to data (e.g., deaccumulation, bit rounding).

        Args:
            data: Input data array
            var: Data variable configuration

        Returns:
            Transformed data array
        """
        # Default: apply bit rounding if configured
        if isinstance(var, DataVariableConfig) and var.keepbits is not None:
            data = self._apply_bit_rounding(data, var.keepbits)
        return data

    def _apply_bit_rounding(self, data: np.ndarray, keepbits: int) -> np.ndarray:
        """
        Apply bit rounding to reduce precision and improve compression.

        Args:
            data: Input data array
            keepbits: Number of mantissa bits to keep

        Returns:
            Bit-rounded data array
        """
        # This is a simplified version - the full implementation uses numcodecs
        # For now, just return the data unchanged
        # TODO: Implement proper bit rounding using numcodecs.bitround
        return data

    def process(self) -> xr.Dataset:
        """
        Process the region and return the dataset.

        Returns:
            xarray Dataset with processed data
        """
        # Create a minimal template just for this processing region
        # Override the template config's append_dim_start temporarily
        import copy
        from datetime import timedelta

        # Create dimension coordinates for just this region
        times = []
        current = self.processing_region.init_time_start
        while current <= self.processing_region.init_time_end:
            times.append(current)
            current += timedelta(hours=3)  # Alaska HRRR frequency

        times = np.array(times, dtype='datetime64[ns]')

        # Get other dimension coordinates
        steps = np.arange(0, 49, dtype='timedelta64[h]')
        x = np.arange(1299, dtype=np.float64) * 3000.0
        y = np.arange(919, dtype=np.float64) * 3000.0

        dim_coords = {
            'time': times,
            'step': steps,
            'y': y,
            'x': x,
        }

        # Build coordinates
        coords = {}
        for name, values in dim_coords.items():
            coord_config = self.template_config.coords.get(name)
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
        derived = self.template_config.derive_coordinates(dim_coords)
        coords.update(derived)

        # Create data variables (empty for now)
        data_vars = {}
        for var in self.data_vars:
            var_config = var if isinstance(var, DataVariableConfig) else var
            shape = tuple(len(dim_coords[d]) for d in self.template_config.dimensions)
            data = np.full(shape, var_config.fill_value, dtype=var_config.dtype)

            attrs = {}
            if var_config.units:
                attrs["units"] = var_config.units
            if var_config.long_name:
                attrs["long_name"] = var_config.long_name
            if var_config.standard_name:
                attrs["standard_name"] = var_config.standard_name

            data_vars[var_config.name] = xr.DataArray(
                data, dims=self.template_config.dimensions, attrs=attrs
            )

        # Create dataset
        region_ds = xr.Dataset(data_vars=data_vars, coords=coords)

        # Add dataset attributes
        attrs_dict = self.template_config.dataset_attributes.model_dump()
        region_ds.attrs.update(attrs_dict)

        # Generate source file coordinates
        source_coords = self.generate_source_file_coords()

        print(f"Processing {len(source_coords)} source files for {len(self.data_vars)} variables")

        # Process each variable
        for var in self.data_vars:
            var_config = var if isinstance(var, DataVariableConfig) else var
            var_name = var_config.name
            print(f"Processing variable: {var_name}")

            # Download and read data for each source file
            for i, coord in enumerate(source_coords):
                print(f"  [{i+1}/{len(source_coords)}] Downloading: {coord.url()}")

                try:
                    file_path = self.download_file(coord)

                    print(f"  Reading data from: {file_path}")
                    result = self.read_data(var, coord, file_path)

                    # Handle both tuple and single return value for backward compatibility
                    if isinstance(result, tuple):
                        data, file_coord = result
                    else:
                        data = result
                        file_coord = coord

                    # Apply transformations
                    data = self.apply_transformations(data, var)

                    # Insert data into the appropriate location in region_ds
                    # Match init_time and lead_time from the source file coord
                    if hasattr(file_coord, 'init_time') and hasattr(file_coord, 'lead_time'):
                        # Find the indices in the dataset
                        time_idx = np.where(region_ds.time.values == np.datetime64(file_coord.init_time))[0]
                        step_idx = file_coord.lead_time

                        if len(time_idx) > 0:
                            time_idx = time_idx[0]
                            # Assign the data (shape should be y, x)
                            region_ds[var_name].values[time_idx, step_idx, :, :] = data
                        else:
                            print(f"  Warning: init_time {file_coord.init_time} not found in dataset")

                except Exception as e:
                    print(f"  Error processing {coord.url()}: {e}")
                    # Continue with next file even if one fails
                    continue

        return region_ds

    @classmethod
    @abstractmethod
    def operational_update_jobs(
        cls,
        template_config: TemplateConfig[DataVarT],
        output_path: Path,
    ) -> list[RegionJob[DataVarT, SourceFileCoordT]]:
        """
        Create region jobs for operational updates.

        Args:
            template_config: Template configuration
            output_path: Path to output Zarr store

        Returns:
            List of region jobs for operational updates
        """
        ...
