import nfl_data_py as nfl
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

def prepareRushingData(pbp):

    query_criteria = 'play_type == "run" & rusher_id.notnull()'
    pbp_run = pbp.query(query_criteria).reset_index()
    # Replace any null carries with 0
    pbp_run.loc[pbp_run.rushing_yards.isnull(), "rushing_yards"] = 0
    return pbp_run

def generateRushYardsScatterPlots(pbp_run, condition):

    sns.scatterplot(data=pbp_run, x=condition, y="rushing_yards")
    plt.show()

    # Add a trend line
    sns.regplot(data=pbp_run, x=condition, y="rushing_yards")
    plt.show()

# This function uses binning and averaging to clean up the mess and better display the trends between yards to go and
# rushing yards.
def generateAveragedScatterPlot(pbp_run, condition):
    pbp_run_ave = pbp_run \
        .groupby([condition]) \
        .agg({"rushing_yards": ["mean"]})

    # This line of code flattens the rushing yards mean stat so instead of it being a multileveled column index, it is
    # now - "rushing_yards_mean" and not rushing_yards[mean]
    pbp_run_ave.columns = list(map("_".join, pbp_run_ave.columns))
    pbp_run_ave.reset_index(inplace=True)
    sns.regplot(data=pbp_run_ave, x=condition, y="rushing_yards_mean")
    plt.show()

def generateRYOEData(pbp_run, threshold):
    ryoe = pbp_run\
        .groupby(["season","rusher", "rusher_id"])\
        .agg({
        "ryoe": ["count", "sum", "mean"],
        "rushing_yards": ["mean"]})
    ryoe.columns = list(map("_".join, ryoe.columns))
    ryoe.reset_index(inplace=True)
    ryoe = ryoe.rename(columns={
        "ryoe_count": "n",
        "ryoe_sum": "ryoe_total",
        "ryoe_mean": "ryoe_per",
        "rushing_yards_mean": "yards_per_carry"}).query("n > " + str(threshold))

    #print(ryoe.sort_values("ryoe_total", ascending=False))

    print(ryoe.sort_values("ryoe_per", ascending=False))

    return ryoe

def ryoeStabilityAnalysis(ryoe):
    cols_keep = ["season", "rusher_id", "rusher", "ryoe_per", "yards_per_carry"]
    ryoe_now = ryoe[cols_keep].copy()
    ryoe_last = ryoe[cols_keep].copy()
    ryoe_last.rename(columns={
        'ryoe_per': 'ryoe_per_last',
        'yards_per_carry': 'yards_per_carry_last',
    }, inplace=True)
    ryoe_last["season"] += 1
    ryoe_lag = ryoe_now.merge(ryoe_last, how='inner', on=['rusher_id', 'rusher', 'season'])

    print(ryoe_lag[["yards_per_carry_last", "yards_per_carry"]].corr())
    print(ryoe_lag[["ryoe_per_last", "ryoe_per"]].corr())

def exercise1(pbp_run):
    ryoe = generateRYOEData(pbp_run, 100)
    ryoeStabilityAnalysis(ryoe)

def exercise3(pbp_run):
    generateRushYardsScatterPlots(pbp_run, "yardline_100")
    generateAveragedScatterPlot(pbp_run, "yardline_100")

    yards_to_go = smf.ols(formula='rushing_yards ~ 1 + yardline_100', data=pbp_run)
    print(yards_to_go.fit().summary())
    pbp_run["ryoe"] = yards_to_go.fit().resid

    ryoe = generateRYOEData(pbp_run, 50)
    ryoeStabilityAnalysis(ryoe)


if __name__ == '__main__':

    # Prepare Rushing Data
    seasons = range(2016, 2022 + 1)
    pbp = nfl.import_pbp_data(seasons)
    pbp_run = prepareRushingData(pbp)

    # Generate Scatter Plots for rushing yds vs yards to go
    sns.set_theme(style="whitegrid", palette="colorblind")
    generateRushYardsScatterPlots(pbp_run, "ydstogo")
    generateAveragedScatterPlot(pbp_run, "ydstogo")

    # Simple linear regression for rushing yards as predicted by yards to go
    yards_to_go = smf.ols(formula='rushing_yards ~ 1 + ydstogo', data=pbp_run)

    # Based on the extremely low R-squared value we see the data wasn't predicted well
    # For reference: an R-squared of 1.00 corresponds to the model perfectly fitting the data
    print(yards_to_go.fit().summary())

    # Add a ryoe column to the dataframe by using the residuals of the model
    pbp_run["ryoe"] = yards_to_go.fit().resid

    ####################################################################################################################

    # Generate RYOE data set which includes season-level data for a rusher's RYOE
    ryoe = generateRYOEData(pbp_run, 50)

    ####################################################################################################################

    # Is RYOE a better metric?  Testing predictable powers of RYOE.
    ryoeStabilityAnalysis(ryoe)

    ####################################################################################################################

    # # Exercise 1: change threshold to 100 carries
    # exercise1(pbp_run)

    # # Exercise 3: Change yards to go into yardline_100
    # exercise3(pbp_run)