import nfl_data_py as nfl
import pandas as pd


def getAllJetsTurnovers(allPlays):

    #important cols:
    #drive, down, yards_gained, ydstogo, play_type, home_team, away_team

    turnovers = 0
    turnoverDriveIds = []
    for ind in allPlays.index:
        if allPlays['defteam'][ind] == "NYJ":
            if allPlays['series_result'][ind] == "Turnover":
                if allPlays['fumble'][ind] or allPlays['interception'][ind]:
                    if (allPlays['game_id'][ind] , allPlays['drive'][ind]) not in turnoverDriveIds:
                        turnoverDriveIds.append((allPlays['game_id'][ind] , allPlays['drive'][ind], allPlays['drive'][ind]))
                        turnovers += 1

    print(turnoverDriveIds)
    print(f"Turnovers: {turnovers}")



def getDriveResult(drive_num, game_id, allPlays):

    return allPlays.loc[
                (allPlays['game_id'] == game_id) & (allPlays['drive'] == drive_num),
                ['game_id', 'drive','series_result']].iloc[0]

def getDrive(allPlays, drive_num, game_id):
    df = allPlays[(allPlays['game_id'] == game_id) & (allPlays['drive'] == drive_num)]
    dfNew = df[['game_id', 'play_id', 'defteam', 'posteam', 'drive', 'series_result', 'extra_point_result', 'two_point_conv_result','drive_play_id_ended']]
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

# average points following a turnover ended up equating to 2.607978650057921
def calculateTotalTurnoverPointValue(allPlays):
    teams = list(allPlays.posteam.unique())
    totalTeams = len(teams)
    totalPointValue = 0
    for team in teams:
        totalPointValue += calculateTeamTurnoverPointsAverage(allPlays, team)

    averageValue = totalPointValue / totalTeams
    return averageValue



if __name__ == '__main__':
    years = list(range(1999, 2024))
    allPlays = nfl.import_pbp_data([2021])
    #print(getAllTeamTurnoverDriveIds(allPlays, 'NYJ').to_string())
    #print(getTeamGameDrives(allPlays, '2022_01_BAL_NYJ', 'NYJ').to_string())
    #print(getDrive(allPlays, '24.0', '2022_01_BAL_NYJ'))
    #print(calculateTeamTurnoverPointsAverage(allPlays, 'NYJ'))
    print(calculateTotalTurnoverPointValue(allPlays))
