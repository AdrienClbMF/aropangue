from typing import List
import numpy as np
import xarray as xr
import pint
import metpy.calc as mpcalc
from metpy.units import units

def get_virtual_temp(temp: xr.DataArray, q: xr.DataArray) -> xr.DataArray:
    print("Quantifying units for metpy use")
    temp = temp.metpy.quantify()
    q = q.metpy.quantify()

    return mpcalc.virtual_temperature(temp, q)

def extend_elevation_by_dry_adiab(
    surface_temp_da: xr.DataArray,
    elevations: List[float] = [0, 500, 1000, 1500, 2000, 3000],
    elevation_units: pint.Unit = units.meter,
) -> xr.DataArray:
    temp_da = surface_temp_da.metpy.quantify()

    elevation_da = xr.DataArray(
        np.array(elevations) * elevation_units,
        dims="elevation",
        coords={"elevation": elevations},
    )

    # zeros_like sur le DataArray NON quantifié -> pas d'unité de température héritée
    ground_elevation = xr.zeros_like(surface_temp_da, dtype=float) * elevation_units
    ground_pressure = mpcalc.height_to_pressure_std(ground_elevation)

    pressure_at_level = mpcalc.height_to_pressure_std(elevation_da)

    dry_adiabatic_temp = mpcalc.dry_lapse(
        pressure_at_level,   # dim: elevation
        temp_da,             # dims: time, lat, lon
        ground_pressure,     # dims: time, lat, lon
    )

    dry_adiabatic_temp = dry_adiabatic_temp.metpy.dequantify()
    dry_adiabatic_temp.name = "temp_dry_adiabatic"

    return dry_adiabatic_temp