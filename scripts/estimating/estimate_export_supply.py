"""The purpose of this script is to estimate parameters of the export supply function

- marginal propensity to export sigma_{ik}

- constant tetha_{ik}

X_ik = tetha_{ik} + sigma_{ik} I_{wkt}

Because world import I_{wkt} is not equal to world export X_{wkt},
the estimation is performed with world exports instead.

- See Buongiorno 2022 "GFPMX: A Cobweb Model of the Global Forest Sector, with an
  Application to the Impact of the COVID-19 Pandemic"

"""

import pandas
import xarray
import numpy as np
import seaborn
from sklearn.linear_model import LinearRegression
from matplotlib import pyplot as plt
from biotrade.faostat import faostat
from cobwood.gfpmx import GFPMX

# Load historical data
gfpmxb2021 = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario_name="base_2021"
)


############################################################
# Estimate the industrial roundwood export supply function #
############################################################
def estimate_export_supply(ds, variable, country):
    """Estimate the export supply function
    modifies the dataset in place by adding new coefficient and constant"""
    X = ds[variable].loc["WORLD"].values.reshape(-1, 1)
    Y = ds[variable].loc[country].values.reshape(-1, 1)
    # TODO: display p values and errors of the estimates and R square
    model = LinearRegression()
    model.fit(X, Y)
    print(country, model.intercept_[0], model.coef_[0, 0])
    ds["exp_constant_2"].loc[country] = model.intercept_[0]
    ds["exp_mpte_2"].loc[country] = model.coef_[0, 0]
    ds["exp_predicted"].loc[country] = model.predict(X).squeeze()


irw = gfpmxb2021["indround"]
# Keep only data related for the historical period
irw = irw.loc[{"year": irw.coords["year"] <= 2021}]
# Convert to a data frame
# Initialize empty new coefficients as 1D datasets
irw["exp_mpte_2"] = xarray.full_like(irw["exp_constant"], fill_value=np.nan)
irw["exp_constant_2"] = xarray.full_like(irw["exp_constant"], fill_value=np.nan)
# Initialize predicted values
irw["exp_predicted"] = xarray.full_like(irw["exp"], fill_value=np.nan)
for this_country in irw["country"].loc[irw.c].values:
    estimate_export_supply(irw, "exp", this_country)

# Change Czechia historical export to the mean of last 5 years
# Re-estimate the model for that country
yr = irw.coords["year"]
cz_mean = irw["exp"].loc["Czechia", (2011 <= yr) & (yr <= 2015)].mean().values
# Initialize empty new coefficients as 1D datasets
irw["exp_2"] = irw["exp"].copy()
irw["exp_2"].loc["Czechia", (yr > 2015)] = cz_mean
estimate_export_supply(irw, "exp", "Czechia")
estimate_export_supply(irw, "exp_2", "Czechia")


# Czechia old -11957.761050798406 0.14492400767319605
# Czechia new -395.63598204559366 0.030772674789748013
irw_cz = irw.loc[{"country": "Czechia"}]
print(
    "Czechia existinct coefficients:",
    irw_cz["exp_constant"].values,
    irw_cz["exp_marginal_propensity_to_export"].values,
    "\nnew coefficients:",
    irw_cz["exp_constant_2"].values,
    irw_cz["exp_mpte_2"].values,
)

# Project to 2050 based on a rough projection of irw world imports
irw_world = pandas.DataFrame(
    {
        "year": [2000, 2010, 2020, 2030, 2040, 2050, 2060],
        "country": ["WORLD", "WORLD", "WORLD", "WORLD", "WORLD", "WORLD", "WORLD"],
        "imp": [
            115241.22300000001,
            109739.82599999999,
            137825.35400000002,
            148918.1680023607,
            163784.09762111588,
            174930.4527127895,
            182549.4140419694,
        ],
    }
)
irw_world["cz_exp_1"] = (
    irw_world["imp"] * irw_cz["exp_marginal_propensity_to_export"].values
    + irw_cz["exp_constant"].values
)
irw_world["cz_exp_2"] = (
    irw_world["imp"] * irw_cz["exp_mpte_2"].values + irw_cz["exp_constant_2"].values
)


# selected_columns = df.columns
# selected_columns = selected_columns[selected_columns.str.contains("exp")]
# df_cz = df.query("country == 'Czechia'").copy()
# df_cz.plot(x="exp", y="exp_predicted", kind="scatter")

# Diagnostic plots


# Diagnostic plots
if False:
    df = irw.to_dataframe()

    # Comparison table EU Countries
    # Scatter plot to compare existing versus estimated parameters
    params = [
        "exp_marginal_propensity_to_export",
        "exp_constant",
        "exp_constant_2",
        "exp_mpte_2",
    ]
    df_params = irw[params].to_dataframe()
    df_params.plot(
        x="exp_marginal_propensity_to_export", y="exp_mpte_2", kind="scatter"
    )
    plt.show()

    # Scatter plot to compare actual versus predicted values
    df.plot(x="exp", y="exp_predicted", kind="scatter")
    plt.show()
    # Scatter plot EU Countries

    # Scatter plot to compare the world export to the sum of predicted exports
    countries = irw["country"].loc[irw.c].values
    df_agg = df.query("country in @countries").groupby("year").sum()
    df_agg.plot(x="exp", y="exp_predicted", kind="scatter")
    plt.show()

    eu_country_names = faostat.country_groups.eu_country_names
    df_eu_long = df.query("country in @eu_country_names")[
        ["exp", "exp_predicted"]
    ].melt(ignore_index=False)
    g = seaborn.relplot(
        data=df_eu_long.reset_index(),
        x="year",
        y="value",
        col="country",
        hue="variable",
        kind="line",
        col_wrap=5,
        height=3,
        facet_kws={"sharey": False, "sharex": False},
    )
    g.fig.supylabel("Actual versus predicted exports")
    g.fig.subplots_adjust(left=0.28, top=0.9)
    g.set(ylim=(0, None))
    plt.show()
