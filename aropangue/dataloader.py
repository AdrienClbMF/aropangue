from meteofetch import AromeOutreMerIndien
import xarray as xr
from datetime import datetime
from typing import Dict, Tuple
from .utils import clean_up_dir, list_available_model_arch
from .format import subset_grib_to_netcdf, DAT_FILENAME_FMT
from .settings import (
    DATA_DIR, 
    PACKETS_TO_RETRIEVE, 
    REUNION_BBOX,
    PARAGLIDING_SITES
)

def load_last_run(remove_previous_data:bool = True):

    if remove_previous_data :
        print("Cleaning up the DATA directory...")
        clean_up_dir()

    datasets = {}
    for pk_name in PACKETS_TO_RETRIEVE:
        print(f"Getting {pk_name} AROME data")
        datasets.update(
            AromeOutreMerIndien.get_latest_forecast(
                paquet=pk_name,
                path=DATA_DIR
            )
        )

        grb_files = list_available_model_arch(arch_type='grib2')
        print(f"Subsetting {len(grb_files)} grib2 files...")
        for grb_p in grb_files.path :
            try :
                subset_grib_to_netcdf(
                grb_p, 
                bbox=REUNION_BBOX,
                model=AromeOutreMerIndien)
            except Exception as e:
                print(f'{grb_p} could not be susbetted : {e}')

def load_model_run(
    packet_name: str,
    run_date: datetime,
    model_name: str = "arome-om-INDIEN__0025",
    as_poi_subset: bool = True,
    poi: Dict[str, Tuple[float, float]] = PARAGLIDING_SITES,
):
    archives_glob = (
        f"{model_name}__{packet_name}__*H__"
        f"{run_date.strftime(DAT_FILENAME_FMT)}.nc"
    )
    print(f"Opening files {archives_glob}")

    ds = xr.open_mfdataset(
        str(DATA_DIR / archives_glob),
        combine="nested",
        concat_dim="time",
    )

    if not as_poi_subset:
        return ds

    point_ds = []

    for name, (lat, lon) in poi.items():
        ds_point = ds.sel(
            latitude=lat,
            longitude=lon,
            method="nearest",
        )

        point_lat = float(ds_point["latitude"].item())
        point_lon = float(ds_point["longitude"].item())

        ds_point = ds_point.expand_dims(point=[name]).assign_coords(
            latitude=("point", [point_lat]),
            longitude=("point", [point_lon]),
        )

        point_ds.append(ds_point)

    return xr.concat(point_ds, dim="point")