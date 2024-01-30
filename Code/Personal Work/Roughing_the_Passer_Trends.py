import nfl_data_py as nfl
import seaborn as sns
import numpy as np

# This code attempts to show which quarterbacks get more roughing the passer calls
# As it stands - no conclusion can be drawn regarding generosity of calls - if anything it seems to show a relationship
# between time to throw and roughing the passer or qb hits and roughing the passer

# I later realized that there is a column for 'qb_hit' - so I will change the analysis to reflect calls per qb_hit and
# not calls per pass attempt

# TODO: Change the metric to roughing call per passing play or per qb hit - not roughing call per game


if __name__ == '__main__':
    # Prepare Penalty/Passing Data
    sns.set_theme(style="whitegrid", palette="colorblind")
    seasons = range(2000, 2023 + 1)
    pbp = nfl.import_pbp_data(seasons)

    # Clean up the data so we can track all qb hits and roughing calls
    pbp_hits = pbp[(pbp['qb_hit'] == 1) | (pbp['penalty_type'] == "Roughing the Passer")]
    pbp_hits = pbp_hits[['season', 'passer', 'passer_id', 'penalty_type', 'qb_hit']]
    pbp_hits['roughing_call'] = np.where(pbp_hits["penalty_type"] == 'Roughing the Passer', 1, 0)

    # Group and Agg
    pbp_hits_qbs = pbp_hits\
        .groupby(['passer', 'passer_id'])\
        .agg({'qb_hit': ['count'], 'roughing_call': ['sum']}).reset_index()

    # Clean up the results and calculate calls per hit
    pbp_hits_qbs.columns = ['passer', 'passer_id', 'qb_hits', 'roughing_calls']
    pbp_hits_qbs = pbp_hits_qbs.query("qb_hits > 500")
    pbp_hits_qbs['calls_per_hit'] = pbp_hits_qbs['roughing_calls'] / pbp_hits_qbs['qb_hits']

    #Order the data by calls per hit
    pbp_hits_qbs = pbp_hits_qbs.sort_values("calls_per_hit", ascending=False)

    print(pbp_hits_qbs.to_string())