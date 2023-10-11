"""The purpose of this script is to estimate parameters of the export supply function

- marginal propensity to export sigma_{ik}

- constant tetha_{ik}

X_ik = tetha_{ik} + sigma_{ik} I_{wkt}

Because world import I_{wkt} is not equal to world export X_{wkt},
the estimation is performed with world exports instead.

- See Buongiorno 2022 "GFPMX: A Cobweb Model of the Global Forest Sector, with an
  Application to the Impact of the COVID-19 Pandemic"

"""

import xarray
import numpy as np
import seaborn
from sklearn.linear_model import LinearRegression
from matplotlib import pyplot as plt
from cobwood.gfpmx import GFPMX


# Load historical data
gfpmxb2021 = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario_name="base_2021"
)


############################################################
# Estimate the industrial roundwood export supply function #
############################################################
ds = gfpmxb2021["indround"]
# Keep only data related for the historical period
ds = ds.loc[{"year": ds.coords["year"] <= 2021}]
# Convert to a data frame
# Initialize empty new coefficients as 1D datasets
ds["exp_mpte_2"] = xarray.full_like(ds["exp_constant"], fill_value=np.nan)
ds["exp_constant_2"] = xarray.full_like(ds["exp_constant"], fill_value=np.nan)
# Initialize predicted values
ds["exp_predicted"] = xarray.full_like(ds["exp"], fill_value=np.nan)
for this_country in ds["country"].loc[ds.c].values:
    X = ds["exp"].loc["WORLD"].values.reshape(-1, 1)
    Y = ds["exp"].loc[this_country].values.reshape(-1, 1)
    # TODO: display p values and errors of the estimates and R square
    model = LinearRegression()
    model.fit(X, Y)
    print(
        this_country,
        model.intercept_[0],
        model.coef_[0, 0],
        any(np.isnan(model.predict(X).squeeze())),
    )
    ds["exp_constant_2"].loc[this_country] = model.intercept_[0]
    ds["exp_mpte_2"].loc[this_country] = model.coef_[0, 0]
    ds["exp_predicted"].loc[this_country] = model.predict(X).squeeze()


# Fit the model using the fit() method
this_country = "Czechia"

df = ds.to_dataframe()
selected_columns = df.columns
selected_columns = selected_columns[selected_columns.str.contains("exp")]


df_cz = df.query("country == 'Czechia'").copy()
df_cz["exp_predicted"] = model.predict(X)
df_cz.plot(x="exp", y="exp_predicted", kind="scatter")

# Diagnostic plots
if False:
    # Comparison table EU Countries
    # Scatter plot to compare existing versus estimated parameters
    params = [
        "exp_marginal_propensity_to_export",
        "exp_constant",
        "exp_constant_2",
        "exp_mpte_2",
    ]
    df_params = ds[params].to_dataframe()
    df_params.plot(
        x="exp_marginal_propensity_to_export", y="exp_mpte_2", kind="scatter"
    )
    plt.show()

    # Scatter plot to compare actual versus predicted values
    df.plot(x="exp", y="exp_predicted", kind="scatter")
    plt.show()
    # Scatter plot EU Countries

    # Scatter plot to compare the world export to the sum of predicted exports
    countries = ds["country"].loc[ds.c].values
    df_agg = df.query("country in @countries").groupby("year").sum()
    df_agg.plot(x="exp", y="exp_predicted", kind="scatter")
    plt.show()

    df_eu_long = df.query("country in @faostat.country_groups.eu_country_names")[
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


# Change Czechia historical export to the mean of last 5 years
