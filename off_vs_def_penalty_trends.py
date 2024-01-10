import nfl_data_py as nfl
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf


if __name__ == '__main__':
    # Prepare Rushing Data
    sns.set_theme(style="whitegrid", palette="colorblind")
    seasons = range(2000, 2023 + 1)
    pbp = nfl.import_pbp_data(seasons)

    pbp_penalty = pbp[pbp['penalty'] == 1].copy()
    pbp_penalty.loc[:, "penalty_side"] = np.where(pbp_penalty["penalty_team"] == pbp_penalty["defteam"], "defense", "offense")
    pbp_penalty_sides_game = pbp_penalty.groupby(['game_id', 'season', "penalty_side"]).agg(
        {'penalty_yards': 'sum'}).reset_index()
    #print(pbp_penalty_sides_game)

    pbp_penalty_sides_game_season = pbp_penalty_sides_game\
        .groupby(['season', 'penalty_side'])\
        .agg({"penalty_yards": ["mean"]})\
        .reset_index()
    #print(pbp_penalty_sides_game_season)

    pbp_penalty_sides_game_season.columns = list(map("_".join, pbp_penalty_sides_game_season.columns))
    pbp_penalty_sides_game_season.reset_index(inplace=True)
    pbp_penalty_sides_game_season = pbp_penalty_sides_game_season.rename(columns={
        "penalty_yards_mean": "penalty_yards_per_game",
        "season_": "season",
        "penalty_side_": "penalty_side"
        })
    print(pbp_penalty_sides_game_season)


    plt.figure(figsize=(12, 6))
    sns.lineplot(data=pbp_penalty_sides_game_season, x='season', y='penalty_yards_per_game', hue='penalty_side')
    plt.title('Offense and Defense Penalty Yards Per Game Over Seasons')
    plt.xlabel('Season')
    plt.ylabel('Penalty Yards Per Game')
    plt.show()


