import nfl_data_py as nfl
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

def getDrive(allPlays, drive_num, game_id):
    df = allPlays[(allPlays['game_id'] == game_id) & (allPlays['drive'] == drive_num)]
    dfNew = df[['game_id', 'play_id', 'defteam', 'posteam', 'drive', 'series_result', 'extra_point_result', 'two_point_conv_result','drive_play_id_ended']]
    #This next snippet will figure out which rows are NOT duplicates a
    last_rows = ~dfNew.duplicated(subset=['drive', 'game_id'], keep='last')
    dfNew = dfNew[last_rows]
    return dfNew

def getTeamGameDrives(allPlays, game_id, team):
    df = allPlays[(allPlays['game_id'] == game_id) & (allPlays['posteam'] == team)]
    return df[['game_id','play_id','defteam', 'posteam', 'yardline_100', 'half_seconds_remaining', 'drive', 'series_result', 'drive_ended_with_score', 'drive_play_id_ended']]

def getDriveIdOfTurnovers(allPlays, game_id, team):
    df = allPlays[(allPlays['game_id'] == game_id) & (allPlays['defteam'] == team) & (allPlays['series_result'] == 'Turnover')]
    dfNew = df[['play_id','defteam', 'posteam', 'yardline_100', 'half_seconds_remaining', 'drive', 'series_result', 'drive_ended_with_score', 'drive_play_id_ended']]
    return dfNew.drop_duplicates(subset=['drive'])

def getAllTeamTurnoverDriveIds(allPlays, team):
    df = allPlays[(allPlays['defteam'] == team) & (allPlays['series_result'] == 'Turnover')]
    dfNew = df[['game_id','play_id', 'defteam', 'posteam', 'drive', 'series_result', 'drive_play_id_ended']]
    dfNew = dfNew.drop_duplicates(subset=['drive', 'game_id'])
    return dfNew[['game_id', 'drive']]

def getAllDrivesAfterTurnover(allPlays, team):
    driveResults = pd.DataFrame()
    ids = getAllTeamTurnoverDriveIds(allPlays, team)
    ids = ids.reset_index()
    
    for index, row in ids.iterrows():
        #print(row)
        nextDrive = float(row['drive']) + 1.0
        game_id = row['game_id']
        #print(nextDrive)
        teamDrive = getDrive(allPlays, nextDrive, game_id)
        driveResults = pd.concat([driveResults, teamDrive])

    return driveResults

def calculateTeamTurnoverPointsAverage(allPlays, team):
    driveResults = getAllDrivesAfterTurnover(allPlays, team)
    pointsTotal = 0
    drivesTotal = 0
    for index, row in driveResults.iterrows():
        if row['series_result'] == 'QB kneel' or row['series_result'] == 'End of half':
            continue
        elif row['series_result'] == 'Field goal':
            pointsTotal += 3
        elif row['series_result'] == 'Touchdown':
            if row['extra_point_result'] == 'good':
                pointsTotal += 7
            elif row['two_point_conv_result'] == 'good':
                pointsTotal += 8
            else:
                pointsTotal += 6

        drivesTotal += 1
    if drivesTotal == 0:
        return 0
    pointValue = pointsTotal/drivesTotal
    return pointValue

def calculateTeamTurnoverPointsAverageConcurrent(allPlays, teams, num_threads=10):
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Calculate point values concurrently for each team
        results = list(executor.map(calculateTeamTurnoverPointsAverage, [allPlays] * len(teams), teams))

    return results

# average points following a turnover ended up equating to 2.607978650057921
def calculateTotalTurnoverPointValue(allPlays, num_threads=10):
    teams = list(allPlays.posteam.unique())
    team_point_values = calculateTeamTurnoverPointsAverageConcurrent(allPlays, teams, num_threads)

    averageValue = sum(team_point_values) / len(teams)
    return averageValue

if __name__ == '__main__':
    years = list(range(1999, 2024))
    allPlays = nfl.import_pbp_data(years)
    print(calculateTotalTurnoverPointValue(allPlays, num_threads=10))
