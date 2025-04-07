"""The purpose of this script is to export data for JRC D4

Usage:

    ipython -i $HOME/repos/cobwood/scripts/export_jrc_d4.py

"""


from cobwood.gfpmx import GFPMX
from biotrade.faostat import faostat
import warnings

eu_countries = faostat.country_groups.eu_country_names
eu_countries += ["Netherlands"]

# Load output data, after a run has already been completed
gfpmx_pikssp2 = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario="pikssp2_fel1"
)
gfpmx_pikfair = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario="pikfair_fel1"
)

SELECTED_VARIABLES = [
    "cons",
    "prod",
    "exp",
    "imp",
    "price",
    "gdp",
]

print("Check units")
for var in ["cons", "prod", "price"]:
    print(var, gfpmx_pikssp2["paper"][var].unit)
msg = "There is an issue with the unit, it should be in tons instead of m3.\n"
msg += "see https://gitlab.com/bioeconomy/cobwood/cobwood/-/issues/11"
warnings.warn(msg)

##########################################
# Extract paper projections to csv files #
##########################################


def extract_for_d4(gfpmx_scenario, product):
    """Extract data for EU countries for d4"""
    df = (
        gfpmx_scenario["paper"][SELECTED_VARIABLES]
        .to_dataframe()
        .reset_index()
        .sort_values(["country", "year"])
    )
    selector = df["country"].isin(eu_countries)
    df["unit"] = "1000 t"
    df["price_unit"] = "$/t"
    df["gdp_unit"] = "1000 constant 2005 USD"
    df["product"] = product
    return df.loc[selector]


paper_ssp2 = extract_for_d4(gfpmx_pikssp2, "paper")
print("countries:\n", paper_ssp2["country"].unique())
paper_ssp2.to_csv("/tmp/paper_gfpmx_pik_ssp2_scenario.csv", index=False)

paper_fair = extract_for_d4(gfpmx_pikfair, "paper")
paper_fair.to_csv("/tmp/paper_gfpmx_pik_fair_scenario.csv", index=False)
