import nfl_data_py as nfl
import pandas as pd
import numpy as np
import statsmodels.api as sm
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from scipy.stats import poisson

if __name__ == '__main__':
    # Get Passing data
    seasons1 = range(2016, 2022 + 1)
    # We use this second seasons for our model later
    seasons2 = range(2017, 2022 + 1)
    pbp = nfl.import_pbp_data(seasons1)
    pbp_pass = pbp.query('passer_id.notnull()').reset_index()

    # Clean the data
    pbp_pass.loc[pbp_pass.pass_touchdown.isnull(), "pass_touchdown"] = 0
    pbp_pass.loc[pbp_pass.passer.isnull(), "passer"] = None
    pbp_pass.loc[pbp_pass.passer.isnull(), "passer_id"] = None

    #Calculate total passing plays for each amount of total tds
    pbp_pass_td = pbp_pass\
        .groupby(['season', 'week', 'passer_id', 'passer'])\
        .agg({'pass_touchdown': ['sum'],
              'total_line': ['count', 'mean']})
    pbp_pass_td.columns = list(map("_".join, pbp_pass_td.columns))
    pbp_pass_td.reset_index(inplace=True)
    pbp_pass_td.rename(columns = {"pass_touchdown_sum": "pass_td_y",
                                  "total_line_mean": "total_line",
                                  "total_line_count": "n_passes"},
                       inplace=True)
    pbp_pass_td = pbp_pass_td.query("n_passes >= 10")
    pbp_pass_td_grouped = pbp_pass_td.groupby("pass_td_y").agg({"n_passes": 'count'})
    print(pbp_pass_td_grouped.to_string())

    #Graph Poisson distribution and pass_td distribution
    pass_td_y_mean = pbp_pass_td.pass_td_y.mean()
    plot_pos = pd.DataFrame(
        {"x": range(0,7),
         "expected": [poisson.pmf(x, pass_td_y_mean) for x in range(0, 7)]
        }
    )
    sns.histplot(pbp_pass_td['pass_td_y'], stat='probability')
    plt.plot(plot_pos.x, plot_pos.expected)
    plt.show()

    ####################################################################################################################

    # Modeling an individual player market
    # Start by getting all rows with more than 10 n_passes
    pbp_pass_td_geq10 = pbp_pass_td.query("n_passes >= 10")

    #Take average td passes for each qb for the prior seasons and the current season until that game
    x = pd.DataFrame()
    for season_idx in seasons2:
        for week_idx in range(1, 22 + 1):
            week_calc = (
                pbp_pass_td_geq10\
                .query("(season == " + str(season_idx - 1) + ") | " +
                       "(season == " + str(season_idx) + "& week < " + str(week_idx) + ")")\
                .groupby(["passer_id", "passer"])\
                .agg({"pass_td_y": ["count", "mean"]})
            )
            week_calc.columns = list(map("_".join, week_calc.columns))
            week_calc.reset_index(inplace=True)
            week_calc.rename(columns = {"pass_td_y_count": "n_games",
                                        "pass_td_y_mean": "pass_td_rate"},
                             inplace=True)
            week_calc["season"] = season_idx
            week_calc["week"] = week_idx
            x = pd.concat([x, week_calc])

    #print(x.query('passer == "P.Mahomes"').tail())

    # Combine dataframes to have all necessary variables in one dataframe and then fit the model
    pbp_pass_td_geq10 = pbp_pass_td_geq10.query("season != 2016")\
        .merge(x,
               on=["season", "week", "passer_id", "passer"],
               how="inner")
    print(pbp_pass_td_geq10)

    pass_fit = smf.glm(
        formula="pass_td_y ~ pass_td_rate + total_line",
        data=pbp_pass_td_geq10,
        family=sm.families.Poisson()).fit()

    pbp_pass_td_geq10["exp_pass_td"] = pass_fit.predict()
    print(pass_fit.summary())

    # Now let's interpret the coefficients (for poisson regressions the coefficients are on the exponential scale so we
    # need to account for that
    print(np.exp(pass_fit.params))

    # Let's look at one example - notice that the exp_tds are less than what he averaged per game until now - likely
    # due to a regression to the mean
    filter_by = 'passer == "P.Mahomes" & season == 2022 & week == 22'
    cols_look = ["season", "week", "passer", "total_line", "n_games", "pass_td_rate", "exp_pass_td"]

    print(pbp_pass_td_geq10.query(filter_by)[cols_look].to_string())

    # We now want to see how different the probability is relative to the odds provided to us by the sports book.  This
    # will help us determine what is the statistically proper move (assuming our model is handled appropriately)
    pbp_pass_td_geq10["p_0_td"] = poisson.pmf(k=0,
                                      mu=pbp_pass_td_geq10['exp_pass_td'])
    pbp_pass_td_geq10["p_1_td"] = poisson.pmf(k=1,
                                              mu=pbp_pass_td_geq10['exp_pass_td'])
    pbp_pass_td_geq10["p_2_td"] = poisson.pmf(k=2,
                                              mu=pbp_pass_td_geq10['exp_pass_td'])
    pbp_pass_td_geq10["p_g2_td"] = 1 - poisson.cdf(k=2,
                                              mu=pbp_pass_td_geq10['exp_pass_td'])

    cols_look2 = ['passer', 'total_line', 'n_games', 'pass_td_rate',
                  'exp_pass_td', 'p_0_td', 'p_1_td', 'p_2_td', 'p_g2_td']
    print(pbp_pass_td_geq10.query(filter_by)[cols_look2].to_string())

    ####################################################################################################################

    # Explaining Poisson Coefficients with better examples:
    x = poisson.rvs(mu=1, size=10)
    print(x)
    print(x.mean())

    # create a df and fit a glm
    df = pd.DataFrame({"x": x})
    glm_out = smf.glm(formula="x ~ 1",
                      data=df,
                      family=sm.families.Poisson()).fit()

    # Look at output on model scale
    print(glm_out.params)

    # Look at output on exponential scale
    print(np.exp(glm_out.params))

    # Now we need an example that will factor in two coefficients (like slope and intercept)
    # We will check the tds per game over the season for the ravens to assess the impact of losing their qb to injury
    # in week 13

    #subset the data
    bal_td = pbp.query('posteam == "BAL" & season == 2022')\
        .groupby(['game_id', 'week'])\
        .agg({"touchdown": ["sum"]})
    #reorganize the columns
    bal_td.columns = list(map("_".join, bal_td.columns))
    bal_td.reset_index(inplace=True)

    #shift the weeks data in the weeks column so intercept 0 = week 1
    bal_td["week"] = bal_td["week"] - 1

    #create a list of weeks for the plot
    weeks_plot = np.linspace(start=0, stop=18, num=10)

    #plot data
    ax = sns.regplot(data=bal_td, x="week", y="touchdown_sum")
    ax.set_xticks(ticks=weeks_plot, labels=weeks_plot)
    plt.xlabel("Week")
    plt.ylabel("Touchdowns per game")
    plt.show()

    #Analyzing Coefficients both on log scale and exp scale
    glm_bal_td = smf.glm(formula="touchdown_sum ~ week",
                         data=bal_td,
                         family=sm.families.Poisson()).fit()
    print(glm_bal_td.params)
    print(np.exp(glm_bal_td.params))









