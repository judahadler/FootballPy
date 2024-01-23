import nfl_data_py as nfl
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

# This code attempts to highlight which afc east teams were more or less disciplined in penalty yards per game in a
# given season compared to each other and compared to the league average

if __name__ == '__main__':
    # Prepare Penalty Data
    sns.set_theme(style="whitegrid", palette="colorblind")
    seasons = range(2000, 2023 + 1)
    pbp = nfl.import_pbp_data(seasons)

    filtered_pbp = pbp[pbp['penalty'] == 1]

    pbp_penalty = filtered_pbp.groupby(['game_id', 'penalty_team', 'season']).agg(
        {'penalty_yards': 'sum'}).reset_index()

    penalty_team_means = pbp_penalty.groupby(['penalty_team', 'season']).agg({"penalty_yards": ["sum", "count"]})
    penalty_team_means.columns = list(map("_".join, penalty_team_means.columns))
    penalty_team_means.reset_index(inplace=True)

    penalty_team_means['penalty_yards_per_game'] = penalty_team_means['penalty_yards_sum'] / penalty_team_means[
        'penalty_yards_count']

    teams = ['NE', 'NYJ', 'MIA', 'BUF']
    penalty_team_means_teams = penalty_team_means[penalty_team_means['penalty_team'].isin(teams)]
    league_avg_df = penalty_team_means.groupby('season').agg({"penalty_yards_per_game": "mean"}).reset_index()
    league_avg_df['penalty_team'] = 'league_avg'

    penalty_team_means_final = pd.concat([penalty_team_means_teams, league_avg_df], ignore_index=True)
    penalty_team_means_final = penalty_team_means_final.sort_values(by=['season', 'penalty_team'])
    print(penalty_team_means_final)

    palette = {'NE': 'red', 'NYJ': 'green', 'league_avg': 'purple', 'MIA': 'orange', 'BUF': 'navy'}
    plt.figure(figsize=(12, 6))
    sns.barplot(data=penalty_team_means_final,
                x='season',
                y='penalty_yards_per_game',
                hue='penalty_team',
                palette=palette)

    plt.title('AFC EAST vs League Average Penalty Yards Per Game Over Seasons')
    plt.show()
