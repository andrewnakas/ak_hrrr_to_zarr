"""Base dataset orchestrator."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

from ak_hrrr_to_zarr.base.region_job import RegionJob, SourceFileCoord
from ak_hrrr_to_zarr.base.template_config import TemplateConfig

DataVarT = TypeVar("DataVarT")
SourceFileCoordT = TypeVar("SourceFileCoordT", bound=SourceFileCoord)


class Dataset(ABC, Generic[DataVarT, SourceFileCoordT]):
    """Base class for dataset orchestration."""

    def __init__(self) -> None:
        """Initialize the dataset."""
        self._template_config: TemplateConfig[DataVarT] | None = None
        self._region_job_class: type[RegionJob[DataVarT, SourceFileCoordT]] | None = None

    @property
    @abstractmethod
    def template_config(self) -> TemplateConfig[DataVarT]:
        """Return the template configuration."""
        ...

    @property
    @abstractmethod
    def region_job_class(self) -> type[RegionJob[DataVarT, SourceFileCoordT]]:
        """Return the region job class."""
        ...

    @property
    def dataset_id(self) -> str:
        """Return the dataset ID."""
        return self.template_config.dataset_attributes.id

    def operational_update(self, output_path: Path) -> None:
        """
        Run operational update for this dataset.

        Args:
            output_path: Path to output Zarr store
        """
        print(f"Running operational update for {self.dataset_id}")

        # Get jobs from the region job class
        jobs = self.region_job_class.operational_update_jobs(
            template_config=self.template_config,
            output_path=output_path,
        )

        # Process each job
        for job in jobs:
            print(f"Processing job: {job.processing_region}")
            result_ds = job.process()

            # Save to Zarr
            print(f"Saving to: {output_path}")
            self._save_to_zarr(result_ds, output_path)

    def _save_to_zarr(self, ds, output_path: Path) -> None:
        """Save dataset to Zarr store."""
        import xarray as xr

        # Create a copy to avoid modifying the original
        ds = ds.copy()

        # Clean up attributes to avoid encoding conflicts
        # Remove units from time coordinates as xarray handles these automatically
        for coord in ["time", "step", "valid_time"]:
            if coord in ds.coords and "units" in ds[coord].attrs:
                ds[coord].attrs = {k: v for k, v in ds[coord].attrs.items() if k != "units"}

        # Remove encoding-specific attributes from all coordinates
        for coord in ds.coords:
            ds[coord].attrs = {
                k: v for k, v in ds[coord].attrs.items()
                if k not in ["dtype", "compressor", "fill_value", "filters", "chunks", "calendar"]
            }

        # Use zarr_format=2 for compatibility with standard tools
        # This uses the older, more stable zarr v2 format
        if output_path.exists():
            # Append mode
            ds.to_zarr(
                output_path,
                mode="a",
                append_dim=self.template_config.append_dim,
                zarr_format=2,
            )
        else:
            # Create new with compression
            # Let xarray handle encoding automatically with zarr v2
            ds.to_zarr(
                output_path,
                mode="w",
                zarr_format=2,
            )
