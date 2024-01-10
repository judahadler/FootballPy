import nfl_data_py as nfl
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.formula.api as smf

if __name__ == '__main__':
    # Prepare Rushing Data
    sns.set_theme(style="whitegrid", palette="colorblind")
    seasons = range(2018, 2023 + 1)
    pbp = nfl.import_pbp_data(seasons)

    pbp_tds_tos_pass = pbp.groupby(['passer', 'passer_id', 'season']).agg({'pass_touchdown': ["sum","count"],
                                                                  'interception': ["sum"],
                                                                  'rush_touchdown': ["sum"],
                                                                  'fumble_lost': ["sum"]})
    pbp_tds_tos_pass.columns = [f"{col[0]}_{col[1]}" if col[1] != '' else col[0] for col in pbp_tds_tos_pass.columns]
    pbp_tds_tos_pass.reset_index(inplace=True)

    pbp_tds_tos_rush = pbp.groupby(['rusher', 'rusher_id', 'season']).agg(
        {'rush_touchdown': ["sum"],
         'fumble_lost': ["sum"]})
    pbp_tds_tos_rush.columns = [f"{col[0]}_{col[1]}" if col[1] != '' else col[0] for col in pbp_tds_tos_rush.columns]
    pbp_tds_tos_rush.reset_index(inplace=True)

    pbp_tds_tos_pass['player_id'] = pbp_tds_tos_pass['passer_id']
    pbp_tds_tos_rush['player_id'] = pbp_tds_tos_rush['rusher_id']
    pbp_tds_tos = pbp_tds_tos_pass.merge(pbp_tds_tos_rush, how='inner', on=['player_id', 'season'])

    pbp_tds_tos.reset_index(inplace=True)

    #print(pbp_tds_tos.head(10))
    pbp_tds_tos = pbp_tds_tos.rename(columns={'pass_touchdown_count': 'attempts'})
    pbp_tds_tos['total_tds'] = pbp_tds_tos['rush_touchdown_sum_x'] + pbp_tds_tos['rush_touchdown_sum_y'] + pbp_tds_tos['pass_touchdown_sum']
    pbp_tds_tos['total_tos'] = pbp_tds_tos['interception_sum'] + pbp_tds_tos['fumble_lost_sum_x'] + pbp_tds_tos['fumble_lost_sum_y']
    pbp_tds_tos['td_vs_to_ratio'] = pbp_tds_tos['total_tds'] / pbp_tds_tos['total_tos']
    #print(pbp_tds_tos.head(10))
    #pbp_tds_tos = pbp_tds_tos.query("attempts > 500")
    pbp_tds_tos = pbp_tds_tos.query("passer == 'J.Allen'")
    pbp_tds_tos_sorted = pbp_tds_tos[['passer', 'season', 'td_vs_to_ratio', 'total_tds', 'total_tos']].sort_values(by='td_vs_to_ratio', ascending=False)
    pbp_tds_tos_sorted = pbp_tds_tos_sorted
    print(pbp_tds_tos_sorted.head(25))
