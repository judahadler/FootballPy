import nfl_data_py as nfl
import seaborn as sns
import matplotlib.pyplot as plt

# This code displays the total points scored per game per season dating back to 2000

if __name__ == '__main__':
    sns.set_theme(style="whitegrid", palette="colorblind")
    seasons = range(2000, 2023 + 1)
    pbp = nfl.import_pbp_data(seasons)

    pbp_scores = pbp.groupby('game_id')[['total', 'season']].first().reset_index()

    pbp_scores_season = pbp_scores.groupby('season').agg({"total": ["sum", "count"]})

    pbp_scores_season.columns = list(map("_".join, pbp_scores_season.columns))
    pbp_scores_season.reset_index(inplace=True)

    pbp_scores_season["ppg"] = pbp_scores_season['total_sum'] / pbp_scores_season['total_count']

    print(pbp_scores_season)

    sns.lmplot(data=pbp_scores_season,
               x="season",
               y="ppg",  # Use the calculated points per game
               markers='o',  # Use markers for each point
               scatter_kws={"s": 100},  # Adjust marker size
               line_kws={"color": "red"}  # Add a red regression line
               )
    plt.title("Points Per Game Over Seasons")
    plt.show()



