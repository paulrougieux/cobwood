""" Extract data to compute the Harvested Wood Products Sink

- Load GFPMx output for the SSP2 and Fair pathways

- Rescale the harvest expected to the harvest actually provided and distinguish
  coniferous from Broadleaves. Use the CBM output table of harvest expected
  provided aggregated by coniferous and broadleaves.

Usage:

    ipython -i ~/repos/cobwood/scripts/extract_data_for_hwp_sink_computations.py

"""

import sys
import warnings
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
from ssp2_fair_owc_prepare_data import hexprovft_wide  # noqa: E402

# from ssp2_fair_owc_prepare_data import hexprov_wide


hwp_dir = cobwood.data_dir / "gfpmx_output" / "hwp"
hwp_dir.mkdir(exist_ok=True)

eu_countries = faostat.country_groups.eu_country_names
eu_countries += ["Netherlands"]

# Load output data, after a run has already been completed
gfpmx_pikssp2 = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario_name="pikssp2_fel1"
)
gfpmx_pikfair = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario_name="pikfair_fel1"
)

SELECTED_VARIABLES = [
    "cons",
    "prod",
    "exp",
    "imp",
]
PRODUCTS = ["indround", "fuel", "sawn", "panel", "pulp", "paper"]
print("Check units")
for product in PRODUCTS:
    for var in SELECTED_VARIABLES:
        print(product, var, gfpmx_pikssp2[product][var].unit)
msg = "There is an issue with the unit, it should be in tons instead of m3.\n"
msg += "see https://gitlab.com/bioeconomy/cobwood/cobwood/-/issues/11"
warnings.warn(msg)


def get_gfpmx_df(gfpmx_scenario, product):
    """Extract GFPMX projection output to a data frame"""
    ds = gfpmx_scenario[product]
    df = (
        ds[SELECTED_VARIABLES]
        .to_dataframe()
        .reset_index()
        .sort_values(["country", "year"])
    )
    df["pathway"] = gfpmx_scenario.scenario_name
    df["product"] = ds.product
    if product in ["paper", "pulp"]:
        df["unit"] = "1000 t"
    else:
        df["unit"] = "1000 m3"
    selector = df["country"].isin(eu_countries)
    # Place last columns first
    cols = list(df.columns)
    cols = cols[-3:] + cols[:-3]
    df = df.loc[selector].copy()[cols]
    return df


# For example
round_fair = get_gfpmx_df(gfpmx_pikfair, "round")

###########
# Rescale #
###########
# Aggregate harvest by combo_name, country, year and con_broad
index = ["combo_name", "iso2_code", "country", "year", "con_broad"]
cols = [
    "irw_need",
    "fw_colat",
    "fw_need",
    "amount_exp_hat",
    "harvest_exp_hat",
    "area",
    "to_product",
    "harvest_prov_ub",
    "harvest_prov_ob",
]
hexprov_cb = hexprovft_wide.groupby(index)[cols].agg("sum").reset_index()


#############################
# Write output to CSV files #
#############################
def extract_to_csv(gfpmx_scenario, product):
    """Extract GFPMx projection to a csv file"""
    df = get_gfpmx_df(gfpmx_scenario=gfpmx_scenario, product=product)
    df.to_csv(hwp_dir / f"{gfpmx_scenario.scenario_name}_{product}_eu.csv", index=False)


# for product in PRODUCTS:
#     extract_to_csv(gfpmx_pikfair, product)
#     extract_to_csv(gfpmx_pikssp2, product)
