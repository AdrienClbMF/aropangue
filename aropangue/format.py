from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Literal
from meteofetch import AromeOutreMerIndien

DAT_FILENAME_FMT = "%Y-%m-%dT%H-%M-%SZ"

def parse_arch_filename(grb_path:Path, suffix: Literal['grib2', 'nc'] = 'grib2') -> Dict[str, str] :
    params = grb_path.name.removesuffix(f".{suffix}").split("__")
    keys = [
        "model_name",
        "resol",
        "package_name",
        "leadtime",
        "dat"
    ]

    fn_params = dict(zip(keys, params))

    fn_params['run_dat'] = datetime.strptime(fn_params['dat'], DAT_FILENAME_FMT)
    fn_params['leadtime'] = timedelta(hours=int(fn_params['leadtime'].removesuffix("H")))
    fn_params['dat'] = fn_params['run_dat'] +  fn_params['leadtime']
    return fn_params



def subset_grib_to_netcdf(
    grib_path: str | Path,
    bbox: tuple[float, float, float, float],
    model: AromeOutreMerIndien
) -> Path:
    """
    Subset a GRIB file to a bounding box, save as NetCDF, and remove
    the original GRIB after successful writing.

    Parameters
    ----------
    grib_path : str or Path
        Input GRIB2 file.
    bbox : tuple
        Bounding box as (lon_min, lon_max, lat_min, lat_max).

    Returns
    -------
    Path
        Path to the resulting NetCDF file.
    """
    grib_path = Path(grib_path)
    output_path = grib_path.with_suffix(".nc")

    lon_min, lon_max, lat_min, lat_max = bbox

    ds = model._read_grib(grib_path)[0]

    # Latitude is decreasing in the AROME grid
    ds = ds.sel(
        longitude=slice(lon_min, lon_max),
        latitude=slice(lat_max, lat_min),
    )

    try:
        ds.to_netcdf(output_path)
    except Exception:
        # Do not remove the original GRIB if writing failed
        raise
    else:
        grib_path.unlink()

    return output_path