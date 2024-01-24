import nfl_data_py as nfl
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

# This code displays the total points scored per drive per season dating back to 2000

# Todo: factor in safeties???

def getTotalDSTPoints(pbp):

    #Filter for all plays where a dst td was scored on that series/play
    pbp_dst_scoring_drives = pbp[(pbp['return_touchdown'] == 1) |
                                 (pbp['series_result'] == "Opp touchdown") &
                                 (pbp['td_team'] != pbp['posteam'])]

    #Only look for the play where the td was scored or the point after was attempted
    filtered_pbp_dst_scoring_drives = pbp_dst_scoring_drives[
        (pbp_dst_scoring_drives['return_touchdown'] == 1) |
        (pbp_dst_scoring_drives['extra_point_result'].notna()) |
        (pbp_dst_scoring_drives['two_point_conv_result'].notna())
        ]

    #Select specific columns
    filtered_pbp_dst_scoring_drives = filtered_pbp_dst_scoring_drives[
        ['game_id', 'season', 'defteam', 'posteam', 'drive',
         'return_touchdown', 'drive_end_transition', 'extra_point_result', 'two_point_conv_result' ]]

    # Define a function to map 'good' to 1 and other values to 0
    def map_extra_point_result(value):
        return 1 if value == 'good' else 0

    # Define a function to map 'success' to 2 and other values to 0
    def map_two_point_result(value):
        return 2 if value == 'success' else 0

    #Rework 'point after' columns to assign points scored on that play
    filtered_pbp_dst_scoring_drives['extra_point_result'] = \
        filtered_pbp_dst_scoring_drives['extra_point_result'].apply(map_extra_point_result)
    filtered_pbp_dst_scoring_drives['two_point_conv_result'] = \
        filtered_pbp_dst_scoring_drives['two_point_conv_result'].apply(map_two_point_result)

    # Designate column for points scored on that play
    filtered_pbp_dst_scoring_drives['points_scored'] = ((filtered_pbp_dst_scoring_drives['return_touchdown'] * 6) +
                                                        (filtered_pbp_dst_scoring_drives['two_point_conv_result']) +
                                                        filtered_pbp_dst_scoring_drives['extra_point_result'])
    #print(filtered_pbp_dst_scoring_drives.to_string())

    #group by season and add up points
    dst_points_per_season = filtered_pbp_dst_scoring_drives\
        .groupby(['season'])\
        .agg({'points_scored': ['sum']}).reset_index()
    dst_points_per_season.columns = ['season', 'total_defense_points']
    return dst_points_per_season



if __name__ == '__main__':
    sns.set_theme(style="whitegrid", palette="colorblind")
    seasons = range(1999, 2023 + 1)
    pbp = nfl.import_pbp_data(seasons)

    pbp_drives = pbp.groupby(['game_id', 'drive'])[['drive_end_transition']].first().reset_index()
    pbp_drive_totals = pbp.groupby(['game_id', 'season'])\
        .agg({'drive': ['nunique'], 'total': ['first']})\
        .reset_index()
    pbp_drive_totals.columns = ['game_id', 'season', 'num_unique_drives', 'total_points']

    pbp_drive_totals_per_season = pbp_drive_totals.groupby('season')\
        .agg({'num_unique_drives': ['sum'], 'total_points': ['sum']})\
        .reset_index()
    pbp_drive_totals_per_season.columns = ['season', 'total_drives', 'total_points']

    def_pts_totals = getTotalDSTPoints(pbp)

    points_and_drives_totals = pd.merge(pbp_drive_totals_per_season, def_pts_totals, on=['season'], how='inner')
    points_and_drives_totals['total_offense_points'] = points_and_drives_totals['total_points'] - \
                                                       points_and_drives_totals['total_defense_points']
    points_and_drives_totals['off_pts_per_drive'] = \
        points_and_drives_totals['total_offense_points'] / points_and_drives_totals['total_drives']

    print(points_and_drives_totals.to_string())

