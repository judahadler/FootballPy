import pandas as pd
import nfl_data_py as nfl

if __name__ == '__main__':
    #years = list(range(1999, 2024))
    pbp_py = nfl.import_pbp_data([2023])
    filter_crit = 'play_type == "pass" & air_yards.notnull()'

    pbp_py_p = (
        pbp_py.query(filter_crit)
        .groupby(["passer_id", "passer"])
        .agg({"air_yards": ["count", "mean"]})
    )

    print(pbp_py_p.to_string())

    pbp_py_p.columns = list(map("_".join, pbp_py_p.columns.values))
    sort_crit = "air_yards_count > 100"
    print(
        pbp_py_p.query(sort_crit)
        .sort_values(by="air_yards_mean", ascending=[False])
        .to_string()
    )