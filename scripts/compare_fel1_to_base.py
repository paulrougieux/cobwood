"""Compare output where the fuel wood elasticity was set to one to the base model
"""

import sys
from cobwood.gfpmx import GFPMX
from biotrade.faostat import faostat
import cobwood

# Load CBM output data
from eu_cbm_hat import eu_cbm_data_pathlib

scenario_dir = (
    eu_cbm_data_pathlib.parent / "eu_cbm_explore" / "scenarios" / "ssp2_fair_degrowth"
)
# Load data and plotting functions from the prepare script in the same directory
sys.path.append(str(scenario_dir))


hwp_dir = cobwood.data_dir / "gfpmx_output" / "hwp"
hwp_dir.mkdir(exist_ok=True)

eu_countries = faostat.country_groups.eu_country_names
eu_countries += ["Netherlands"]

# Load output data, after a run has already been completed
gfpmx_pikssp2_fel1 = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario_name="pikssp2_fel1"
)
gfpmx_pikssp2_base = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario_name="pikssp2"
)


# Comparison of EU fuelwood consumption and production

gfpmx_pikssp2_base["fuel"]["cons"]


# Comparison of total roundwood consumption and production
# Including fuelwood and industrial roundwood
