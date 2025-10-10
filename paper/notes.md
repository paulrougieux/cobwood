
# TODO

- TODO: install the package in a new environment, based on the TOML file


# Instruction

- Journal of Open Source Software (JOSS)- Paper submission guidelines
  https://joss.readthedocs.io/en/latest/submitting.html


## Compile the paper to pdf

- Compile this paper to a pdf document with the script specified in .gitlab-ci.yml. JOSS
  uses the openjournals/inara docker image and compiles the document with the following
script:

        inara -p -o pdf paper/paper.md

- Extract documentation from the package docstrings with pdoc

        pdoc -o public ./cobwood/


End comments.


## Generate plots as images

Save plots as images to be inserted in the paper

    from cobwood import data_dir
    from cobwood.gfpmx_equations import compute_country_aggregates
    plot_dir = data_dir.parent / "cobwood/paper/fig"
    gfpmxb2021 = GFPMX(
        input_dir="gfpmx_base2021", base_year=2021, scenario="base_2021",
        rerun=False
    )
    print("Re-compute aggregates for the historical period.")
    for this_product in gfpmxb2021.products:
        for year in range(1995, 2022):
            compute_country_aggregates(gfpmxb2021[this_product], year)
            compute_country_aggregates(gfpmxb2021.other, year, ["area", "stock"])

    # Draw the default plot with one line by continent
    g = gfpmxb2021.facet_plot("indround")
    g.savefig(plot_dir / "indround_by_continent.png")

    # Use the countries argument to specify one line by country
    g = gfpmxb2021.facet_plot("indround", countries=["Canada", "France", "Japan"])
    g.savefig(plot_dir / "indround_by_country.png")

Maybe use https://docs.xarray.dev/en/latest/generated/xarray.plot.pcolormesh.html



# Discarded text

The following text was removed to keep the paper concise.

## Summary

- By implementing country and time coordinates, the python source code closely mirrors
  mathematical equations used in research publications.

- For example, it can provide harvest scenarios to forest vegetation dynamics models, or
  of downstream of forest vegetation models or upstream of upstream, or life cycle
  analysis downstream.

- including for example forest dynamics models and life cycle analysis models.


## Statement of need

- They particularly value the ability to explore future wood harvest developments under
  various demand and supply scenarios.

- Detailed knowledge on the source code implementation of a model becomes essential when
  extending a model to address novel research questions.

- While research papers describe the conceptual specifications for these models, reading
  the source code of the model implementation offers a more comprehensive understanding
  of the system.

- While this approach can make programs more concise, it creates challenges for
  newcomers trying to understand the models.

- for those unfamiliar with the model's implementation

- Examples of readability issue can be found in the source code of models like GFTM,
  GFPM, and Timba. Other models are closed source and not yet publicly available for
  review That source code for other forest sector models, such as EFI-GTM and
  G4M-GLOBIOM-Forest, is .

- the main value of this python package doesn't lie in the model itself, but in the
  panel data structure that can be used to implement many models.


- These paragraph was removed because it has been reformulated and shortened using
  Claude

    - Macroeconomic models typically organize market datasets along two dimensions:
      country and time. In econometrics, the structure is known as panel data. Forest
      products market datasets contain information on production, consumption, and trade
      for specific products such as roundwood, sawnwood, wood panels, pulp, and paper
      products. Current modelling software often lack a panel data structure, instead,
      they use partial labelling approaches—such as matrices names or vector names
      within data frames i.e. tabular structures. Variable names are sometimes unclear,
      making the source code difficult to interpret, some of the models are not
      available as open source. In addition, the limited data labelling makes it harder
      to reuse the output of those models.

    - Adjacent fields of research such as forest management, vegetation dynamic
      modelling or Life Cycle Analysis need estimes of future roundwood harvest and of
      future wood products consumption. The transparency of the models and algorithms
      are helpful to these research communities when determining whether a particular
      model is suitable for analysing specific policy questions or can be modified
      appropriately

## Input, output

- Remember that Xarray datasets can be converted to pandas data frame very easily.

- Xarray saves the model output data to  NetCDF files.


## Data structure and implementation

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

- enabling a more intuitive approach to economic modelling.

- A model organizes global forest product data including consumption, production, trade
  flows, and prices.

- An advantage of Xarray's approach is the automatic dimension alignment when performing
  operations between arrays, which simplifies mathematical operations across different
  data elements.

- creates a clean, organized data representation that makes the modelling system more
  accessible to new users.

- The cobwood package is designed for extensibility across different models, though the
  initial release focuses on implementing the Global Forest Products Model (GFPMx) .


### Model run

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


## Visualisation

- We don't need to re-run the model this time since we can simply reload the model's
  output data from the previous run above.


## Conclusion

- by allowing equations with time and country coordinates to be easily identified in the
  code. Units are stored as metadata attributes


### Other models

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


# Review

Link to the pre-review https://github.com/openjournals/joss-reviews/issues/8587


## Reviewers

List of potential reviewers without the "`@`" mention, with a short explanation for the
choice.

Authors of papers marked as similar:

- MatthewHeun https://github.com/MatthewHeun
- ghislainv https://github.com/ghislainv
- klau506 https://github.com/klau506
- realxinzhao https://github.com/realxinzhao

Authors of packages that use Xarray as well:

- ArcticSnow https://github.com/ArcticSnow
- tennlee https://github.com/tennlee
- tomvothecoder https://github.com/tomvothecoder

