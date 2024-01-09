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



