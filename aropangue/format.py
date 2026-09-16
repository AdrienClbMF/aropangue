from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict

DAT_FILENAME_FMT = "%Y-%m-%dT%H-%M-%SZ"

def parse_grb_filename(grb_path:Path) -> Dict[str, str] :
    params = grb_path.name.removesuffix(".grib2").split("__")
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
