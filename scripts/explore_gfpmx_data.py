""" The purpose of this script is to compute the percentage increase of roundwood harvest by 2050

- Compute the aggregate for EU countries of production and consumption.
- Compute the percentage change between any given year.

"""
from gftmx.gfpmx_data import gfpmx_data
from biotrade.faostat import faostat

round_ = gfpmx_data.get_country_rows("round")
fuel = gfpmx_data.get_country_rows("fuel")
indround = gfpmx_data.get_country_rows("indround")

# Select EU countries
eucountries = faostat.country_groups.eu_country_names + ["Czech Republic"]
indroundeu = indround.query("country in @eucountries")
fueleu = fuel.query("country in @eucountries")

# Check number of countries
print(set(eucountries) - set(indroundeu.reset_index().country.unique()))
print(indroundeu.reset_index().country.unique())


def print_increase_in_production(df, var, start, end):
    """Print the difference in production between the start and the end date"""
    df_change = df.loc[end, var].sum() / df.loc[start, var].sum()
    print(
        f"Increase in {df['faostat_name'].unique()} {var} between {start} and {end}:",
        round((df_change - 1) * 100),
        "%",
        f"from {round(df.loc[start, var].sum()/1e3)}",
        f"to {round(df.loc[end, var].sum()/1e3)} million m3",
    )


print_increase_in_production(indroundeu, "prod", 2020, 2050)
print_increase_in_production(fueleu, "prod", 2020, 2050)

print_increase_in_production(fueleu, "prod", 2022, 2050)
print_increase_in_production(indroundeu, "prod", 2022, 2050)

print_increase_in_production(indroundeu, "cons", 2020, 2050)
print_increase_in_production(fueleu, "cons", 2020, 2050)
