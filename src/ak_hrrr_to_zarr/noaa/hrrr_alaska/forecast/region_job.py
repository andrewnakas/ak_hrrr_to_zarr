"""Region job for Alaska HRRR forecast data."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import xarray as xr
from pydantic import ConfigDict

from ak_hrrr_to_zarr.base.region_job import (
    ProcessingRegion,
    RegionJob,
    SourceFileCoord,
)
from ak_hrrr_to_zarr.base.template_config import DataVariableConfig, TemplateConfig


class AlaskaHrrrSourceFileCoord(SourceFileCoord):
    """Source file coordinate for Alaska HRRR data."""

    model_config = ConfigDict(frozen=True)

    init_time: datetime
    lead_time: int  # hours
    file_type: str  # 'sfc', 'prs', 'nat', 'subh'

    def url(self) -> str:
        """Return the URL to download the source file."""
        # Format: hrrr.YYYYMMDD/alaska/hrrr.tXXz.wrfsfcfYY.ak.grib2
        date_str = self.init_time.strftime("%Y%m%d")
        hour_str = self.init_time.strftime("%H")
        lead_str = f"{self.lead_time:02d}"

        base_url = "https://noaa-hrrr-bdp-pds.s3.amazonaws.com"
        filename = f"hrrr.t{hour_str}z.wrf{self.file_type}f{lead_str}.ak.grib2"
        return f"{base_url}/hrrr.{date_str}/alaska/{filename}"

    def index_url(self) -> str | None:
        """Return the URL to the index file."""
        return f"{self.url()}.idx"


class AlaskaHrrrForecastRegionJob(RegionJob[DataVariableConfig, AlaskaHrrrSourceFileCoord]):
    """Region job for processing Alaska HRRR forecast data."""

    # Variable name mapping from GRIB to our standard names
    # Note: NOAA HRRR uses standard GRIB short names, not ECMWF convention
    VARIABLE_MAPPING = {
        "t2m": {"grib_name": "t2m", "typeOfLevel": "heightAboveGround", "level": 2.0},
        "d2m": {"grib_name": "d2m", "typeOfLevel": "heightAboveGround", "level": 2.0},
        "r2": {"grib_name": "r2", "typeOfLevel": "heightAboveGround", "level": 2.0},
        "u10": {"grib_name": "u10", "typeOfLevel": "heightAboveGround", "level": 10.0},
        "v10": {"grib_name": "v10", "typeOfLevel": "heightAboveGround", "level": 10.0},
        "u80": {"grib_name": "u", "typeOfLevel": "heightAboveGround", "level": 80.0},
        "v80": {"grib_name": "v", "typeOfLevel": "heightAboveGround", "level": 80.0},
        "gust": {"grib_name": "gust", "typeOfLevel": "surface", "level": None},
        "prate": {"grib_name": "prate", "typeOfLevel": "surface", "level": None},
        "crain": {"grib_name": "crain", "typeOfLevel": "surface", "level": None},
        "csnow": {"grib_name": "csnow", "typeOfLevel": "surface", "level": None},
        "cfrzr": {"grib_name": "cfrzr", "typeOfLevel": "surface", "level": None},
        "cicep": {"grib_name": "cicep", "typeOfLevel": "surface", "level": None},
        "tcc": {"grib_name": "tcc", "typeOfLevel": "atmosphere", "level": None},
        "dswrf": {"grib_name": "sdswrf", "typeOfLevel": "surface", "level": None},
        "dlwrf": {"grib_name": "sdlwrf", "typeOfLevel": "surface", "level": None},
        "sp": {"grib_name": "sp", "typeOfLevel": "surface", "level": None},
        "msl": {"grib_name": "mslma", "typeOfLevel": "meanSea", "level": None},
        "vis": {"grib_name": "vis", "typeOfLevel": "surface", "level": None},
        "refc": {"grib_name": "refd", "typeOfLevel": "heightAboveGround", "level": 1000.0},
        "ceiling": {"grib_name": "gh", "typeOfLevel": "cloudCeiling", "level": None},
        "cpofp": {"grib_name": "cpofp", "typeOfLevel": "surface", "level": None},
        "pwat": {"grib_name": "pwat", "typeOfLevel": "atmosphereSingleLayer", "level": None},
        "acpcp": {"grib_name": "tp", "typeOfLevel": "surface", "level": None, "stepType": "accum"},
    }

    def generate_source_file_coords(self) -> list[AlaskaHrrrSourceFileCoord]:
        """
        Generate source file coordinates for the processing region.

        Returns:
            List of source file coordinates to download and process
        """
        coords = []

        # Generate coordinates for each init time in the processing region
        current = self.processing_region.init_time_start
        while current <= self.processing_region.init_time_end:
            # Determine forecast length based on cycle
            # 00/06/12/18 UTC: 48-hour forecasts
            # 03/09/15/21 UTC: 18-hour forecasts
            if current.hour in [0, 6, 12, 18]:
                max_lead = 48
            else:
                max_lead = 18

            # Generate coordinate for each lead time
            # Most variables are in the 'sfc' (surface) file
            for lead in range(0, max_lead + 1):
                coords.append(
                    AlaskaHrrrSourceFileCoord(
                        init_time=current,
                        lead_time=lead,
                        file_type="sfc",
                    )
                )

            # Move to next init time (3 hours)
            current += timedelta(hours=3)

        return coords

    def download_file(self, coord: AlaskaHrrrSourceFileCoord) -> Path:
        """
        Download a file for the given coordinate.

        Uses byte-range requests with index files for efficient partial downloads.

        Args:
            coord: Source file coordinate

        Returns:
            Path to the downloaded file
        """
        # Create a unique filename
        date_str = coord.init_time.strftime("%Y%m%d_%H")
        filename = f"hrrr_ak_{date_str}_f{coord.lead_time:02d}_{coord.file_type}.grib2"
        output_path = self.download_dir / filename

        # Check if already downloaded
        if output_path.exists():
            print(f"  File already exists: {output_path}")
            return output_path

        url = coord.url()
        print(f"  Downloading from: {url}")

        try:
            # Download the full file
            # In production, you would use the index file for byte-range requests
            # to only download the needed variables
            with httpx.stream("GET", url, timeout=60.0, follow_redirects=True) as response:
                response.raise_for_status()

                with open(output_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)

            print(f"  Downloaded successfully: {output_path}")
            return output_path

        except httpx.HTTPError as e:
            print(f"  Error downloading {url}: {e}")
            raise

    def _get_grib_variable_info(self, var_name: str) -> dict[str, str]:
        """Get GRIB variable information from mapping."""
        if var_name not in self.VARIABLE_MAPPING:
            raise ValueError(f"Variable {var_name} not in mapping")
        return self.VARIABLE_MAPPING[var_name]

    def read_data(
        self,
        var: DataVariableConfig,
        coord: AlaskaHrrrSourceFileCoord,
        file_path: Path,
    ) -> tuple[np.ndarray, AlaskaHrrrSourceFileCoord]:
        """
        Read data for a variable from a source file.

        Args:
            var: Data variable configuration
            coord: Source file coordinate
            file_path: Path to the downloaded file

        Returns:
            Tuple of (NumPy array with the data (shape: y, x), coordinate)
        """
        try:
            grib_info = self._get_grib_variable_info(var.name)
            grib_name = grib_info["grib_name"]
            type_of_level = grib_info["typeOfLevel"]
            level = grib_info.get("level")
            step_type = grib_info.get("stepType", "instant")  # Default to instant

            # Build cfgrib filter keys
            filter_keys = {
                "typeOfLevel": type_of_level,
                "stepType": step_type,
            }

            # Add level filter if specified
            if level is not None:
                filter_keys["level"] = level

            # Open GRIB file with xarray/cfgrib
            ds = xr.open_dataset(
                file_path,
                engine="cfgrib",
                filter_by_keys=filter_keys,
                backend_kwargs={"indexpath": ""},  # Don't create index files
            )

            # Get the variable data
            if grib_name in ds.data_vars:
                data = ds[grib_name].values
                ds.close()
                return data.astype(var.dtype), coord
            else:
                ds.close()
                raise ValueError(
                    f"Variable {grib_name} not found in dataset. "
                    f"Available: {list(ds.data_vars.keys())}"
                )

        except Exception as e:
            print(f"  Error reading {var.name} from {file_path}: {e}")
            raise

    @classmethod
    def operational_update_jobs(
        cls,
        template_config: TemplateConfig[DataVariableConfig],
        output_path: Path,
    ) -> list[AlaskaHrrrForecastRegionJob]:
        """
        Create region jobs for operational updates.

        For Alaska HRRR, we want to fetch the most recent cycle data.
        Alaska HRRR updates every 3 hours, with a delay of ~2 hours for data availability.

        Args:
            template_config: Template configuration
            output_path: Path to output Zarr store

        Returns:
            List of region jobs for operational updates
        """
        # Get the most recent init time
        # Alaska HRRR cycles: 00, 03, 06, 09, 12, 15, 18, 21 UTC
        # Data is usually available ~2 hours after init time
        # For operational updates, prefer main cycles (00/06/12/18 UTC) which have 48-hour forecasts
        # Intermediate cycles (03/09/15/21 UTC) only have 18-hour forecasts
        now = datetime.utcnow()

        # Round down to the most recent 6-hour main cycle (00, 06, 12, 18 UTC)
        # This ensures we get the full 48-hour forecast
        hours_since_midnight = now.hour
        init_hour = (hours_since_midnight // 6) * 6

        # Go back one cycle if we're too close to the current cycle
        # (data may not be available yet)
        init_time = now.replace(hour=init_hour, minute=0, second=0, microsecond=0)
        if (now - init_time).total_seconds() < 2 * 3600:  # Less than 2 hours old
            init_time -= timedelta(hours=6)

        print(f"Fetching Alaska HRRR data for init time: {init_time} UTC (48-hour forecast)")

        # Create a processing region for just this init time
        processing_region = ProcessingRegion(
            init_time_start=init_time,
            init_time_end=init_time,
        )

        # Create a job for all variables
        job = cls(
            template_config=template_config,
            processing_region=processing_region,
            data_vars=template_config.data_vars,
            output_path=output_path,
        )

        return [job]
