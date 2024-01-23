import nfl_data_py as nfl
import seaborn as sns

# This code attempts to show which quarterbacks get more roughing the passer calls
# As it stands - no conclusion can be drawn regarding generosity of calls - if anything it seems to show a relationship
# between time to throw and roughing the passer or qb hits and roughing the passer

# TODO: Change the metric to roughing call per passing play or per qb hit - not roughing call per game

if __name__ == '__main__':
    # Prepare Penalty Data
    sns.set_theme(style="whitegrid", palette="colorblind")
    seasons = range(2011, 2023 + 1)
    pbp = nfl.import_pbp_data(seasons)

    # Get all roughing the passer calls
    pbp_roughing_game = pbp.groupby(['game_id', 'season', 'passer', 'passer_id'], as_index=False)['penalty_type'] \
        .apply(lambda x: (x == 'Roughing the Passer').sum()) \
        .fillna(0)
    pbp_roughing_game = pbp_roughing_game.rename(columns={'penalty_type': 'roughing_calls'})

    # Get roughing the passer calls per passer per game
    pbp_roughing_game_season = pbp_roughing_game.groupby(['passer', 'passer_id']).agg({"roughing_calls": ["sum", "count"]})
    pbp_roughing_game_season.columns = [f"{col[0]}_{col[1]}" if col[1] != '' else col[0] for col in pbp_roughing_game_season.columns]
    pbp_roughing_game_season = pbp_roughing_game_season.query("roughing_calls_count > 50")
    pbp_roughing_game_season.reset_index(inplace=True)

    # Rename the count column to 'games'
    pbp_roughing_game_season = pbp_roughing_game_season.rename(columns={'roughing_calls_count': 'games'})

    # Calculate roughing_calls_per_game
    pbp_roughing_game_season['roughing_calls_per_game'] = pbp_roughing_game_season['roughing_calls_sum'] / pbp_roughing_game_season['games']
    pbp_roughing_game_season_most = pbp_roughing_game_season.sort_values(by='roughing_calls_per_game', ascending=False)
    pbp_roughing_game_season_least = pbp_roughing_game_season.sort_values(by='roughing_calls_per_game', ascending=True)

    print("Most:")
    print(pbp_roughing_game_season_most[['passer', 'roughing_calls_per_game', 'games']])
