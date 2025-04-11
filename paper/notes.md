

# Discarded text

The following text was removed to keep the paper concise.

# Data structure and implementation

Figure illustrating the following points:

- 2D panel data countries x time
- 1D vector data elasticities
- Arrow to the gfpmx_data model object which contains data only
- Arrow to the GFPMx model object which contains the data and a modelling implementation
  in the form of equations.
- illustration of the gfpmx["sawn"] dataset containing many data arrays
- illustration of gfpmx["sawn"]["cons"] 2 dimensional data array

Note: We have thought about setting the product as another dimension of a larger data
array that would contain all products, but we have decided against this because products
are treated differently and adding a third dimension to the data array would mean that
we need to call the 3 dimensions each time we write equations with these data arrays.
However, this decision can be revised and adding a third dimension could well be
experimented as further development of this model. As explained above, the method called
`write_datasets_to_netcdf` already sets a third dimension coordinate called `product`
before saving the datasets to netcdf files.


## Model run

It's possible to change any input parameters in the GFPMX object after it has been
created. For example, to change the GDP projections to a hypothetical 2% growth scenario
from a given start year:

    start_year = 2025
    gfpmx_2_percent = GFPMX(
        input_dir="gfpmx_base2021", base_year=2021, scenario="2_percent",
        rerun=True
    )
    countries = gfpmx_2_percent["sawn"].c
    gfpmx_2_percent.gdp


## Other models

- https://www.perplexity.ai/search/i-am-writing-a-paper-describin-BujunqDzSWCoO1yyDoBkIQ

> "Global Forest Model (G4M) G4M is a spatially explicit model developed by IIASA,
> focusing on forestry and land-use change. It evaluates wood demand, carbon
> sequestration policies, and alternative land uses. The model code is not open-source,
> but more details can be found on its model page
> https://web.jrc.ec.europa.eu/policy-model-inventory/explore/models/model-g4m

> GLOBIOM-Forest Model This version of GLOBIOM includes a detailed description of the
> forest sector, focusing on economic surplus maximization and biophysical data
> integration. The source code is not yet freely available, but documentation and
> results are accessible on its GitHub repository
> https://github.com/iiasa/GLOBIOM_forest

> https://globiom.org/source_tree.html

    > See the Source Tree to learn how the GLOBIOM code is structured, and what the
    > various code files do. An **Open Source version of GLOBIOM is under preparation**.
    > External collaborators are given access to a pre-release version of GLOBIOM hosted
    > on GitHub in this private repository.


> EFI-GTM (Global Forest Sector Model) EFI-GTM is a partial equilibrium model analyzing
> production, consumption, trade, and prices of forest products under various external
> factors. It is developed by the European Forest Institute. Detailed documentation can
> be found in the internal report"


