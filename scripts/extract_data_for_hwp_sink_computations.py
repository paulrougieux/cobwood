""" Extract data to compute the Harvested Wood Products Sink"""


import warnings
from cobwood.gfpmx import GFPMX
from biotrade.faostat import faostat
import cobwood

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


# Extract all products projections to csv files
def extract_to_csv(gfpmx_scenario, product):
    """Extract GFPMx projection to a csv file"""
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
    df.to_csv(hwp_dir / f"{gfpmx_scenario.scenario_name}_{product}_eu.csv", index=False)


for product in PRODUCTS:
    extract_to_csv(gfpmx_pikfair, product)
    extract_to_csv(gfpmx_pikssp2, product)
