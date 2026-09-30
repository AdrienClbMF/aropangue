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

def get_lcl_height(ds_surf, temp_key: str = 't'):
    """LCL height above ground (m) from surface pressure, T2m and Td2m."""
    p  = ds_surf["sp"].metpy.quantify()
    t  = ds_surf[temp_key].metpy.quantify()
    td = ds_surf["d2m"].metpy.quantify()

    p_lcl, _ = mpcalc.lcl(p, t, td)

    # Standard-atmosphere height difference between the surface and the LCL
    # -> height above ground, independent of station elevation
    h_lcl = mpcalc.pressure_to_height_std(p_lcl) - mpcalc.pressure_to_height_std(p)

    return h_lcl.metpy.convert_units("m").metpy.dequantify().rename("lcl_height")


def get_ccl_height(ds):
    """CCL height above ground (m) for each valid_time."""
    ds = ds.swap_dims({"time": "valid_time"}).squeeze("point", drop=True).load()
    # dims are now (valid_time, heightAboveGround)

    T  = ds["t"].metpy.quantify()
    rh = ds["r"].clip(min=1e-3, max=100).metpy.quantify()
    p  = ds["pres"].metpy.quantify()
    Td = mpcalc.dewpoint_from_relative_humidity(T, rh)

    z = ds["heightAboveGround"].values
    out = np.full(ds.sizes["valid_time"], np.nan)

    for i in range(ds.sizes["valid_time"]):
        pi  = p.isel(valid_time=i).metpy.unit_array
        Ti  = T.isel(valid_time=i).metpy.unit_array
        Tdi = Td.isel(valid_time=i).metpy.unit_array

        if any(np.isnan(x.magnitude).any() for x in (pi, Ti, Tdi)):
            continue  # e.g. first time step is all NaN

        try:
            p_ccl, _, _ = mpcalc.ccl(pi, Ti, Tdi)
        except Exception:
            continue  # no CCL found in this profile
        if np.isnan(p_ccl.magnitude):
            continue

        lp = np.log(pi.to("hPa").magnitude)          # decreasing with height
        out[i] = np.interp(np.log(p_ccl.to("hPa").magnitude), lp[::-1], z[::-1])

    return xr.DataArray(
        out,
        coords={"valid_time": ds["valid_time"]},
        dims="valid_time",
        name="ccl_height",
        attrs={"units": "m", "long_name": "CCL height above ground"},
    )
