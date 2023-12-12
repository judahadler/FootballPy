import nfl_data_py as nfl
import pandas as pd

def findQuarterEndScore(allPlays, game_id):
    df = allPlays[
        (allPlays['game_id'] == game_id) & ((allPlays['quarter_end'] == 1) | (allPlays['game_seconds_remaining'] == 0))]
    dfNew = df[
        ['game_id', 'play_id', 'home_team', 'away_team', 'total_home_score', 'total_away_score', 'qtr', 'quarter_end',
         'result']]
    return dfNew

def createQuarterDifferentials(allPlays, game_id):
    df = findQuarterEndScore(allPlays, game_id)
    winner = ''
    result = df['result']

    if result.iloc[0] < 0:
        winner = df['away_team'].iloc[0]
    else:
        winner = df['home_team'].iloc[0]

    return winner

if __name__ == '__main__':
    years = list(range(1999, 2024))
    allPlays = nfl.import_pbp_data([2022])
    game_id = '2022_01_BAL_NYJ'
    print(findQuarterEndScore(allPlays, game_id).to_string())
    print(createQuarterDifferentials(allPlays, game_id))