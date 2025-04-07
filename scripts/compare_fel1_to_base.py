"""Compare output where the fuel wood elasticity was set to one to the base model

Run this script

    penv
    ipython -i /home/paul/rp/cobwood/scripts/compare_fel1_to_base.py

"""

import sys
import pandas
import matplotlib.pyplot as plt
from biotrade.faostat import faostat
import cobwood
from cobwood.gfpmx import GFPMX

eu_countries = faostat.country_groups.eu_country_names
eu_countries += ["Netherlands"]

# Load CBM output data
eu_cbm_explore_path = cobwood.data_dir.parent / "eu_cbm" / "eu_cbm_explore"
scenario_dir = eu_cbm_explore_path / "scenarios" / "ssp2_fair_degrowth"
# Load data and plotting functions from the prepare script in the same directory
sys.path.append(str(scenario_dir))


hwp_dir = cobwood.data_dir / "gfpmx_output" / "hwp"
hwp_dir.mkdir(exist_ok=True)

eu_countries = faostat.country_groups.eu_country_names
eu_countries += ["Netherlands"]

# Load output data, after a run has already been completed
gfpmx_pikssp2_fel1 = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario="pikssp2_fel1"
)
gfpmx_pikssp2_base = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario="pikssp2"
)
gfpmx_pikfair_fel1 = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario="pikfair_fel1"
)
gfpmx_pikfair_base = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario="pikfair"
)


def get_df_eu(model, product, variable):
    """Extract a data frame from the model xarray output keep only EU countries"""
    df = model[product][variable].to_dataframe().reset_index()
    selector = df["country"].isin(eu_countries)
    df = df.melt(id_vars=["country", "year"], value_vars="cons", var_name="variable")
    df["product"] = product
    df["scenario"] = model.scenario
    return df.loc[selector].reset_index(drop=True)


########################################################
# Comparison of EU fuelwood consumption and production #
########################################################
comp_list = []
for this_prod in ["fuel", "indround"]:
    for this_var in ["cons", "prod"]:
        dfssp2base = get_df_eu(gfpmx_pikssp2_base, this_prod, this_var)
        dfssp2fel1 = get_df_eu(gfpmx_pikssp2_fel1, this_prod, this_var)
        dffairbase = get_df_eu(gfpmx_pikfair_base, this_prod, this_var)
        dffairfel1 = get_df_eu(gfpmx_pikfair_fel1, this_prod, this_var)
        comp_list += [dfssp2base, dfssp2fel1, dffairbase, dffairfel1]

comp = pandas.concat(comp_list)
del comp_list
index = ["year", "product", "scenario", "variable"]
compeu = comp.groupby(index)["value"].agg("sum").reset_index()


########
# Plot #
########
# Facet plot by country with 2 colors for the different sources
def plotcomp(df, product, variable):
    selector = df["product"] == product
    selector &= df["variable"] == variable
    selector &= df["year"] != 2071
    df = df.loc[selector].copy()
    df["value"] *= 1e-6
    df_wide = df.pivot(columns="scenario", index="year", values="value")
    df_wide.plot(title=f"{product} {variable} Million m3")
    plt.show()


plotcomp(compeu, "fuel", "cons")

plotcomp(compeu, "fuel", "prod")
plotcomp(compeu, "indround", "prod")
plotcomp(compeu, "indround", "cons")

# Percentage difference between base and fel1
# In 2030, 2050 and 2070
compeu["base_or_fel1"] = "base"
compeu[["scenario2", "model_version"]] = compeu["scenario"].str.split(
    "_", n=1, expand=True
)
selector = compeu["scenario"].str.contains("_fel1")
compeu.loc[~selector, "model_version"] = "base"

index = ["year", "product", "variable", "scenario2"]
compeu_wide = compeu.pivot(columns="base_or_fel1", index=index, values="value")
compeu_wide["reldiff"] = compeu_wide["fel1"] / compeu_wide["base"] - 1
compeu_wide.query("year in [2030, 2050]")

# Roundwood = indround + Fuelwood 2050
#                                   base	fel1	reldiff
# indround	cons	pikfair	471085.040325443	415235.488134672	-0.118555138478157
# indround	prod	pikssp2	633721.456237559	649287.283194183	0.0245625689384723
