"""Descriptive statistics, correlations and basic regression."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..core.io import load_data, require_columns, write_tables
from ..core.plugin import Plugin
from ..core.provenance import RunLog
from ..stats.robust import wls_cluster
from ._common import add_common, split_list


def cmd_summary(a):
    df = load_data(a.data)
    cols = split_list(a.vars) or list(df.columns)
    require_columns(df, cols)
    with RunLog(a.out, "describe", "summary", vars(a), None) as run:
        run.add_input(a.data)
        d = df[cols]
        num = d.select_dtypes("number")
        tables = {}
        if not num.empty:
            t = num.describe().T
            t["missing"] = num.isna().sum()
            tables["numeric"] = t
        cat = d.select_dtypes(exclude="number")
        if not cat.empty:
            rows = []
            for c in cat.columns:
                vc = cat[c].value_counts(dropna=False)
                for lv, n in vc.items():
                    rows.append({"variable": c, "level": str(lv), "n": int(n), "percent": 100 * n / len(cat)})
            tables["categorical"] = pd.DataFrame(rows).set_index(["variable", "level"])
        if a.by:
            require_columns(df, [a.by])
            tables[f"means_by_{a.by}"] = df.groupby(a.by)[list(num.columns.drop(a.by, errors="ignore"))].agg(["count", "mean", "std"])
        write_tables(run, tables, "summary")


def cmd_corr(a):
    df = load_data(a.data)
    cols = split_list(a.vars) or list(df.select_dtypes("number").columns)
    require_columns(df, cols)
    with RunLog(a.out, "describe", "corr", vars(a), None) as run:
        run.add_input(a.data)
        write_tables(run, {"correlation": df[cols].corr(method=a.method), "n_pairwise": df[cols].notna().astype(int).T @ df[cols].notna().astype(int)}, "correlation")


def cmd_regress(a):
    df = load_data(a.data)
    xs = split_list(a.x)
    need = [a.y] + xs + ([a.cluster] if a.cluster else []) + ([a.weight] if a.weight else [])
    require_columns(df, need)
    d = df[need].dropna()
    with RunLog(a.out, "describe", "regress", vars(a), None) as run:
        run.add_input(a.data)
        if len(d) < len(df):
            run.warn(f"{len(df) - len(d)} rows dropped for missing values (listwise).")
        X = pd.get_dummies(d[xs], drop_first=True, dtype=float)
        names = ["const"] + list(X.columns)
        Xm = np.column_stack([np.ones(len(d)), X.to_numpy(float)])
        cl = d[a.cluster].to_numpy() if a.cluster else None
        w = d[a.weight].to_numpy(float) if a.weight else None
        vt = a.vcov if a.cluster else "CR1"
        if not a.cluster:
            run.warn("No --cluster given: using heteroskedasticity-robust (each row its own cluster).")
        res = wls_cluster(d[a.y].to_numpy(float), Xm, w=w, cluster=cl, vcov_type=vt, names=names)
        rows = []
        for j, nm in enumerate(names):
            c = np.zeros(len(names)); c[j] = 1
            r = res.contrast(c)
            rows.append({"term": nm, **{k: r[k] for k in ("estimate", "se", "t", "p", "ci_low", "ci_high")}})
        info = pd.DataFrame({"value": [res.n, res.n_clusters, res.vcov_type, res.df]}, index=["n", "clusters", "vcov", "df"])
        write_tables(run, {"coefficients": pd.DataFrame(rows).set_index("term"), "model": info}, "regression")


class Describe(Plugin):
    name = "describe"
    help = "Descriptive statistics, correlations, linear regression with cluster-robust SEs"

    def register(self, sub):
        p = add_common(sub.add_parser("summary", help="Descriptive tables"))
        p.add_argument("--vars", help="Comma-separated columns (default: all)")
        p.add_argument("--by", help="Group means by this column")
        p.set_defaults(func=cmd_summary)

        p = add_common(sub.add_parser("corr", help="Correlation matrix"))
        p.add_argument("--vars")
        p.add_argument("--method", default="pearson", choices=["pearson", "spearman", "kendall"])
        p.set_defaults(func=cmd_corr)

        p = add_common(sub.add_parser("regress", help="Linear regression (optionally weighted, cluster-robust)"))
        p.add_argument("--y", required=True)
        p.add_argument("--x", required=True, help="Comma-separated predictors")
        p.add_argument("--cluster")
        p.add_argument("--weight")
        p.add_argument("--vcov", default="CR2", choices=["CR0", "CR1", "CR2"])
        p.set_defaults(func=cmd_regress)


PLUGIN = Describe()
