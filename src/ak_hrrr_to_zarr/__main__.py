"""CLI entry point for Alaska HRRR to Zarr."""

from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ak_hrrr_to_zarr.noaa.hrrr_alaska.forecast import AlaskaHrrrForecastDataset

app = typer.Typer(
    name="ak-hrrr",
    help="Alaska HRRR to Zarr data reformatter",
    add_completion=False,
)
console = Console()


# Registry of available datasets
DATASETS = {
    "noaa-hrrr-alaska-forecast": AlaskaHrrrForecastDataset,
}


@app.command()
def list_datasets() -> None:
    """List available datasets."""
    table = Table(title="Available Datasets")
    table.add_column("ID", style="cyan")
    table.add_column("Description", style="green")

    for dataset_id, dataset_class in DATASETS.items():
        dataset = dataset_class()
        attrs = dataset.template_config.dataset_attributes
        table.add_row(dataset_id, attrs.description)

    console.print(table)


@app.command()
def update_template(
    dataset_id: str = typer.Argument(..., help="Dataset ID"),
    output_dir: Path = typer.Option(
        Path("./templates"),
        "--output",
        "-o",
        help="Output directory for templates",
    ),
) -> None:
    """Update the template for a dataset."""
    if dataset_id not in DATASETS:
        rprint(f"[red]Error: Dataset {dataset_id} not found[/red]")
        rprint(f"Available datasets: {', '.join(DATASETS.keys())}")
        raise typer.Exit(1)

    rprint(f"[cyan]Updating template for {dataset_id}...[/cyan]")

    dataset = DATASETS[dataset_id]()
    template_config = dataset.template_config

    # Create template
    from datetime import datetime, timedelta

    end_time = datetime.utcnow() + timedelta(days=7)  # Template extends 7 days into future
    template_ds = template_config.get_template(end_time)

    # Save template
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{dataset_id}.zarr"

    rprint(f"[cyan]Saving template to {output_path}...[/cyan]")
    template_ds.to_zarr(output_path, mode="w")

    rprint(f"[green]✓ Template updated successfully[/green]")
    rprint(f"  Dataset: {template_config.dataset_attributes.title}")
    rprint(f"  Dimensions: {template_ds.dims}")
    rprint(f"  Variables: {list(template_ds.data_vars)}")


@app.command()
def operational_update(
    dataset_id: str = typer.Argument(..., help="Dataset ID"),
    output_path: Path = typer.Option(
        Path("./data/hrrr_alaska.zarr"),
        "--output",
        "-o",
        help="Output Zarr store path",
    ),
) -> None:
    """Run operational update for a dataset."""
    if dataset_id not in DATASETS:
        rprint(f"[red]Error: Dataset {dataset_id} not found[/red]")
        rprint(f"Available datasets: {', '.join(DATASETS.keys())}")
        raise typer.Exit(1)

    rprint(f"[cyan]Running operational update for {dataset_id}...[/cyan]")

    dataset = DATASETS[dataset_id]()

    try:
        dataset.operational_update(output_path)
        rprint(f"[green]✓ Operational update completed successfully[/green]")
        rprint(f"  Output: {output_path}")
    except Exception as e:
        rprint(f"[red]✗ Operational update failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def info(
    dataset_id: str = typer.Argument(..., help="Dataset ID"),
) -> None:
    """Show information about a dataset."""
    if dataset_id not in DATASETS:
        rprint(f"[red]Error: Dataset {dataset_id} not found[/red]")
        rprint(f"Available datasets: {', '.join(DATASETS.keys())}")
        raise typer.Exit(1)

    dataset = DATASETS[dataset_id]()
    template_config = dataset.template_config
    attrs = template_config.dataset_attributes

    rprint(f"\n[bold cyan]{attrs.title}[/bold cyan]")
    rprint(f"[dim]{attrs.description}[/dim]\n")

    table = Table(show_header=False, box=None)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("ID", attrs.id)
    table.add_row("Provider", attrs.provider)
    table.add_row("Model", attrs.model)
    table.add_row("Variant", attrs.variant)
    table.add_row("Version", attrs.version)
    table.add_row("Dimensions", str(template_config.dimensions))
    table.add_row("Append dimension", template_config.append_dim)
    table.add_row("Update frequency", template_config.append_dim_freq)
    table.add_row("Variables", str(len(template_config.data_vars)))

    console.print(table)

    rprint("\n[bold]Available variables:[/bold]")
    for var in template_config.data_vars[:5]:  # Show first 5
        rprint(f"  • {var.name}: {var.long_name} ({var.units})")
    if len(template_config.data_vars) > 5:
        rprint(f"  ... and {len(template_config.data_vars) - 5} more")


if __name__ == "__main__":
    app()
