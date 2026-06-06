"""
EDA Notebook Template

Standard structure for an exploratory data analysis notebook.
Save as .py for version control, convert to .ipynb via jupytext or paste-import.

Sections:
    1. Setup & data load
    2. Sanity checks (shape, types, missing, duplicates)
    3. Univariate distributions
    4. Target relationship (if supervised problem)
    5. Bivariate / correlation exploration
    6. Time-based patterns
    7. Key takeaways
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")
pd.set_option("display.max_columns", 50)
pd.set_option("display.float_format", "{:.4f}".format)


# %% [markdown]
# # EDA: <dataset name>
#
# **Analyst:** <your name>
# **Date:** <YYYY-MM-DD>
# **Goal:** <one sentence>
#
# ## TL;DR
# <fill in after analysis>

# %% Section 1: Load data
INPUT_PATH = "<path/to/data.csv>"
df = pd.read_csv(INPUT_PATH)
print(f"Shape: {df.shape}")
df.head()

# %% Section 2: Sanity checks
print("Dtypes:")
print(df.dtypes)
print("\nMissing values:")
print(df.isnull().sum())
print(f"\nDuplicate rows: {df.duplicated().sum()}")
print(f"\nDate range: {df['<time_col>'].min()} → {df['<time_col>'].max()}")

# %% Section 3: Univariate
for col in df.select_dtypes(include=["int64", "float64"]).columns[:10]:
    fig, ax = plt.subplots(1, 2, figsize=(10, 3))
    df[col].hist(ax=ax[0], bins=40)
    ax[0].set_title(f"{col} — histogram")
    df[col].plot.box(ax=ax[1])
    ax[1].set_title(f"{col} — boxplot")
    plt.tight_layout()
    plt.show()

# %% Section 4: Target relationship (replace <target> with your variable)
TARGET = "<target>"

if TARGET in df.columns:
    for col in df.select_dtypes(include=["int64", "float64"]).columns:
        if col == TARGET:
            continue
        fig, ax = plt.subplots(figsize=(6, 4))
        df.plot.scatter(x=col, y=TARGET, alpha=0.3, ax=ax)
        ax.set_title(f"{col} vs {TARGET}")
        plt.show()

# %% Section 5: Correlation heatmap
numeric = df.select_dtypes(include=["int64", "float64"])
if len(numeric.columns) > 1:
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(numeric.corr(), annot=True, fmt=".2f", center=0, cmap="RdBu_r", ax=ax)
    ax.set_title("Correlation matrix")
    plt.tight_layout()
    plt.show()

# %% Section 6: Time-based patterns
TIME_COL = "<time_col>"

if TIME_COL in df.columns:
    df[TIME_COL] = pd.to_datetime(df[TIME_COL])
    daily = df.groupby(df[TIME_COL].dt.date).size()
    fig, ax = plt.subplots(figsize=(12, 4))
    daily.plot(ax=ax)
    ax.set_title("Daily row count")
    ax.set_ylabel("rows")
    plt.show()

    if TARGET in df.columns:
        daily_target = df.groupby(df[TIME_COL].dt.date)[TARGET].mean()
        fig, ax = plt.subplots(figsize=(12, 4))
        daily_target.plot(ax=ax)
        ax.set_title(f"Daily mean of {TARGET}")
        plt.show()

# %% [markdown]
# ## Key takeaways
#
# 1. **Shape:** <N rows × M cols, date range>
# 2. **Data quality:** <issues found>
# 3. **Distribution:** <skew, outliers, surprises>
# 4. **Target:** <if applicable: relationships found>
# 5. **Next steps:** <what to do next — feature engineering, modeling, etc.>
