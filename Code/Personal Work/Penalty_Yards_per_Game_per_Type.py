import nfl_data_py as nfl
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

# This code attempts to generate a scatter plot with trend lines to show the trends of the top N most called penalties
# since 2000

# TODO: See how the penalty type rankings changed over time - zoom in on years around 2011 when league dynamic changed
#  also check defensive holding on run vs pass - curious what is more

if __name__ == '__main__':
    # Prepare Penalty Data
    pd.set_option('display.max_columns', None)
    sns.set_theme(style="whitegrid", palette="colorblind")
    seasons = range(2000, 2023 + 1)
    pbp = nfl.import_pbp_data(seasons)

    filtered_pbp = pbp[pbp['penalty'] == 1]
    # Added to check only defensive penalties
    filtered_pbp = filtered_pbp[filtered_pbp['penalty_team'] == filtered_pbp['posteam']]

    # Get total games per season
    total_games_per_season = pbp.groupby('season').agg({'game_id': 'nunique'}).reset_index()
    total_games_per_season = total_games_per_season.rename(columns={"game_id": "total_games"})

    # Get total penalty calls per type grouped by season
    pbp_penalty_season_total = filtered_pbp.groupby(['penalty_type', 'season']).agg({'penalty_yards': ['sum'], 'penalty': ['sum']}).reset_index()
    # Flatten columns
    pbp_penalty_season_total.columns = ['penalty_type', 'season', 'total_yards', 'total_calls']

    # Merge the two so that we can calculate the mean (couldn't use an agg function for 'mean' since the dataframe
    # ignored games where no flag for a given type were called
    pbp_penalties_games = pd.merge(total_games_per_season, pbp_penalty_season_total, on=['season'], how='inner')

    # Reorder columns
    column_order = ['season', 'penalty_type', 'total_calls', 'total_yards', 'total_games']
    pbp_penalties_games = pbp_penalties_games[column_order]

    # Add column for penalty_calls_per_game, penalty_yards_per_game, and penalty_yards_per_call
    pbp_penalties_games['penalty_calls_per_game'] = pbp_penalties_games['total_calls'] / pbp_penalties_games['total_games']
    pbp_penalties_games['penalty_yards_per_game'] = pbp_penalties_games['total_yards'] / pbp_penalties_games['total_games']
    pbp_penalties_games['penalty_yards_per_call'] = pbp_penalties_games['total_yards'] / pbp_penalties_games['total_calls']

    # Find N penalty types with most calls per game
    pbp_penalty_season_total = pbp_penalties_games.groupby('penalty_type').agg({'penalty_calls_per_game': ['mean'],
                                                                                'penalty_yards_per_call': ['mean']}).reset_index()

    # Flatten columns
    pbp_penalty_season_total.columns = ['penalty_type', 'penalty_calls_per_game_mean', 'penalty_yards_per_call_mean']

    #Print in descending order of penalty calls
    pbp_penalty_season_total = pbp_penalty_season_total.sort_values(by='penalty_calls_per_game_mean', ascending=False)
    print(pbp_penalty_season_total.to_string())

    # Find top penalties
    top_penalty_types = pbp_penalty_season_total.nlargest(10, 'penalty_calls_per_game_mean')['penalty_type']
    pbp_penalty_filtered = pbp_penalties_games[pbp_penalties_games['penalty_type'].isin(top_penalty_types)]
    #print(pbp_penalty_filtered.to_string())

    #Create a plot to visualize the trend of mean penalty yards per penalty type over seasons
    sns.lmplot(data=pbp_penalty_filtered,
               x="season",
               y="penalty_calls_per_game",
               hue="penalty_type",  # Use hue for different penalty types
               markers='o',
               scatter_kws={"s": 25},
               )
    plt.title("Defensive Penalty Calls per Game for Top Penalty Types")
    plt.show()



