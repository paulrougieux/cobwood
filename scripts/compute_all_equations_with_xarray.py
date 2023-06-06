"""This scripts computes all GFPMx equations using xarray

TODO: Continue work in scripts/compute_gdp_fair_scenario.py

Usage:

    ipython -i ~/repos/cobwood/scripts/compute_all_equations_with_xarray.py

See also:

- The general version of this script in the module cobwood/run_and_compare_to_ref.py

- A drawing illustrating the model structure in
  draft_articles/gftm_degrowth/model_structure.odg

- Buongiorno, J. (2021). GFPMX: A Cobweb Model of the Global Forest Sector,
  with an Application to the Impact of the COVID-19 Pandemic. Sustainability,
  13(10), 5507. https://www.mdpi.com/2071-1050/13/10/5507

Advantages of using xarray over pandas:

- The shift_index() function is not needed any more, we can call
  sawn["price"].loc[:, t - 1] directly.


- Evaluate whether it is better to keep countries and aggregates in the same dataset.

- TODO within option A replace COUNTRIES by a list internal to the dataset for example

  >>> ds = sawn
  >>> all(ds["price"].loc[~ds.region.isnull(), 2019] ==  ds["price"].loc[COUNTRIES, 2019])
  >>> ds["c"] = ~ds.region.isnull()
  >>> ds["price"].loc[ds.c, 2019]
  >>> assert(all(ds["country"].loc[~ds.c] ==
  >>>            ['WORLD', 'AFRICA', 'NORTH AMERICA', 'SOUTH AMERICA', 'ASIA', 'OCEANIA', 'EUROPE']))


  Option A first option as of begining of 2023. Countries and aggregates are in the same dataset, consumption can be
  computed for countries only first, the aggregates computed later.

        ds["cons_constant"]
        * pow(ds["price"].loc[COUNTRIES, t - 1], ds["cons_price_elasticity"])
        * pow(ds["gdp"].loc[COUNTRIES, t], ds["cons_gdp_elasticity"])

  World price is

        ds["price_constant"].loc["WORLD"]
        * pow(ds_primary["price"].loc["WORLD", t], ds["price_input_elast"].loc["WORLD"])

  Should the .loc["WORLD"] and .loc[COUNTRIES] be done when the function is
  called? No better to leave no ambiguity.

  All uses of the world aggregates in the equations below, show that only the
  world price, world production and world stock variables are used in equations:

        ds["price_constant"].loc["WORLD"]
        pow(ds_primary["price"].loc["WORLD", t], ds["price_input_elast"].loc["WORLD"])
        ds_agg["price_constant"].loc["WORLD"]
        pow(ds_primary_agg["price"].loc["WORLD", t], ds_agg["price_input_elast"].loc["WORLD"])
        ds["price_constant"].loc["WORLD"]
        ds_primary["price"].loc["WORLD", t], ds["price_input_elast"].loc["WORLD"]
        ds["price_constant"].loc["WORLD"]
        ds["prod"].loc["WORLD", t],
        ds["price_world_price_elasticity"].loc["WORLD"],
        ds_other["stock"].loc["WORLD", t],
        ds["price_stock_elast"].loc["WORLD"],
        np.exp(ds["price_trend"].loc["WORLD"] * t)
        ds["price"].loc["WORLD", t], ds["price_world_price_elasticity"].loc[ds.c]


  Option B There is a dataset of countries only and a dataset of aggregates only we
  can compute consumption as such:

        ds["cons_constant"]
        * pow(ds["price"].loc[:, t - 1], ds["cons_price_elasticity"])
        * pow(ds["gdp"].loc[:, t], ds["cons_gdp_elasticity"])

  World prices can be computed as:

        ds_agg["price_constant"].loc["WORLD"]
        * pow(ds_primary_agg["price"].loc["WORLD", t], ds_agg["price_input_elast"].loc["WORLD"])

  Option C Aggregates are stored as another dimension. Since the continent
  aggregates are not used, they could be stored separately as part of the
  dataset. Or the dataset could contain another dimension that distinguishes
  the aggregates.


    Do we need a big or a small class? Do we need a class at all?
    - Con: This would mean using methods instead of functions. Nah.
       - All the computation functions can remain as functions, they don't need to be part of the class
    - Pro: a class would mean storing all data sets as class attributes,
      and providing an object for model comparison yes.
          - The only blocker is the COUNTRIES list, which is also part of gfpmx_data.

    class GFPMX_runner:
        # Run the GFPMX simulation, I"m not in favour of this big monster class
        def __init__(self, data_dir, base_year):
            self.gfpmx_data = GFPMXData(data_dir=data_dir, base_year=base_year)

    class mini_gfpmx_data:
       # carry only indround, fuel, pulp, sawn, panel, paper

  Option D Aggregates are only available as a method computed from the data, based on the


"""


from cobwood.gfpmx_data import convert_to_2d_array
from cobwood.gfpmx_data import GFPMXData
from cobwood.gfpmx_data import remove_after_base_year_and_copy
from cobwood.gfpmx_data import compare_to_ref
from cobwood.gfpmx_equations import compute_one_time_step
from cobwood.gfpmx_equations import consumption
from cobwood.gfpmx_equations import import_demand
from cobwood.gfpmx_equations import export_supply
from cobwood.gfpmx_equations import production
from cobwood.gfpmx_equations import world_price
from cobwood.gfpmx_equations import local_price

BASE_YEAR = 2018
DATA_DIR = "gfpmx_8_6_2021"
gfpmx_data = GFPMXData(data_dir=DATA_DIR, base_year=BASE_YEAR)

# Load reference data
other_ref = gfpmx_data.convert_sheets_to_dataset("other")
indround_ref = gfpmx_data.convert_sheets_to_dataset("indround")
round_ref = gfpmx_data.convert_sheets_to_dataset("round")
fuel_ref = gfpmx_data.convert_sheets_to_dataset("fuel")
sawn_ref = gfpmx_data.convert_sheets_to_dataset("sawn")
panel_ref = gfpmx_data.convert_sheets_to_dataset("panel")
pulp_ref = gfpmx_data.convert_sheets_to_dataset("pulp")
paper_ref = gfpmx_data.convert_sheets_to_dataset("paper")
gdp = convert_to_2d_array(gfpmx_data.get_sheet_wide("gdp"))

COUNTRY_AGGREGATES = gfpmx_data.country_aggregates
COUNTRIES = sawn_ref.country[~sawn_ref.country.isin(COUNTRY_AGGREGATES)].values
# Check that all countries in the dataset are also present in the list
assert set(list(COUNTRIES)) - set(gfpmx_data.country_groups["country"]) == set()
# Check that all countries present in the list are also in the dataset
assert set(gfpmx_data.country_groups["country"]) - set(list(COUNTRIES)) == set()

######################################################
# Erase data after base year and copy the data frame #
######################################################
# Using a mask makes the dataset return an error on loc selection
# base_year = 2018
# mask = sawn.coords["year"] > base_year
# sawn = xarray.where(mask, np.nan, sawn_ref).copy()
# sawn["price"].loc[:,t-1]
# # returns KeyError: 2018
# # But selecting the original data works fine
# sawn_ref["price"].loc[:,t-1]
# --> Make a reproducible example and ask on Stackoverflow why this is the case.
# We will compute demand from the base_year + 1

other = remove_after_base_year_and_copy(other_ref, BASE_YEAR)
fuel = remove_after_base_year_and_copy(fuel_ref, BASE_YEAR)
indround = remove_after_base_year_and_copy(indround_ref, BASE_YEAR)
# Use an underscore so that we don't overwrite the python round() function
round_ = remove_after_base_year_and_copy(round_ref, BASE_YEAR)
sawn = remove_after_base_year_and_copy(sawn_ref, BASE_YEAR)
panel = remove_after_base_year_and_copy(panel_ref, BASE_YEAR)
pulp = remove_after_base_year_and_copy(pulp_ref, BASE_YEAR)
paper = remove_after_base_year_and_copy(paper_ref, BASE_YEAR)

# Memory size
for ds in [indround, fuel, pulp, sawn, panel, paper, other]:
    print(f"{ds.product}: {ds.nbytes / 1024 ** 2:.2f} MB")

# Add GDP projections to the datasets gdp are projected to the future
sawn["gdp"] = gdp
round_["gdp"] = gdp
panel["gdp"] = gdp
fuel["gdp"] = gdp
paper["gdp"] = gdp

compute_one_time_step(indround, fuel, pulp, sawn, panel, paper, other, 2019)
compute_one_time_step(indround, fuel, pulp, sawn, panel, paper, other, 2020)
# See more years below, using the compare_to_ref function to compare

# # Compute roundwood as the sum of industrial round wood and fuel wood
# round_["prod"].loc[COUNTRIES, year] = (
#     indround["prod"].loc[COUNTRIES, year] + fuel["prod"].loc[COUNTRIES, year]
# )

##########
# Checks #
##########


compute_one_time_step(indround, fuel, pulp, sawn, panel, paper, other, 2019)
ciepp_vars = ["cons", "imp", "exp", "prod", "price"]
compare_to_ref(sawn, sawn_ref, ciepp_vars, 2019)
compare_to_ref(panel, panel_ref, ciepp_vars, 2019)
compare_to_ref(paper, paper_ref, ciepp_vars, 2019)
compare_to_ref(pulp, pulp_ref, ciepp_vars, 2019)
compare_to_ref(indround, indround_ref, ciepp_vars, 2019)

compute_one_time_step(indround, fuel, pulp, sawn, panel, paper, other, 2020)
ciepp_vars = ["cons", "imp", "exp", "prod", "price"]
compare_to_ref(sawn, sawn_ref, ciepp_vars, 2020)
compare_to_ref(panel, panel_ref, ciepp_vars, 2020)
compare_to_ref(paper, paper_ref, ciepp_vars, 2020)
compare_to_ref(pulp, pulp_ref, ciepp_vars, 2020)
compare_to_ref(indround, indround_ref, ciepp_vars, 2020)

for this_year in range(BASE_YEAR + 1, 2051):
    print(this_year)
    # TODO: decrease tolerance
    rtol = 1e-2
    compute_one_time_step(indround, fuel, pulp, sawn, panel, paper, other, this_year)
    ciepp_vars = ["cons", "imp", "exp", "prod", "price"]
    compare_to_ref(sawn, sawn_ref, ciepp_vars, this_year, rtol=rtol)
    compare_to_ref(panel, panel_ref, ciepp_vars, this_year, rtol=rtol)
    compare_to_ref(paper, paper_ref, ciepp_vars, this_year, rtol=rtol)
    compare_to_ref(pulp, pulp_ref, ciepp_vars, this_year, rtol=rtol)
    compare_to_ref(indround, indround_ref, ciepp_vars, this_year, rtol=rtol)

# Compare world price
#  assert_allclose(sawn["price"].loc["WORLD", year], sawn_ref["price"].loc["WORLD", year])

raise ValueError(
    """ds["price"].loc[ds.c, 2019] opens the possibility to use the class gfpmx_data
                 as the sole argument of compute_one_time_step"""
)


year = 2019
# Comparison between sawn modified in place by the
# compute_secondary_product_ciep() function
# and sawn2 computed below
sawn2 = sawn.copy(deep=True)
sawn2["cons"].loc[COUNTRIES, year] = consumption(sawn2, year)
sawn2["imp"].loc[COUNTRIES, year] = import_demand(sawn2, year)
sawn2["exp"].loc[COUNTRIES, year] = export_supply(sawn2, year)
sawn2["prod"].loc[COUNTRIES, year] = production(sawn2, year)
sawn2["price"].loc["WORLD", year] = world_price(sawn2, indround, year)
sawn2["price"].loc[COUNTRIES, year] = local_price(sawn2, year)
assert sawn.equals(sawn2)


# Comparison in case of mismatch
sawn_df = sawn.loc[dict(country=COUNTRIES, year=year)].to_pandas().reset_index()
sawn_ref_df = sawn_ref.loc[dict(country=COUNTRIES, year=year)].to_pandas().reset_index()
cols_to_check = ["cons", "imp", "exp", "prod"]
print(sawn_df[cols_to_check])
print(sawn_ref_df[cols_to_check])
sawn_df["prod_diff"] = sawn_df["prod"] / sawn_ref_df["prod"] - 1
sawn_df["cons_diff"] = sawn_df["cons"] / sawn_ref_df["cons"] - 1
print(sawn_df[["cons_diff", "prod_diff"]].describe())
sawn_df[["country"] + cols_to_check + ["prod_diff"]].sort_values(
    "prod_diff", ascending=False
)
print(sawn_ref_df[["country"] + cols_to_check])


# Plot comparison
# sawn_df["reference"] = "no"
# sawn_ref_df["reference"] = "yes"
# sawn_comp = pandas.concat([sawn_df, sawn_ref_df])
# p = seaborn.scatterplot(x="country", y="prod", hue="reference", data=sawn_comp)
# plt.xticks(rotation=90)
# plt.show()
