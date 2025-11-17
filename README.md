# Alaska HRRR to Zarr

> Automated reformatting of NOAA Alaska HRRR weather forecasts into Zarr format, following [dynamical.org](https://dynamical.org) architecture patterns.

[![Update Alaska HRRR Data](https://github.com/andrewnakas/ak_hrrr_to_zarr/actions/workflows/update-data.yml/badge.svg)](https://github.com/andrewnakas/ak_hrrr_to_zarr/actions/workflows/update-data.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This project automatically downloads NOAA's Alaska HRRR (High-Resolution Rapid Refresh) forecast data and converts it to [Zarr format](https://zarr.dev/) for efficient cloud-native access. The system runs entirely on GitHub Actions and serves a data catalog via GitHub Pages.

### Key Features

- ⚡ **Automated ingestion**: GitHub Actions runs every 3 hours
- 📦 **Zarr format**: Cloud-optimized with compression (~5x smaller than GRIB2)
- 🗺️ **Alaska domain**: 1299×919 grid, 3km resolution, polar stereographic projection
- 🌤️ **Comprehensive variables**: Temperature, wind, precipitation, clouds, radiation, and more
- 📊 **Data catalog**: Beautiful web interface via GitHub Pages
- 🏗️ **Production-ready**: Follows [dynamical.org](https://dynamical.org) best practices

## Data Specifications

| Property | Value |
|----------|-------|
| **Grid Size** | 1299 × 919 (1,193,781 points) |
| **Resolution** | 3 km |
| **Projection** | Polar Stereographic (North Pole centered) |
| **Update Frequency** | Every 3 hours |
| **Forecast Length** | 48h (00/06/12/18 UTC), 18h (03/09/15/21 UTC) |
| **Variables** | 20+ surface and atmospheric variables |
| **Data Source** | NOAA AWS Open Data |

## Quick Start

### Installation

```bash
# Install uv package manager (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/andrewnakas/ak_hrrr_to_zarr.git
cd ak_hrrr_to_zarr

# Install dependencies
uv sync --all-extras

# Install pre-commit hooks (optional, for development)
uv run pre-commit install
```

### Usage

```bash
# List available datasets
uv run ak-hrrr list-datasets

# Show dataset information
uv run ak-hrrr info noaa-hrrr-alaska-forecast

# Update template (generates metadata structure)
uv run ak-hrrr update-template noaa-hrrr-alaska-forecast

# Run operational update (fetch latest data)
uv run ak-hrrr operational-update noaa-hrrr-alaska-forecast \
    --output data/hrrr_alaska.zarr
```

### Accessing Data with Python

```python
import xarray as xr

# Open the Zarr store
ds = xr.open_zarr("data/hrrr_alaska.zarr")

# View available variables
print(ds.data_vars)

# Access specific variable
temperature = ds["t2m"]  # 2-meter temperature

# Select data for a specific time
latest = ds.isel(init_time=-1)

# Get forecast for specific location
point = ds.sel(x=500000, y=300000, method="nearest")
```

## Architecture

This project implements the [dynamical.org reformatter architecture](https://github.com/dynamical-org/reformatters):

```
┌─────────────────────┐
│  TemplateConfig     │  Defines dataset structure
│  - Dimensions       │  (dimensions, coordinates, variables)
│  - Coordinates      │
│  - Data Variables   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  RegionJob          │  Processes data chunks
│  - Download GRIB2   │  (download, read, transform)
│  - Read with        │
│    rasterio         │
│  - Apply transforms │
│  - Write to Zarr    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Dataset            │  Orchestrates workflow
│  - Operational      │  (scheduling, coordination)
│    updates          │
│  - Job management   │
└─────────────────────┘
```

### Key Components

1. **TemplateConfig** (`src/ak_hrrr_to_zarr/base/template_config.py`)
   - Defines dataset structure with dimensions, coordinates, and variables
   - Handles metadata and CF-conventions compliance
   - Creates empty template datasets for Zarr initialization

2. **RegionJob** (`src/ak_hrrr_to_zarr/base/region_job.py`)
   - Downloads GRIB2 files from NOAA AWS S3
   - Reads data using rasterio
   - Applies transformations (bit rounding, unit conversions)
   - Writes processed data to Zarr stores

3. **Dataset** (`src/ak_hrrr_to_zarr/base/dataset.py`)
   - Orchestrates the end-to-end workflow
   - Manages operational updates
   - Coordinates multiple region jobs

### Alaska HRRR Implementation

```
src/ak_hrrr_to_zarr/noaa/hrrr_alaska/forecast/
├── template_config.py   # Grid specs, coordinates, variables
├── region_job.py        # GRIB2 download and processing
└── dataset.py           # Operational workflow orchestration
```

## Variables

The system processes 20+ meteorological variables:

| Category | Variables |
|----------|-----------|
| **Temperature** | 2m temperature, 2m dewpoint, 2m relative humidity |
| **Wind** | 10m U/V components, 80m U/V components, gusts |
| **Precipitation** | Total precipitation, rate, categorical (rain/snow/freezing rain/ice pellets) |
| **Clouds** | Total cloud cover |
| **Radiation** | Downward shortwave/longwave flux |
| **Pressure** | Surface pressure, mean sea level pressure |
| **Other** | Visibility, composite radar reflectivity |

## Data Source

Data is sourced from the [NOAA Big Data Program](https://registry.opendata.aws/noaa-hrrr-pds/):

- **S3 Bucket**: `s3://noaa-hrrr-bdp-pds/hrrr.{YYYYMMDD}/alaska/`
- **File Pattern**: `hrrr.t{HH}z.wrfsfcf{FF}.ak.grib2`
- **Format**: GRIB2
- **Access**: Public, no credentials required

### Example URLs

```
# Latest 00 UTC cycle, 0-hour forecast
https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.20241113/alaska/hrrr.t00z.wrfsfcf00.ak.grib2

# Latest 00 UTC cycle, 12-hour forecast
https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.20241113/alaska/hrrr.t00z.wrfsfcf12.ak.grib2
```

## GitHub Actions Workflow

The system runs automatically via GitHub Actions (`.github/workflows/update-data.yml`):

### Schedule

```yaml
# Runs 15 minutes after each HRRR cycle
schedule:
  - cron: '15 0,3,6,9,12,15,18,21 * * *'
```

### Workflow Steps

1. **Checkout & Setup**: Python 3.12 + uv package manager
2. **Download**: Fetch latest GRIB2 files from NOAA AWS
3. **Process**: Convert to Zarr with compression
4. **Commit**: Update data files in repository
5. **Deploy**: Publish catalog to GitHub Pages

## GitHub Pages Catalog

The data catalog is automatically generated and deployed to GitHub Pages:

🌐 **View Catalog**: `https://<username>.github.io/<repo>/`

The catalog provides:
- Dataset metadata and descriptions
- Temporal coverage and dimensions
- Available variables
- Direct links to Zarr stores
- JSON metadata for programmatic access

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=ak_hrrr_to_zarr --cov-report=html

# Run specific test
uv run pytest tests/test_template_config.py
```

### Code Quality

```bash
# Lint
uv run ruff check src/

# Format
uv run ruff format src/

# Type check
uv run mypy src/
```

## Comparison with dynamical.org

This project follows the architecture of [dynamical.org/reformatters](https://github.com/dynamical-org/reformatters) but adapted for:

| Aspect | dynamical.org | This Project |
|--------|---------------|--------------|
| **Deployment** | Kubernetes | GitHub Actions |
| **Storage** | S3 (Source Coop) | Git LFS / GitHub Releases |
| **Scheduling** | CronJobs | GitHub Actions cron |
| **Domain** | CONUS HRRR | Alaska HRRR |
| **Projection** | Lambert Conformal | Polar Stereographic |
| **Grid** | 1799×1059 | 1299×919 |

## Roadmap

- [ ] Add pressure level data (`hrrr.t{HH}z.wrfprsf{FF}.ak.grib2`)
- [ ] Add native level data (`hrrr.t{HH}z.wrfnatf{FF}.ak.grib2`)
- [ ] Add subhourly data (`hrrr.t{HH}z.wrfsubhf{FF}.ak.grib2`)
- [ ] Implement git-lfs for large Zarr stores
- [ ] Add data validation checks
- [ ] Create Intake catalog for data discovery
- [ ] Add visualization examples with hvPlot

## Credits

- Architecture inspired by [dynamical.org](https://dynamical.org)
- Data from [NOAA HRRR on AWS](https://registry.opendata.aws/noaa-hrrr-pds/)
- Built with [Zarr](https://zarr.dev/), [Xarray](https://xarray.dev/), and [rasterio](https://rasterio.readthedocs.io/)

## License

MIT License - see [LICENSE](LICENSE) file for details.
