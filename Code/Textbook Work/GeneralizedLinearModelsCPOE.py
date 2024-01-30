import nfl_data_py as nfl
import pandas as pd
import numpy as np
import statsmodels.api as sm
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

def getPassingData(pbp):
    query_str = 'play_type == "pass" & passer_id.notnull() & air_yards.notnull()'
    pbp_pass = pbp.query(query_str).reset_index()
    return pbp_pass

def plotCompPctVsTargetDistance(pbp_pass):
    pass_pct = pbp_pass.query('0<air_yards<=20').groupby('air_yards').agg({'complete_pass': ['mean']})

    pass_pct.columns = list(map('_'.join, pass_pct.columns))
    pass_pct.reset_index(inplace=True)
    pass_pct.rename(columns={'complete_pass_mean': 'comp_pct'}, inplace=True)
    sns.regplot(pass_pct, x='air_yards', y='comp_pct', line_kws={'color': 'red'})
    plt.show()


if __name__ == '__main__':

    sns.set_theme(style="whitegrid", palette="colorblind")

    # Prepare Passing Data
    seasons = range(2016, 2022 + 1)
    pbp = nfl.import_pbp_data(seasons)
    pbp_pass = getPassingData(pbp)

    plotCompPctVsTargetDistance(pbp_pass)

    ####################################################################################################################

    # Building a GLM
    complete_ay = smf.glm(formula= 'complete_pass ~ air_yards',
                          data= pbp_pass,
                          family=sm.families.Binomial()).fit()
    print(complete_ay.summary())

    # Seeing why linear regression would be a bad idea for this model:
    # sns.regplot(data=pbp_pass, x='air_yards', y='complete_pass',
    #             logistic=True,
    #             line_kws={'color': 'red'},
    #             scatter_kws={'alpha': 0.05})
    # plt.show()

    # Add residuals (or cpoe) to the pbp_pass data frame
    pbp_pass['exp_completion'] = complete_ay.predict()
    pbp['cpoe'] = pbp_pass['complete_pass'] - pbp_pass['exp_completion']

    # CPOE leaders vs actual completion percentage dating back to 2016
    cpoe_py = pbp_pass\
        .groupby(['season', 'passer_id', 'passer'])\
        .agg({"cpoe": ['count', 'mean'],
              "complete_pass": ['mean']})
    cpoe_py.columns = list(map('_'.join, cpoe_py.columns))
    cpoe_py.reset_index(inplace=True)
    cpoe_py = cpoe_py.rename(columns = {'cpoe_count': 'n',
                                        'cpoe_mean': 'cpoe',
                                        'complete_pass_mean': 'compl'}).query("n > 100")
    print(cpoe_py.sort_values("cpoe", ascending=False))

    #Factor in more variables, remove missing data, fit model again
    pbp_pass['down'] = pbp_pass['down'].astype(str)
    pbp_pass['qb_hit'] = pbp_pass['qb_hit'].astype(str)

    pbp_pass_no_miss = pbp_pass[['passer', 'passer_id', 'season', 'down', 'qb_hit',
                                 'complete_pass', 'ydstogo', 'yardline_100',
                                 'air_yards', 'pass_location']].dropna(axis=0)
    complete_more = smf.glm(formula='complete_pass ~ down * ydstogo + ' +
                            'yardline_100 + air_yards + ' +
                            'pass_location + qb_hit',
                            data=pbp_pass_no_miss,
                            family=sm.families.Binomial()).fit()

    #Extract outputs and calculate cpoe
    pbp_pass_no_miss['exp_completion'] = complete_more.predict()
    pbp_pass_no_miss['cpoe'] = pbp_pass_no_miss['complete_pass'] - pbp_pass_no_miss['exp_completion']

    #Summarize outputs, rename columns and reformat columns
    cpoe_more = pbp_pass_no_miss\
        .groupby(['season', 'passer_id', 'passer'])\
        .agg({'cpoe': ['count', 'mean'],
              'complete_pass': ['mean'],
              'exp_completion': ['mean']})

    cpoe_more.columns = list(map("_".join, cpoe_more.columns))
    cpoe_more.reset_index(inplace=True)
    cpoe_more = cpoe_more.rename(columns = {'cpoe_count': 'n',
                                            'cpoe_mean': 'cpoe',
                                            'complete_pass_mean': 'compl',
                                            'exp_completion_mean': 'exp_completion'}).query("n > 100")
    #Notice the way some of the ordering flips from the original cpoe dataframe -
    # The newer model has slightly different estimates for a completed pass - hence the different cpoe numbers
    print(cpoe_more.sort_values("cpoe", ascending=False))

    ####################################################################################################################

    # Is CPOE more stable than completion percentage?
    # First process the data so that we have a column for last years numbers too
    cols_keep = ['season', 'passer_id', 'passer', 'cpoe', 'compl', 'exp_completion']
    cpoe_now = cpoe_more[cols_keep].copy()
    cpoe_last = cpoe_now[cols_keep].copy()
    cpoe_last.rename(columns = {'cpoe': 'cpoe_last',
                                'compl': 'compl_last',
                                'exp_completion': 'exp_completion_last'},
                     inplace=True)
    cpoe_last['season'] += 1
    # Merge on the season (since we added 1 to each season in cpoe_last, our lag df will have the stats from the
    # previous year as well.
    cpoe_lag = cpoe_now.merge(cpoe_last,
                              how='inner',
                              on=['passer_id', 'passer', 'season'])
    # See correlation for comp percentage across years
    print(cpoe_lag[['compl_last', 'compl']].corr())

    # See correlation for cpoe across years
    print(cpoe_lag[['cpoe_last', 'cpoe']].corr())







