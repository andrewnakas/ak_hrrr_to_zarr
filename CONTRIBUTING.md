## Contributing to Alaska HRRR to Zarr

Thank you for your interest in contributing to this project!

## Development Setup

1. **Install uv package manager**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/andrewnakas/ak_hrrr_to_zarr.git
   cd ak_hrrr_to_zarr
   ```

3. **Install dependencies**:
   ```bash
   uv sync --all-extras --dev
   ```

4. **Install pre-commit hooks**:
   ```bash
   uv run pre-commit install
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=ak_hrrr_to_zarr --cov-report=html

# Run specific test file
uv run pytest tests/test_template_config.py
```

### Code Quality

```bash
# Run linter
uv run ruff check src/

# Auto-fix linting issues
uv run ruff check --fix src/

# Format code
uv run ruff format src/

# Type checking
uv run mypy src/
```

### Running the CLI

```bash
# List available datasets
uv run ak-hrrr list-datasets

# Show dataset info
uv run ak-hrrr info noaa-hrrr-alaska-forecast

# Update template
uv run ak-hrrr update-template noaa-hrrr-alaska-forecast

# Run operational update
uv run ak-hrrr operational-update noaa-hrrr-alaska-forecast
```

## Architecture

The project follows the dynamical.org reformatter architecture:

### Core Components

1. **TemplateConfig** (`src/ak_hrrr_to_zarr/base/template_config.py`)
   - Defines dataset structure (dimensions, coordinates, variables)
   - Handles metadata and attributes
   - Creates empty template datasets

2. **RegionJob** (`src/ak_hrrr_to_zarr/base/region_job.py`)
   - Downloads data from source
   - Reads GRIB2 files
   - Applies transformations
   - Writes to Zarr

3. **Dataset** (`src/ak_hrrr_to_zarr/base/dataset.py`)
   - Orchestrates the overall process
   - Manages operational updates

### Alaska HRRR Implementation

- **Template Config**: `src/ak_hrrr_to_zarr/noaa/hrrr_alaska/forecast/template_config.py`
  - Grid: 1299 x 919 (polar stereographic)
  - Resolution: 3 km
  - Updates: Every 3 hours

- **Region Job**: `src/ak_hrrr_to_zarr/noaa/hrrr_alaska/forecast/region_job.py`
  - Downloads from NOAA AWS S3 bucket
  - Processes GRIB2 files with rasterio
  - Handles 48h and 18h forecast lengths

## Adding New Datasets

To add a new dataset (e.g., Alaska HRRR pressure levels):

1. Create a new module in `src/ak_hrrr_to_zarr/noaa/hrrr_alaska/`

2. Implement three classes:
   - `YourTemplateConfig(TemplateConfig)`
   - `YourRegionJob(RegionJob)`
   - `YourDataset(Dataset)`

3. Register in `src/ak_hrrr_to_zarr/__main__.py`:
   ```python
   DATASETS = {
       "your-dataset-id": YourDataset,
       # ...
   }
   ```

4. Add tests in `tests/test_your_dataset.py`

## Submitting Changes

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "Add your feature"
   ```

3. Push and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Write docstrings for all public functions/classes
- Keep functions focused and small
- Add tests for new features

## Questions?

Open an issue on GitHub if you have questions or need help!
