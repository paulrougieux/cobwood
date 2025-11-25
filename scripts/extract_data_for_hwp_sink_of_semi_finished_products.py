""" Extract data to compute the Harvested Wood Products Sink


"""

from cobwood.gfpmx import GFPMX
from eu_cbm_hat import eu_cbm_data_pathlib

EU_COUNTRIES_LIST = [
    "Austria",
    "Belgium",
    "Bulgaria",
    "Croatia",
    "Czechia",
    "Denmark",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Hungary",
    "Luxembourg",
    "Ireland",
    "Italy",
    "Netherlands",
    "Poland",
    "Portugal",
    "Romania",
    "Slovakia",
    "Slovenia",
    "Spain",
    "Sweden",
    "Estonia",
    "Latvia",
    "Lithuania",
]

# Check all EU countries are in gfpmx output
# assert set(EU_COUNTRIES_LIST) - set(df.country.unique()) == set()


# country scenario year
# sw_broad_expected	sw_con_expected	sw_expected	wp_expected	pp_expected
def get_semifinished_projection(model):
    """Get projection of semifinished data from the model

    Example:

        ssp2fel1 = GFPMX(scenario="pikssp2_fel1")
        df = get_semifinished_projection(ssp2fel1)

    """
    df = model.all_products_ds["prod"].to_dataframe()
    df["scenario"] = model.scenario
    df.reset_index(inplace=True)
    return df


def write_semifinished_projection_to_eu_cbm_data(model):
    """Write to eu_cbm_data/domestic_harvest/scenario name

    Example:

        ssp2fel1 = GFPMX(scenario="pikssp2_fel1")
        write_semifinished_projection_to_eu_cbm_data(ssp2fel1)

    """
    # Keep only EU countries
    df = get_semifinished_projection(model)
    selector = df["country"].isin(EU_COUNTRIES_LIST)
    df = df.loc[selector]
    # Place scenario column first
    cols = df.columns.tolist()
    cols.remove("scenario")
    cols.insert(0, "scenario")
    df = df[cols]
    directory = eu_cbm_data_pathlib / "domestic_harvest" / model.scenario
    df.to_csv(directory / "hwp_expected_gfpmx.csv", index=False)


# available scenarios
# | base_2021.yaml
# | pikfair_fel1.yaml
# | pikssp2.yaml
# | pikssp2_fel1.yaml
# Scenario for a fuel wood demand elasticity of 1 fel1
ssp2fel1 = GFPMX(scenario="pikssp2_fel1")
