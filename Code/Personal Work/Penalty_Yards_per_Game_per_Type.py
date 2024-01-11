import nfl_data_py as nfl
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf


if __name__ == '__main__':
    # Prepare Rushing Data
    sns.set_theme(style="whitegrid", palette="colorblind")
    seasons = range(2000, 2023 + 1)
    pbp = nfl.import_pbp_data(seasons)

    filtered_pbp = pbp[pbp['penalty'] == 1]

    pbp_penalty = filtered_pbp.groupby(['game_id', 'penalty_type', 'season']).agg({'penalty_yards': 'sum'}).reset_index()

    penalty_type_means = pbp_penalty.groupby('penalty_type').agg({"penalty_yards": ["mean"]})
    penalty_type_means.columns = list(map("_".join, penalty_type_means.columns))
    penalty_type_means.reset_index(inplace=True)

    top_penalty_types = penalty_type_means.nlargest(10, 'penalty_yards_mean')['penalty_type']
    pbp_penalty_filtered = pbp_penalty[pbp_penalty['penalty_type'].isin(top_penalty_types)]
    print(pbp_penalty_filtered)

    pbp_penalty_season = pbp_penalty_filtered.groupby(['season', 'penalty_type']).agg({"penalty_yards": ["mean"]})
    pbp_penalty_season.columns = list(map("_".join, pbp_penalty_season.columns))
    pbp_penalty_season.reset_index(inplace=True)

    # Create a plot to visualize the trend of mean penalty yards per penalty type over seasons
    sns.lmplot(data=pbp_penalty_season,
               x="season",
               y="penalty_yards_mean",
               hue="penalty_type",  # Use hue for different penalty types
               markers='o',
               scatter_kws={"s": 25},
               )
    plt.title("Mean Penalty Yards Per Top Penalty Types Over Seasons")
    plt.show()



