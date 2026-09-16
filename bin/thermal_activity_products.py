from meteofetch import AromeOutreMerIndien
from aropangue.basic_thermodynamics import (
    get_virtual_temp,
    extend_elevation_by_dry_adiab
)
from aropangue.settings import DATA_DIR


if __name__ == "__main__":
    print("Getting AROME surface data")
    datasets = AromeOutreMerIndien.get_latest_forecast(
        paquet="SP2",
        variables=("mx2t", "sh2"),
        path=DATA_DIR
    )

    tv = get_virtual_temp(
        datasets["mx2t"],
        datasets["sh2"]
    )

    particle_tv = extend_elevation_by_dry_adiab(
        tv
    )

    print("Getting AROME 3D data") 
    datasets_3d = AromeOutreMerIndien.get_latest_forecast(
        paquet="HP1",
        path=DATA_DIR
    )