import nfl_data_py as nfl
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

if __name__ == '__main__':
    # Prepare Penalty Data
    sns.set_theme(style="whitegrid", palette="colorblind")
    seasons = range(2023, 2023 + 1)
    pbp = nfl.import_pbp_data(seasons)

    filtered_pbp = pbp[pbp['game_id'] == '2023_05_NYJ_DEN']

    columns_to_select = ['play_id', 'posteam', 'defteam', 'qtr', 'drive', 'total_home_score', 'total_away_score',
                         'series_result', 'extra_point_result', 'two_point_conv_result']

    filtered_pbp_subset = filtered_pbp.loc[:, columns_to_select]

    print(filtered_pbp_subset.to_string())
