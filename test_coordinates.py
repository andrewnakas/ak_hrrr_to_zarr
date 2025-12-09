#!/usr/bin/env python3
"""Test script to verify Alaska HRRR coordinate transformation."""

import numpy as np
import pyproj

# Alaska HRRR projection parameters (from GRIB metadata)
proj = pyproj.Proj(
    proj="stere",
    lat_0=90.0,  # North Pole
    lon_0=225.0,  # -135 degrees
    lat_ts=60.0,  # Standard parallel
    x_0=0.0,
    y_0=0.0,
    R=6371229.0,  # Earth radius in meters
)

# First grid point from GRIB metadata
first_lon = 185.117126 - 360.0  # Convert to -180 to 180 range = -174.882874
first_lat = 41.612949

print("Alaska HRRR Grid Verification")
print("=" * 60)
print(f"\nFirst grid point (from GRIB):")
print(f"  Lat: {first_lat:.6f}°N")
print(f"  Lon: {first_lon:.6f}°W")

# Convert first grid point to projection coordinates
x_first, y_first = proj(first_lon, first_lat)
print(f"\nProjection coordinates of first grid point:")
print(f"  X: {x_first:.2f} m")
print(f"  Y: {y_first:.2f} m")

# Create x/y arrays
nx, ny = 1299, 919
dx, dy = 3000.0, 3000.0

x = x_first + np.arange(nx) * dx
y = y_first + np.arange(ny) * dy

print(f"\nX coordinate range:")
print(f"  Min: {x.min():.2f} m")
print(f"  Max: {x.max():.2f} m")

print(f"\nY coordinate range:")
print(f"  Min: {y.min():.2f} m")
print(f"  Max: {y.max():.2f} m")

# Create meshgrid and transform to lat/lon
xx, yy = np.meshgrid(x, y, indexing='xy')
lon, lat = proj(xx, yy, inverse=True)

print(f"\n" + "=" * 60)
print("Transformed Latitude/Longitude Grid:")
print("=" * 60)

print(f"\nLatitude range:")
print(f"  Min: {lat.min():.2f}°N")
print(f"  Max: {lat.max():.2f}°N")
print(f"  Expected for Alaska: ~40-72°N")

print(f"\nLongitude range:")
print(f"  Min: {lon.min():.2f}°")
print(f"  Max: {lon.max():.2f}°")
print(f"  Expected for Alaska: ~-180 to -130°W")

# Test specific corners
print(f"\n" + "=" * 60)
print("Grid Corners:")
print("=" * 60)
print(f"\nSouthwest corner [0, 0]:")
print(f"  Lat: {lat[0, 0]:.2f}°N, Lon: {lon[0, 0]:.2f}°")

print(f"\nSoutheast corner [0, {nx-1}]:")
print(f"  Lat: {lat[0, nx-1]:.2f}°N, Lon: {lon[0, nx-1]:.2f}°")

print(f"\nNorthwest corner [{ny-1}, 0]:")
print(f"  Lat: {lat[ny-1, 0]:.2f}°N, Lon: {lon[ny-1, 0]:.2f}°")

print(f"\nNortheast corner [{ny-1}, {nx-1}]:")
print(f"  Lat: {lat[ny-1, nx-1]:.2f}°N, Lon: {lon[ny-1, nx-1]:.2f}°")

# Test a known Alaska location
print(f"\n" + "=" * 60)
print("Location Lookup Test:")
print("=" * 60)

# Anchorage: 61.2181°N, 149.9003°W
anchorage_lat, anchorage_lon = 61.2181, -149.9003
anc_x, anc_y = proj(anchorage_lon, anchorage_lat)

# Find closest grid point
x_idx = np.argmin(np.abs(x - anc_x))
y_idx = np.argmin(np.abs(y - anc_y))

closest_lat = lat[y_idx, x_idx]
closest_lon = lon[y_idx, x_idx]

print(f"\nAnchorage, AK:")
print(f"  Actual: {anchorage_lat:.4f}°N, {anchorage_lon:.4f}°W")
print(f"  Closest grid point [{y_idx}, {x_idx}]:")
print(f"    Lat: {closest_lat:.4f}°N, Lon: {closest_lon:.4f}°W")

distance = np.sqrt((closest_lat - anchorage_lat)**2 + (closest_lon - anchorage_lon)**2)
print(f"  Distance: {distance:.4f}° (~{distance * 111:.1f} km)")

if distance < 0.05:  # Within ~5.5 km
    print(f"  ✅ PASS: Grid point is close to Anchorage")
else:
    print(f"  ❌ FAIL: Grid point is too far from Anchorage")

print(f"\n" + "=" * 60)
