import pandas as pd
from .settings import DATA_DIR
from .format import parse_grb_filename

def list_available_gribs() -> pd.DataFrame :
    available_gribs = list(DATA_DIR.glob("*.grib2"))

    grib_params = [
        {
            **parse_grb_filename(grb_path),
            "path": grb_path,
        }
        for grb_path in available_gribs
    ]

    return (
        pd.DataFrame(grib_params)
        .sort_values("dat")
        .reset_index(drop=True)
    )