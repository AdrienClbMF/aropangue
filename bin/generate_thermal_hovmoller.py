from matplotlib import pyplot as plt
from datetime import datetime
from aropangue.dataloader import load_model_run
from aropangue.basic_thermodynamics import (
    get_virtual_temp,
    extend_elevation_by_dry_adiab,
    add_specific_and_virtual_temperature, 
    get_lcl_height,
    get_ccl_height
)
from aropangue.plots import plot_tv_difference_hovmoller
from aropangue.settings import PARAGLIDING_SITES


PRINT_DS_INFO = False
run_date = datetime(2026,9,30,0)

if __name__ == "__main__":

    ds_surf = load_model_run(
        "SP2",
        run_date,
        as_poi_subset=True,
        poi=PARAGLIDING_SITES
    )

    ds_3d = load_model_run(
        "HP1",
        run_date,
        as_poi_subset=True,
        poi=PARAGLIDING_SITES
    )

    elevations = ds_3d['t'].coords["heightAboveGround"].values
    
    print("compute diags")

    ds_surf["Tv"] = get_virtual_temp(ds_surf["mx2t"], ds_surf["sh2"])
    lcl = get_lcl_height(ds_surf)
    lcl_mxt = get_lcl_height(ds_surf, temp_key='mx2t')
    ccl = get_ccl_height(ds_3d)
    particle_tv = extend_elevation_by_dry_adiab(
        ds_surf["Tv"], 
        elevations=elevations)

    ds_3d = add_specific_and_virtual_temperature(ds_3d)
    ds_3d["Tv"] =  ds_3d["Tv"].metpy.quantify()




    tv_diff = - (ds_3d["Tv"].compute() - particle_tv.compute())
    u = ds_3d["u"]
    v = ds_3d["v"]

    point='Colimacons'
    fig, ax = plot_tv_difference_hovmoller(
        tv_diff.sel(point=point), 
        u.sel(point=point), 
        v.sel(point=point), 
        add_windbarbs=True,
        pointname='Colimacons')
    plt.savefig(f'../figures/{run_date.isoformat()}_thermal_hovmollers.png')