import nfl_data_py as nfl
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# This code attempts to assign a simple point value to a turnover.  By averaging the points scored on drives following
# turnovers, we can see the offensive value.  The difficult part is assessing the defensive point value as well.

def getPlayAfterDefTD(allPlays, game_id, home_score, away_score):
    df = allPlays[(allPlays['series_result'] == 'Opp touchdown') &
                  (pd.isna(allPlays['drive'])) &
                  (allPlays['game_id'] == game_id) &
                  (abs(allPlays['total_home_score'] + allPlays['total_away_score'] - home_score - away_score) <= 2)]

    dfNew = df[['game_id', 'defteam', 'posteam', 'drive', 'series_result', 'extra_point_result',
                'two_point_conv_result', 'qtr']]

    return dfNew

# Retrieves information about a specific drive in a game.
def getDrive(allPlays, drive_num, game_id):
    #Get all rows with a given gameId and drive number
    df = allPlays[(allPlays['game_id'] == game_id) & (allPlays['drive'] == drive_num)]
    dfNew = df[['game_id', 'defteam', 'posteam', 'drive', 'series_result', 'extra_point_result',
                'two_point_conv_result', 'qtr']]
    # This next snippet will figure out which rows are NOT duplicates a
    last_rows = ~dfNew.duplicated(subset=['drive', 'game_id'], keep='last')
    dfNew = dfNew[last_rows]
    return dfNew

# Retrieves information about all drives of a specific game.
def getGameDrives(allPlays, game_id):
    df = allPlays[(allPlays['game_id'] == game_id)]
    return df[
        ['game_id', 'play_id', 'defteam', 'posteam', 'yardline_100', 'half_seconds_remaining', 'drive', 'series_result',
         'drive_ended_with_score']]

# Retrieves drive IDs where turnovers occurred.
def getDriveIdOfTurnoversSeason(allPlays, game_id, season):
    #Get all rows where a team forced a turnover in a given game
    df = allPlays[
        (allPlays['game_id'] == game_id) & (allPlays['series_result'] == 'Turnover') & (allPlays['season'] == season)]
    dfNew = df[['season', 'play_id', 'defteam', 'posteam', 'yardline_100', 'half_seconds_remaining',
                'drive', 'series_result', 'drive_ended_with_score', 'qtr']]
    return dfNew.drop_duplicates(subset=['drive'])

# Retrieves all drive IDs where a defense caused a turnover.
def getAllTurnoverDriveIdsSeason(allPlays, season):
    # Check to also keep defensive tds
    df = allPlays[((allPlays['series_result'] == 'Turnover') | (allPlays['series_result'] == 'Opp touchdown') &
                   ((allPlays['interception'] == 1) | (allPlays['fumble'] == 1)) & (allPlays['season'] == season))]

    dfNew = df[['season', 'game_id', 'play_id', 'defteam', 'posteam', 'drive', 'series_result', 'extra_point_result',
                'two_point_conv_result', 'qtr', 'return_touchdown', 'total_home_score', 'total_away_score']]
    dfNew = dfNew.drop_duplicates(subset=['drive', 'game_id'])
    return dfNew[['season', 'game_id', 'drive', 'series_result', 'defteam', 'posteam', 'extra_point_result',
                  'two_point_conv_result', 'qtr', 'return_touchdown', 'total_home_score', 'total_away_score']]

# Retrieves information about all drives that occurred after turnovers.
def getAllDrivesAfterTurnover(allPlays, season):

    driveResults = pd.DataFrame()
    ids = getAllTurnoverDriveIdsSeason(allPlays, season)
    ids = ids.reset_index()

    for index, row in ids.iterrows():
        # Look for defensive Touchdowns
        if row['series_result'] == "Opp touchdown" and \
                (not pd.isna(row['drive'])) and \
                (not row['defteam'] == None) and \
                not (allPlays['return_touchdown'].iloc[0] == 1):
            #Get the attempt after the turnover
            attemptPlay = getPlayAfterDefTD(allPlays, row['game_id'], row['total_home_score'], row['total_away_score'])

            #Create new row to represent 'drive' of the defTD
            row_data = {
                'game_id': row['game_id'],
                'defteam': row['defteam'],
                'posteam': row['posteam'],
                'drive': row['drive'],
                'series_result': 'Touchdown',
                'extra_point_result': attemptPlay['extra_point_result'].iloc[0] if not attemptPlay.empty else None,
                'two_point_conv_result': attemptPlay['two_point_conv_result'].iloc[0] if not attemptPlay.empty else None,
                'qtr': row['qtr']
            }
            # Create a DataFrame with a single row
            newDrive = pd.DataFrame([row_data])
            driveResults = pd.concat([driveResults, newDrive])
            continue

        qtr = row['qtr']
        nextDrive = float(row['drive']) + 1.0
        game_id = row['game_id']
        # print(nextDrive)
        teamDrive = getDrive(allPlays, nextDrive, game_id)
        #Eliminate any turnovers on last play of half
        if not teamDrive.empty and (
                (qtr == 2 and teamDrive['qtr'].iloc[0] == 3) or (qtr == 4 and teamDrive['qtr'].iloc[0] == 5)):
            continue
        driveResults = pd.concat([driveResults, teamDrive])

    return driveResults

# average points following a turnover ended up equating to 2.9600137909440063 - this does not factor in pick 6's
def calculateTurnoverPointsAveragePerSeason(allPlays, season):
    driveResults = getAllDrivesAfterTurnover(allPlays, season)
    pointsTotal = 0
    drivesTotal = 0
    for index, row in driveResults.iterrows():
        if row['series_result'] == 'QB kneel':
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
    pointValue = pointsTotal / drivesTotal
    season_turnover_data = pd.DataFrame({
        'season': [season],
        'total_post_turnover_drives': [drivesTotal],
        'total_post_turnover_points': [pointsTotal],
        'average_pts_following_turnover': [pointValue]
    })

    return season_turnover_data

def calculateSeasonTurnoverPointsAverageConcurrent(allPlays, seasons, num_threads=10):
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Calculate point values concurrently for each season
        results = list(executor.map(calculateTurnoverPointsAveragePerSeason, [allPlays] * len(seasons), seasons))

    return results

# average points following a turnover ended up equating to 2.9600137909440063 - this does not factor in pick 6's
def calculateTotalTurnoverPointValue(allPlays, num_threads=10):
    seasons = list(range(2020, 2023 + 1))
    season_point_values = calculateSeasonTurnoverPointsAverageConcurrent(allPlays, seasons, num_threads)

    # Concatenate the DataFrames for each season into one
    combined_df = pd.concat(season_point_values, ignore_index=True)

    return combined_df


if __name__ == '__main__':
    years = list(range(2020, 2023 + 1))
    allPlays = nfl.import_pbp_data(years)
    print(calculateTotalTurnoverPointValue(allPlays, 10).to_string())
