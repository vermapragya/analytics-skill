# Rule: Python Data Science Style

Always-follow conventions for Python in DS workflows.

## Imports
- Standard library first, then third-party, then local
- Specific imports preferred over `import *`
- Common aliases:
  ```python
  import pandas as pd
  import numpy as np
  import matplotlib.pyplot as plt
  import seaborn as sns
  ```

## DataFrame operations
- Use method chaining for clarity:
  ```python
  result = (
      df
      .query("status == 'active'")
      .groupby("country")
      .agg(n=("user_id", "nunique"), revenue=("amount", "sum"))
      .reset_index()
  )
  ```
- Prefer `.loc[]` over chained indexing (`df[df['x'] > 0]['y']` → use `df.loc[df['x'] > 0, 'y']`)
- Avoid mutating source DataFrames; use `.copy()` when transforming

## Null handling
- Be explicit: `df.fillna(0)`, `df.dropna()`, `df.isnull().sum()`
- Distinguish missing-by-design vs missing-by-error
- Document null policy in code comments

## Type hints
- Use type hints in functions:
  ```python
  def compute_retention(df: pd.DataFrame, cohort_col: str) -> pd.DataFrame:
      ...
  ```
- Use `from __future__ import annotations` for forward-compatible syntax

## Reproducibility
- Set random seeds: `np.random.seed(42)`, `random.seed(42)`
- Use deterministic train/test splits
- Pin library versions in `requirements.txt` for production work

## Modeling
- Always separate train/test (no fitting on test set, ever)
- Use temporal splits for production models, random splits only for exploration
- Save fitted models with metadata (training date, sample size, version)

## Visualization
- Every chart has a title that states the takeaway
- Axis labels include units
- One message per chart
- Color-blind safe palettes (`tab10`, viridis, cividis)

## Notebooks
- One purpose per notebook
- Reset cell counter before sharing
- Move reusable code to `.py` modules, don't leave in notebooks
- Add a TL;DR markdown cell at the top

## Performance
- Vectorize: avoid `for` loops over DataFrame rows
- Use `pd.merge` or `pd.concat` over manual stitching
- For very large data: prefer `polars` or chunked pandas

## Logging vs printing
- Use `logging` in libraries / production
- `print` is fine in notebooks and scripts

## See also
- `rules/snowflake-sql-style.md`
- `skills/logistic-regression/`, `skills/linear-regression/`, etc. for modeling
