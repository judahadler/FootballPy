import nfl_data_py as nfl
import seaborn as sns


if __name__ == '__main__':
    # Prepare Penalty Data
    sns.set_theme(style="whitegrid", palette="colorblind")
    seasons = range(2013, 2023 + 1)
    pbp = nfl.import_pbp_data(seasons)

    pbp_juszczyk = pbp[pbp['receiver_player_name'] == 'K.Juszczyk']
    pbp_juszczyk_filtered = pbp_juszczyk[['receiver_player_name', 'game_id', 'season', 'air_yards']]
    pbp_juszczyk_filtered = pbp_juszczyk_filtered[pbp_juszczyk_filtered['air_yards'] > 20]
    pbp_juszczyk_filtered_sorted = pbp_juszczyk_filtered.sort_values(by='air_yards', ascending=False)


    print(pbp_juszczyk_filtered_sorted.to_string())