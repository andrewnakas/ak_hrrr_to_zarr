# Alaska HRRR GRIB2 File Metadata Summary

## File Information
- **File**: `hrrr.t00z.wrfsfcf00.ak.grib2`
- **Date Downloaded**: 2024-11-13 00Z cycle
- **File Size**: ~80.3 MB
- **Total Messages/Variables**: 169
- **Data Source**: NOAA HRRR Big Data Project (AWS S3)

## 1. Grid Specifications

### Grid Dimensions
- **X dimension (west-east)**: 1,299 points
- **Y dimension (south-north)**: 919 points
- **Total grid points**: 1,193,781

### Grid Spacing
- **Dx**: 3,000 meters (3.0 km)
- **Dy**: 3,000 meters (3.0 km)
- **Resolution**: 3 km uniform horizontal resolution

## 2. Projection Parameters

### Polar Stereographic Projection
- **Grid Type**: `polar_stereographic`
- **Projection Center**: North Pole (flag = 0)
- **Orientation (LoV)**: 225.0° (central meridian)
- **Standard Parallel (LaD)**: 60.0° (latitude where Dx/Dy are specified)

### First Grid Point
- **Latitude**: 41.612949°
- **Longitude**: 185.117126° (or -174.882874° W)

### Earth Shape
- **Model**: Spherical (code 6)
- **Earth Radius**: 6,371,229 meters (6,371.229 km)

### Scanning Mode
- **i scans negatively**: False (scans in positive i direction)
- **j scans positively**: True (scans in positive j direction)
- **j points consecutive**: False (i direction is consecutive in memory)

## 3. Coordinate Information

### Latitude Coverage
- **Range**: 41.6129° N to 77.0929° N
- **Extent**: Covers Alaska and surrounding regions

### Longitude Coverage
- **Range**: 156.4368° E to 244.2243° E (or -115.7757° W to -203.5632° W adjusted)
- **Extent**: Covers Alaska, western Canada, and adjacent ocean areas

## 4. Available Variables

### Variable Categories (by Level Type)

#### Surface Variables (45 variables)
Key surface variables include:
- **Temperature & Moisture**: `t` (temperature), `2t` (2m temperature), `2d` (2m dewpoint), `2r` (2m RH), `2sh` (2m specific humidity)
- **Pressure**: `sp` (surface pressure)
- **Wind**: `10u`, `10v` (10m wind components), `gust` (wind gust)
- **Precipitation**: `tp` (total precipitation), `prate` (precipitation rate), `crain`, `csnow`, `cfrzr`, `cicep` (categorical precip types)
- **Radiation**: `sdswrf`, `sdlwrf` (downward SW/LW flux), `suswrf`, `sulwrf` (upward SW/LW flux)
- **Land Surface**: `orog` (orography), `lsm` (land-sea mask), `sde` (snow depth), `snowc` (snow cover), `veg` (vegetation), `lai` (leaf area index)
- **Fluxes**: `ishf` (sensible heat flux), `slhtf` (latent heat flux), `gflux` (ground heat flux)
- **Other**: `vis` (visibility), `blh` (boundary layer height), `cape`, `cin`, `hail`

#### Isobaric Levels (1000, 925, 850, 700, 500, 400, 300, 250 hPa)
Variables at pressure levels (34 variables):
- `gh` (geopotential height)
- `t` (temperature)
- `dpt` (dewpoint temperature)
- `u`, `v` (wind components)
- `wz` (vertical velocity, at 700 hPa)

#### Height Above Ground Levels
Variables at various heights (2m, 10m, 80m, 1000m, 4000m):
- **2 meters**: `2t`, `2d`, `2r`, `2sh`, `pt`
- **10 meters**: `10u`, `10v`, `max_10si` (max 10m wind speed)
- **80 meters**: `u`, `v`
- **1000m, 4000m**: `refd` (derived radar reflectivity)

#### Atmospheric Column Variables
- `refc` (composite radar reflectivity)
- `ltng` (lightning)
- `tcc` (total cloud cover)
- `veril` (vertically-integrated liquid)
- `pwat` (precipitable water)
- `hail`

#### Cloud Variables
- Cloud base: `gh`, `pcdb` (pressure at cloud base)
- Cloud top: `gh`, `pres` (pressure)
- Cloud ceiling: `gh`
- Cloud layers: `lcc` (low), `mcc` (medium), `hcc` (high), `tcc` (total), `boundaryLayerCloudLayer`

#### Convection Variables (pressure from ground layers)
- `cape` (Convective Available Potential Energy) at 9000, 18000, 25500 Pa
- `cin` (Convective Inhibition) at 9000, 18000, 25500 Pa
- `4lftx` (4-layer lifted index) at 18000 Pa
- `lftx` (surface lifted index) at 500 hPa layer

#### Specialized Variables
- Storm motion: `ustm`, `vstm` (U/V components)
- Wind shear: `vucsh`, `vvcsh` (vertical U/V shear)
- Helicity: `hlcy` (storm relative helicity) at 1000m, 3000m layers
- Vorticity: `max_vo` (max relative vorticity) at 1000m, 2000m layers
- Isothermal levels (253K, 263K): `gh`, `refd`
- Freezing levels: `gh`, `pres`, `r` (RH) at isotherm zero and highest tropospheric freezing
- Satellite products: `SBT113`, `SBT114`, `SBT123`, `SBT124` (simulated brightness temperatures)

## 5. Data Characteristics

### Time Information
- **Forecast Reference Time**: Based on file name - 00Z cycle
- **Forecast Hour**: f00 (analysis/0-hour forecast)
- **Step Types**: instant, max, accum (accumulated), avg

### GRIB Edition
- **Edition**: GRIB2
- **Center**: KWBC (US National Weather Service - NCEP)
- **Sub-Center**: 0

## 6. Key Specifications for Data Processing

### For Zarr Conversion
```python
grid_config = {
    "projection": "polar_stereographic",
    "grid_mapping_name": "polar_stereographic",
    "straight_vertical_longitude_from_pole": 225.0,  # LoV
    "latitude_of_projection_origin": 90.0,  # North Pole
    "standard_parallel": 60.0,  # LaD
    "false_easting": 0.0,
    "false_northing": 0.0,
    "earth_radius": 6371229.0,

    "dimensions": {
        "x": 1299,
        "y": 919
    },

    "grid_spacing": {
        "dx": 3000.0,
        "dy": 3000.0
    },

    "first_grid_point": {
        "lat": 41.612949,
        "lon": 185.117126  # or -174.882874 W
    },

    "coordinate_range": {
        "lat_min": 41.6129,
        "lat_max": 77.0929,
        "lon_min": 156.4368,
        "lon_max": 244.2243
    }
}
```

### CF-Conventions Compliance
- The data follows CF-1.7 conventions
- Variable names use CF standard names where available
- Projection information can be encoded as CF grid mapping

## 7. Unique Characteristics of Alaska HRRR

1. **Different grid from CONUS HRRR**: Alaska HRRR uses a different polar stereographic projection optimized for Alaska
2. **3 km resolution**: Same as CONUS HRRR
3. **Polar stereographic centered on North Pole**: Unlike CONUS which uses Lambert Conformal
4. **Smaller domain**: ~1.2M grid points vs ~1.9M for CONUS HRRR
5. **Similar variable set**: Contains most of the same variables as CONUS HRRR

## 8. Notes for Data Catalog Development

- **Chunking Strategy**: Consider chunking by time and spatial tiles (e.g., 100x100 or 200x200 grid points)
- **Variable Grouping**: May want to separate by level type (surface, isobaric, etc.) for efficient access
- **Coordinate Variables**: Latitude and longitude are 2D arrays (919 x 1299) due to projection
- **Missing Values**: GRIB missing value = 3.4028234663852886e+38
- **Unknown Variables**: File contains several "unknown" variables (param_id = 0) which may need manual identification

## File Locations

- **Downloaded GRIB2 file**: `/home/user/ak_hrrr_to_zarr/hrrr.t00z.wrfsfcf00.ak.grib2`
- **Metadata JSON**: `/home/user/ak_hrrr_to_zarr/alaska_hrrr_metadata.json`
- **This Summary**: `/home/user/ak_hrrr_to_zarr/ALASKA_HRRR_METADATA_SUMMARY.md`
