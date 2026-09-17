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
        dims="heightAboveGround",
        coords={"heightAboveGround": elevations},
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

    return dry_adiabatic_temp.metpy.quantify()



def add_specific_and_virtual_temperature(datasets_3d):
    """Compute specific humidity and virtual temperature 
    from RH, T and pressure."""
    e_s = mpcalc.saturation_vapor_pressure(datasets_3d["t"])
    e = datasets_3d["r"] / 100 * e_s

    mixing_ratio = mpcalc.mixing_ratio(
        e,
        datasets_3d["pres"],
    )

    datasets_3d["q"] = mpcalc.specific_humidity_from_mixing_ratio(
        mixing_ratio
    )

    datasets_3d["Tv"] = mpcalc.virtual_temperature(
        datasets_3d["t"],
        datasets_3d["q"],
    )

    return datasets_3d

def get_lcl_ceiling(datasets_surf) :
    lcl_pressure, _ = mpcalc.lcl(
        datasets_surf['sp'], 
        datasets_surf['t'], 
        datasets_surf['d2m'])
    
    return mpcalc.pressure_to_height_std(lcl_pressure).to("m")