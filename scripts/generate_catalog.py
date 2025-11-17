#!/usr/bin/env python3
"""Generate catalog metadata and HTML page."""

import json
from datetime import datetime
from pathlib import Path

import xarray as xr


def generate_catalog() -> None:
    """Generate catalog metadata and HTML page."""
    catalog_dir = Path("catalog")
    catalog_dir.mkdir(parents=True, exist_ok=True)

    data_dir = Path("data")

    # Initialize catalog metadata
    catalog = {
        "title": "Alaska HRRR Data Catalog",
        "description": "High-Resolution Rapid Refresh (HRRR) forecast data for Alaska - Rolling 24-hour window",
        "generated": datetime.utcnow().isoformat() + "Z",
        "datasets": [],
    }

    # Find all zarr stores (timestamped directories)
    zarr_stores = sorted(data_dir.glob("hrrr_alaska_*.zarr"), reverse=True)

    if zarr_stores:
        # Process the most recent zarr store for metadata
        zarr_path = zarr_stores[0]
        try:
            ds = xr.open_zarr(zarr_path)

            # Extract metadata
            dataset_info = {
                "id": "noaa-hrrr-alaska-forecast",
                "title": str(ds.attrs.get("title", "NOAA HRRR Alaska Forecast")),
                "description": str(ds.attrs.get("description", "")),
                "provider": str(ds.attrs.get("provider", "NOAA")),
                "model": str(ds.attrs.get("model", "HRRR")),
                "variant": str(ds.attrs.get("variant", "alaska-forecast")),
                "dimensions": {k: int(v) for k, v in ds.dims.items()},
                "variables": list(ds.data_vars),
                "coordinates": list(ds.coords),
                "temporal_extent": {
                    "start": str(ds.init_time.min().values),
                    "end": str(ds.init_time.max().values),
                },
                "zarr_path": str(zarr_path),
                "forecast_cycles": len(zarr_stores),
                "available_forecasts": [str(p.name) for p in zarr_stores],
            }

            catalog["datasets"].append(dataset_info)
            ds.close()

        except Exception as e:
            print(f"Error reading Zarr store: {e}")
            dataset_info = {
                "id": "noaa-hrrr-alaska-forecast",
                "title": "NOAA HRRR Alaska Forecast",
                "status": "error",
                "error": str(e),
            }
            catalog["datasets"].append(dataset_info)

    # Write catalog JSON
    catalog_json_path = catalog_dir / "catalog.json"
    with open(catalog_json_path, "w") as f:
        json.dump(catalog, f, indent=2)

    print(f"Generated catalog JSON: {catalog_json_path}")

    # Generate HTML page
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{catalog['title']}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        header {{
            background: #1e3a8a;
            color: white;
            padding: 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }}
        h1 {{
            margin: 0;
            font-size: 2.5rem;
        }}
        .subtitle {{
            opacity: 0.9;
            margin-top: 0.5rem;
        }}
        .updated {{
            font-size: 0.875rem;
            opacity: 0.8;
            margin-top: 1rem;
        }}
        .dataset-card {{
            background: white;
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .dataset-title {{
            font-size: 1.5rem;
            color: #1e3a8a;
            margin-top: 0;
        }}
        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
        }}
        .metadata-item {{
            padding: 1rem;
            background: #f8fafc;
            border-radius: 4px;
        }}
        .metadata-label {{
            font-weight: 600;
            color: #64748b;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .metadata-value {{
            margin-top: 0.25rem;
            color: #1e293b;
            font-size: 1rem;
        }}
        .variables-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
        }}
        .variable-tag {{
            background: #e0e7ff;
            color: #3730a3;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.875rem;
            font-family: monospace;
        }}
        .error {{
            background: #fee;
            color: #c00;
            padding: 1rem;
            border-radius: 4px;
            border-left: 4px solid #c00;
        }}
        a {{
            color: #1e3a8a;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <header>
        <h1>{catalog['title']}</h1>
        <div class="subtitle">{catalog['description']}</div>
        <div class="updated">Last updated: {catalog['generated']}</div>
    </header>

    <main>
"""

    # Add dataset cards
    for dataset in catalog["datasets"]:
        if "error" in dataset:
            html_content += f"""
        <div class="dataset-card">
            <h2 class="dataset-title">{dataset['title']}</h2>
            <div class="error">
                Error loading dataset: {dataset['error']}
            </div>
        </div>
"""
        else:
            html_content += f"""
        <div class="dataset-card">
            <h2 class="dataset-title">{dataset['title']}</h2>
            <p>{dataset.get('description', 'No description available')}</p>

            <div class="metadata-grid">
                <div class="metadata-item">
                    <div class="metadata-label">Provider</div>
                    <div class="metadata-value">{dataset.get('provider', 'N/A')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Model</div>
                    <div class="metadata-value">{dataset.get('model', 'N/A')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Variant</div>
                    <div class="metadata-value">{dataset.get('variant', 'N/A')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Temporal Extent</div>
                    <div class="metadata-value">
                        {dataset.get('temporal_extent', {}).get('start', 'N/A')}<br>
                        to<br>
                        {dataset.get('temporal_extent', {}).get('end', 'N/A')}
                    </div>
                </div>
            </div>

            <h3>Dimensions</h3>
            <div class="metadata-grid">
"""
            for dim, size in dataset.get("dimensions", {}).items():
                html_content += f"""
                <div class="metadata-item">
                    <div class="metadata-label">{dim}</div>
                    <div class="metadata-value">{size}</div>
                </div>
"""
            html_content += """
            </div>

            <h3>Variables</h3>
            <div class="variables-list">
"""
            for var in dataset.get("variables", [])[:20]:  # Show first 20
                html_content += f"""
                <span class="variable-tag">{var}</span>
"""
            remaining = len(dataset.get("variables", [])) - 20
            if remaining > 0:
                html_content += f"""
                <span class="variable-tag">... and {remaining} more</span>
"""
            html_content += """
            </div>

            <div style="margin-top: 2rem;">
                <a href="catalog.json">View full catalog JSON</a> |
                <a href="https://github.com/andrewnakas/ak_hrrr_to_zarr">View on GitHub</a>
            </div>
        </div>
"""

    html_content += """
    </main>

    <footer style="text-align: center; margin-top: 3rem; padding: 2rem; color: #64748b;">
        <p>Generated automatically by <a href="https://github.com/andrewnakas/ak_hrrr_to_zarr">ak_hrrr_to_zarr</a></p>
        <p>Data source: <a href="https://registry.opendata.aws/noaa-hrrr-pds/">NOAA HRRR on AWS</a></p>
    </footer>
</body>
</html>
"""

    # Write HTML
    html_path = catalog_dir / "index.html"
    with open(html_path, "w") as f:
        f.write(html_content)

    print(f"Generated catalog HTML: {html_path}")


if __name__ == "__main__":
    generate_catalog()
