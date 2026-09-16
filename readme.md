# AROPANGUE

Tooling for processing and analysing weather forecast data, with a focus on
Arome Outre-Mer Indien (AOMEI) products and basic thermodynamics.

## Features

- Fetch latest AROME forecast products via `meteofetch`
- Parse GRIB2 filenames into structured metadata (`aropangue/format.py`)
- Basic thermodynamic calculations (`aropangue/basic_thermodynamics.py`):
  - Virtual temperature from temperature and specific humidity
  - Dry-adiabatic extension of surface temperature to elevation profiles
- Thermal activity product generation (`bin/thermal_activity_products.py`)

## Installation

The project uses Conda with the environment defined in `environment.yaml`:

```bash
conda env create -f environment.yaml
conda activate aropang_env
```

## Usage

Run the thermal activity product script:

```bash
python bin/thermal_activity_products.py
```

## Layout

```
aropangue/    Core package (settings, format, utils, thermodynamics)
bin/          Executable scripts
data/         Downloaded forecast data (GRIB2)
notebooks/    Exploratory notebooks
```

## License

TBD.
