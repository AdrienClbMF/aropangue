import pandas as pd
from typing import Literal
from .settings import DATA_DIR
from .format import parse_arch_filename

def list_available_model_arch(
        arch_type:Literal['grib2', 'nc'] = 'grib2'
) -> pd.DataFrame :
    available_gribs = list(DATA_DIR.glob(f"*.{arch_type}"))

    if len(available_gribs) > 0 :
        grib_params = [
            {
                **parse_arch_filename(grb_path, suffix=arch_type),
                "path": grb_path,
            }
            for grb_path in available_gribs
        ]

        return (
            pd.DataFrame(grib_params)
            .sort_values("dat")
            .reset_index(drop=True)
        )
    else : 
        return pd.DataFrame()