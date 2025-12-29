# Agent Behaviour

This document outlines the guidelines and best practices for agent interactions and
modifications in the Cobwood project.


## Coding Standards

- Format code with black,
- Documentation should follow numpy docstrings format.
- Use type hints for function parameters and return types.
- Use pytest for writing and running tests.
- Describe changes made to this file in the "Operations Performed" section below.


## Development Practices

- Respect and use existing conventions, libraries, and frameworks already present in the
  codebase.
- Use TODO management tools to plan and track tasks.
- Prioritize using search tools to understand the codebase before making changes.
- Run lint commands after modifications to ensure code quality.
- Never commit changes unless explicitly asked by the user.


## Task Management

- Break down complex tasks into clear, achievable steps.
- Use TODOs to track progress and mark tasks as completed.
- Verify solutions with tests where possible.
- Provide CLI commands to showcase results when appropriate.


# Changes Made by the Agent

This section logs the operations, changes, and commits made by the agent during this
session. The agent should append the description of most recent operation at the end of
this list.


## Operations Changes

1. **Modified `cobwood/tests/test_gfpmx_equations.py`**: Added `imp_products_elasticity` to the `primary_product_dataset` fixture to support testing of `import_demand_indround`.

2. **Modified `cobwood/tests/test_gfpmx_equations.py`**: Uncommented `import_demand_indround` in the import statement to enable testing.

3. **Modified `cobwood/tests/test_gfpmx_equations.py`**: Added `test_import_demand_indround` function to test the `import_demand_indround` equation with expected results.

4. **Modified `scripts/extract_data_for_hwp_sink_of_semi_finished_products.py`**: Added
   code to place the "scenario" column first in the dataframe before writing to CSV.
   This improves data organization for downstream use.

5. **Modified `cobwood/gfpmx_plot.py`**: Updated the `facet_plot_by_var` function to
   display 2 columns by default. Added an optional `ncol` parameter (default 2) to
   control the number of columns in the facet plot, enhancing visualization flexibility.

6. **Improved `AGENTS.md`**: Expanded the document with detailed agent behaviour
   guidelines, development practices, and task management. Merged operations and commits
   into this section.

7. **Modified `cobwood/gfpmx_plot.py`**: Removed the y-axis label "value" from subplots
   and adjusted the supylabel position to prevent overlap with units on the right.

8. **Modified `cobwood/gfpmx.py`**: Added `return g` to the `facet_plot_by_var` method
   to return the plot object instead of None, allowing users to save the plot with
   `g.savefig()`.

9. **Modified `cobwood/gfpmx_plot.py`**: Added code to force scientific notation (1e6
   for millions, 1e3 for thousands) on the y-axis of facet plots.

10. **Modified `cobwood/gfpmx.py`**: Added type hints to all methods in the GFPMX class,
    including imports for typing and seaborn.

11. **Modified `cobwood/gfpmx_spreadsheet_to_csv.py`**: Added type hints to the
    `extract_world_price_parameter` and `gfpmx_spreadsheet_to_csv` functions, including
    adding the `Union` import from typing.

12. **Modified `cobwood/faostat/__init__.py`**: Added type hints to the
    `forestry_production_df` method (returning `pd.DataFrame`) and `foresty_production_ds`
    method (returning `xr.Dataset`), including necessary imports for pandas and xarray.

