import nfl_data_py as nfl
import seaborn as sns
import matplotlib.pyplot as plt

# This code attempts to visualize the penalty yards per game for each season dating back to 2000 (No trends jumped off
# the page)

if __name__ == '__main__':
    # Prepare Penalty Data
    sns.set_theme(style="whitegrid", palette="colorblind")
    seasons = range(2000, 2023 + 1)
    pbp = nfl.import_pbp_data(seasons)

    pbp_penalty = pbp[pbp['penalty'] == 1]
    pbp_pass_interference = pbp_penalty[pbp_penalty['penalty_type'] == 'Defensive Pass Interference']
    pbp_pass_interference_game = pbp_pass_interference.groupby(['game_id', 'season']).agg(
        {'penalty_yards': 'sum'}).reset_index()

    pbp_pass_interference_season = pbp_pass_interference_game.groupby(['season']).agg({"penalty_yards": ["mean"]})
    print(pbp_pass_interference_season)
    pbp_pass_interference_season.columns = list(map("_".join, pbp_pass_interference_season.columns))
    pbp_pass_interference_season.reset_index(inplace=True)

    # Create a plot to visualize the trend of mean penalty yards per PI over seasons
    sns.lineplot(data=pbp_pass_interference_season,
               x="season",
               y="penalty_yards_mean",
               markers='o'
               )
    plt.title("Mean Penalty Yards Per PI Over Seasons")
    plt.show()



