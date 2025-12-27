


# Agent Behaviour

This document outlines the guidelines and best practices for agent interactions and
modifications in the Cobwood project.

## Coding Standards

- Format code with black
- Documentation should follow numpy docstrings format.
- Use type hints for function parameters and return types.
- Use pytest for writing and running tests.
- Describe changes made to this file in the "Operations Performed" section below.

## Development Practices

- Respect and use existing conventions, libraries, and frameworks already present in the
  codebase.
- Use TODO management tools to plan and track tasks.
- Prioritize using search tools to understand the codebase before making changes.
- Run lint and typecheck commands (e.g., `ruff`, `mypy`) after modifications to ensure
  code quality.
- Never commit changes unless explicitly asked by the user.

## Task Management

- Break down complex tasks into clear, achievable steps.
- Use TODOs to track progress and mark tasks as completed.
- Verify solutions with tests where possible.
- Provide CLI commands to showcase results when appropriate.

# Changes Made by the Agent

This section logs the operations, changes, and commits made by the agent during this session.

## Operations Changes and corresponding commit hash

1. **Modified `scripts/extract_data_for_hwp_sink_of_semi_finished_products.py`**: Added
code to place the "scenario" column first in the dataframe before writing to CSV. This
improves data organization for downstream use.

2. **Modified `cobwood/gfpmx_plot.py`**: Updated the `facet_plot_by_var` function to
display 2 columns by default. Added an optional `ncol` parameter (default 2) to control
the number of columns in the facet plot, enhancing visualization flexibility.

3. **Improved `AGENTS.md`**: Expanded the document with detailed agent behaviour guidelines, development practices, and task management. Merged operations and commits into this section.

