import nfl_data_py as nfl
import seaborn as sns
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

def getTeamsThreeOutRateSeason(pbp, season):
    pbp = pbp[pbp['season'] == season]
    pbp_filtered = pbp[['season', 'game_id', 'drive', 'defteam', 'series_result', 'drive_first_downs',
                                   'play_id', 'drive_play_id_ended']]

    # Further filter to keep last play in each drive
    pbp_filtered = pbp_filtered[pbp_filtered['play_id'] == pbp_filtered['drive_play_id_ended']]

    pbp_filtered["three_and_out"] = ((pbp_filtered["series_result"] == "Punt") &
                                     (pbp_filtered["drive_first_downs"] == 0)).astype(int)

    three_out_rates = pbp_filtered.groupby(['season', 'defteam']).agg({
        'three_and_out': 'sum',
        'defteam': 'size'
    }).rename(columns={'three_and_out': 'total_three_outs', 'defteam': 'total_def_drives'}).reset_index()

    three_out_rates['three_out_rate'] = three_out_rates['total_three_outs'] / three_out_rates['total_def_drives']

    three_out_rates = three_out_rates.sort_values(by='three_out_rate', ascending=False)

    return three_out_rates

#process a single season
def process_season(season):
    pbp = nfl.import_pbp_data([season])
    result = getTeamsThreeOutRateSeason(pbp, season)
    return result

def process_multiple_seasons(seasons):
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_season, seasons))

    combined_result = pd.concat(results, ignore_index=True)
    return combined_result


if __name__ == '__main__':
    years = list(range(2023, 2023 + 1))
    combined_result_df = process_multiple_seasons(years)
    print(combined_result_df.to_string())
