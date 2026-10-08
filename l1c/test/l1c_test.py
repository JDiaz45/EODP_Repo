from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset

from common.io.readGeodetic import readGeodetic


# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------

root = Path.home() / "EODP_TER_2021" / "EODP-TS-L1C"

gm_dir = root / "input" / "gm_alt100_act_150"
l1c_file = root / "myoutput" / "l1c_toa_VNIR-0.nc"

fig_dir = Path.home() / "EODP" / "l1c" / "test" / "figures"
fig_dir.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# Read L1B geolocation
# ------------------------------------------------------------------

lat_l1b, lon_l1b = readGeodetic(
    str(gm_dir),
    "geolocation.nc"
)


# ------------------------------------------------------------------
# Read L1C coordinates
# ------------------------------------------------------------------

def get_variable(ds, candidates):

    for candidate in candidates:
        if candidate in ds.variables:
            return np.asarray(
                ds.variables[candidate][:],
                dtype=float
            ).ravel()

    for name in ds.variables:
        low = name.lower()

        if any(candidate in low for candidate in candidates):
            return np.asarray(
                ds.variables[name][:],
                dtype=float
            ).ravel()

    raise KeyError(
        f"Variable not found. Available variables: "
        f"{list(ds.variables.keys())}"
    )


with Dataset(l1c_file) as ds:

    lat_l1c = get_variable(
        ds,
        ["lat", "latitude"]
    )

    lon_l1c = get_variable(
        ds,
        ["lon", "longitude"]
    )


# ==================================================================
# PLOT 1: L1B grid vs L1C grid
# ==================================================================

plt.figure(figsize=(10, 8))

# L1B grid - red
plt.scatter(
    lon_l1b.ravel(),
    lat_l1b.ravel(),
    s=3,
    c="red",
    label="L1B grid"
)

# L1C grid - blue
plt.scatter(
    lon_l1c,
    lat_l1c,
    s=5,
    c="blue",
    label="L1C MGRS grid"
)

plt.xlabel("Longitude [deg]")
plt.ylabel("Latitude [deg]")
plt.title("L1B grid vs L1C MGRS grid")
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.savefig(
    fig_dir / "l1b_vs_l1c_grid.png",
    dpi=200
)

plt.close()


# ------------------------------------------------------------------
# Haversine function
# ------------------------------------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    """
    Distance between two geographic coordinates [m]
    """

    R = 6371000.0  # Earth radius [m]

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2.0) ** 2
    )

    c = 2.0 * np.arctan2(
        np.sqrt(a),
        np.sqrt(1.0 - a)
    )

    return R * c


# ==================================================================
# PLOT 2: Spatial Sampling Distance - central L1B row
# ==================================================================

# Central ALT row
central_row = lat_l1b.shape[0] // 2

lat_central = lat_l1b[central_row, :]
lon_central = lon_l1b[central_row, :]

# Distance between consecutive ACT pixels
ssd_act = haversine(
    lat_central[:-1],
    lon_central[:-1],
    lat_central[1:],
    lon_central[1:]
)

act_pixel = np.arange(len(ssd_act))


plt.figure(figsize=(10, 6))

plt.plot(
    act_pixel,
    ssd_act
)

plt.axhline(
    np.mean(ssd_act),
    linestyle="--",
    label=f"Mean SSD = {np.mean(ssd_act):.2f} m"
)

plt.xlabel("ACT pixel")
plt.ylabel("Spatial Sampling Distance [m]")
plt.title(
    f"L1B Spatial Sampling Distance - central row {central_row}"
)

plt.grid(True)
plt.legend()
plt.tight_layout()

plt.savefig(
    fig_dir / "l1b_ssd_central_row.png",
    dpi=200
)

plt.close()


# ==================================================================
# PLOT 3: Spatial Sampling Distance versus latitude
# ==================================================================

# Central ACT column
central_col = lat_l1b.shape[1] // 2

lat_column = lat_l1b[:, central_col]
lon_column = lon_l1b[:, central_col]

# Distance between consecutive ALT pixels
ssd_alt = haversine(
    lat_column[:-1],
    lon_column[:-1],
    lat_column[1:],
    lon_column[1:]
)

# Latitude associated with each distance:
# midpoint between two consecutive pixels
latitude_mid = (
    lat_column[:-1] + lat_column[1:]
) / 2.0


plt.figure(figsize=(10, 6))

plt.plot(
    latitude_mid,
    ssd_alt,
    marker="."
)

plt.axhline(
    np.mean(ssd_alt),
    linestyle="--",
    label=f"Mean SSD = {np.mean(ssd_alt):.2f} m"
)

plt.xlabel("Latitude [deg]")
plt.ylabel("Spatial Sampling Distance [m]")
plt.title(
    "L1B Spatial Sampling Distance versus Latitude"
)

plt.grid(True)
plt.legend()
plt.tight_layout()

plt.savefig(
    fig_dir / "l1b_ssd_vs_latitude.png",
    dpi=200
)

plt.close()


# ------------------------------------------------------------------
# Numerical sanity checks
# ------------------------------------------------------------------

print("L1B grid shape:", lat_l1b.shape)
print("L1C points:", len(lat_l1c))

print()
print("Central L1B row:", central_row)
print("ACT SSD minimum [m]:", np.min(ssd_act))
print("ACT SSD maximum [m]:", np.max(ssd_act))
print("ACT SSD mean    [m]:", np.mean(ssd_act))

print()
print("Central ACT column:", central_col)
print("ALT SSD minimum [m]:", np.min(ssd_alt))
print("ALT SSD maximum [m]:", np.max(ssd_alt))
print("ALT SSD mean    [m]:", np.mean(ssd_alt))

print()
print("Saved figures:")
print(fig_dir / "l1b_vs_l1c_grid.png")
print(fig_dir / "l1b_ssd_central_row.png")
print(fig_dir / "l1b_ssd_vs_latitude.png")