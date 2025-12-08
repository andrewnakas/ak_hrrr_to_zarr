"""Alaska HRRR forecast dataset orchestrator."""

from ak_hrrr_to_zarr.base.dataset import Dataset
from ak_hrrr_to_zarr.base.template_config import DataVariableConfig
from ak_hrrr_to_zarr.noaa.hrrr_alaska.forecast.region_job import (
    AlaskaHrrrForecastRegionJob,
    AlaskaHrrrSourceFileCoord,
)
from ak_hrrr_to_zarr.noaa.hrrr_alaska.forecast.template_config import (
    AlaskaHrrrTemplateConfig,
)


class AlaskaHrrrForecastDataset(Dataset[DataVariableConfig, AlaskaHrrrSourceFileCoord]):
    """Alaska HRRR forecast dataset orchestrator."""

    @property
    def template_config(self) -> AlaskaHrrrTemplateConfig:
        """Return the template configuration."""
        if self._template_config is None:
            self._template_config = AlaskaHrrrTemplateConfig()
        return self._template_config  # type: ignore

    @property
    def region_job_class(self) -> type[AlaskaHrrrForecastRegionJob]:
        """Return the region job class."""
        return AlaskaHrrrForecastRegionJob
