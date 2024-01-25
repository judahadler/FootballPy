import nfl_data_py as nfl
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# This code attempts to assign a simple point value to a turnover.  By averaging the points scored on drives following
# turnovers, we can see the offensive value.  The difficult part is assessing the defensive point value as well.
#  TODO: I also need to account for turnovers on the last play of halves/games - cant count the following drive

#Find total points scored for a given season
def getPointsPerSeason(pbp, season):
    searchSeason = pbp[pbp['season'] == season]
    gameTotal = searchSeason.groupby(['season', 'game_id']).agg({'total': ['first']}).reset_index()
    gameTotal.columns = ['season', 'game_id', 'total_pts']
    seasonTotal = gameTotal.groupby('season').agg({'total_pts': ['sum']}).reset_index()
    seasonTotal.columns = ['season', 'total_points_scored_in_season']
    return seasonTotal

#Find the drive ids for all turnovers in a season
def getTurnoverDriveIdsPerSeason(pbp, season):
    pbp_tos = pbp[((pbp['season'] == season) &
                   ((pbp['drive_end_transition'] == 'INTERCEPTION') | (pbp['drive_end_transition'] == 'FUMBLE')) &
                   (pbp['return_touchdown'] == 0))]
    pbp_tos_filtered = pbp_tos[['game_id', 'season', 'drive']]

    pbp_tos_filtered.loc[:, 'drive'] = pbp_tos_filtered['drive'].fillna(100.0)

    return pbp_tos_filtered


#Get drive reults for all drives following a turnover
def getResultsPostTurnoverDrives(pbp, season):
    turnover_df = getTurnoverDriveIdsPerSeason(pbp, season)
    turnover_df['drive'] += 1
    # Merge with the original DataFrame based on 'season', 'drive', and 'game_id'
    postTurnOverDrives = pd.merge(turnover_df, pbp, on=['game_id', 'season', 'drive'], how='left')
    postTurnOverDrivesFiltered = postTurnOverDrives[['season', 'game_id', 'defteam', 'posteam', 'qtr', 'drive',
                                                    'drive_end_transition', 'extra_point_result', 'two_point_conv_result']]

    postTurnOverDrivesSimplified = postTurnOverDrivesFiltered.groupby(['season', 'game_id', 'drive']).agg('last')

    # Define a function to map 'TOUCHDOWN' to 6 and other values to 0
    def map_drive_result(value):
        if value == 'TOUCHDOWN':
            return 6
        elif value == 'FIELD_GOAL':
            return 3
        else:
            return 0

    # Define a function to map 'good' to 1 and other values to 0
    def map_extra_point_result(value):
        return 1 if value == 'good' else 0

    # Define a function to map 'success' to 2 and other values to 0
    def map_two_point_result(value):
        return 2 if value == 'success' else 0

    # Rework 'point after' columns to assign points scored on that play
    postTurnOverDrivesSimplified['drive_end_transition'] = \
        postTurnOverDrivesSimplified['drive_end_transition'].apply(map_drive_result)
    postTurnOverDrivesSimplified['extra_point_result'] = \
        postTurnOverDrivesSimplified['extra_point_result'].apply(map_extra_point_result)
    postTurnOverDrivesSimplified['two_point_conv_result'] = \
        postTurnOverDrivesSimplified['two_point_conv_result'].apply(map_two_point_result)

    postTurnOverDrivesSimplified['total_off_points'] = postTurnOverDrivesSimplified['drive_end_transition'] + \
                                                   postTurnOverDrivesSimplified['extra_point_result'] + \
                                                   postTurnOverDrivesSimplified['two_point_conv_result']

    postTurnOverDrivesAggs = postTurnOverDrivesSimplified \
        .groupby('season') \
        .agg({'total_off_points': 'sum', 'defteam': 'size'}).reset_index()

    postTurnOverDrivesAggs.rename(columns={'defteam': 'total_drives'}, inplace=True)

    # Find points scored defensively off of turnovers
    defResult = findDefPtsPerSeason(pbp, season)
    result = pd.merge(postTurnOverDrivesAggs, defResult, on=['season'], how='inner')
    result['total_turnover_points'] = result['total_off_points'] + result['total_def_points']

    result['pts_per_drive_post_TO'] = result['total_turnover_points'] / result['total_drives']

    return result

#Calculate defensive points scored per season - doesnt include extra points and 2pointconvs after return tds
def findDefPtsPerSeason(pbp, season):
    pbp_tos = pbp[((pbp['season'] == season) &
                   ((pbp['drive_end_transition'] == 'INTERCEPTION') | (pbp['drive_end_transition'] == 'FUMBLE')) &
                   (pbp['return_touchdown'] == 1))]

    pbp_def_points = pd.DataFrame({'season': [season], 'total_def_points': [len(pbp_tos) * 6]})

    return pbp_def_points

#process a single season
def process_season(season):
    pbp = nfl.import_pbp_data([season])
    getPointsPerSeason(pbp, 2023)
    toData = getResultsPostTurnoverDrives(pbp, season)
    allPointsScored = getPointsPerSeason(pbp, season)
    result = pd.merge(toData, allPointsScored, on=['season'], how='inner')
    result['percentageOfPointsScoredOffTurnovers'] = result['total_turnover_points'] / result['total_points_scored_in_season'] * 100
    return result

def process_multiple_seasons(seasons):
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_season, seasons))

    combined_result = pd.concat(results, ignore_index=True)
    return combined_result


if __name__ == '__main__':
    years = list(range(1999, 2023 + 1))
    combined_result_df = process_multiple_seasons(years)
    print(combined_result_df.to_string())
    tunover_point_average = combined_result_df['total_turnover_points'].sum() \
                            / combined_result_df['total_drives'].sum()
    print(f"Average Points Following a Turnover: {tunover_point_average}")

