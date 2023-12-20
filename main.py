import pandas as pd
import numpy as np
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

def generateRushYardsScatterPlots(pbp_run):

    sns.scatterplot(data=pbp_run, x="ydstogo", y="rushing_yards")
    plt.show()

    # Add a trend line
    sns.regplot(data="pbp_run", x="ydstogo", y="rushing_yards")
    plt.show()

# This function uses binning and averaging to clean up the mess and better display the trends between yards to go and
# rushing yards.
def generateAveragedScatterPlot(pbp_run):
    pbp_run_ave = pbp_run \
        .groupby(["ydstogo"]) \
        .agg({"rushing_yards": ["mean"]})

    # This line of code flattens the rushing yards mean stat so instead of it being a multileveled column index, it is
    # now - "rushing_yards_mean" and not rushing_yards[mean]
    pbp_run_ave.columns = list(map("_".join, pbp_run_ave.columns))
    pbp_run_ave.reset_index(inplace=True)
    sns.regplot(data=pbp_run_ave, x="ydstogo", y="rushing_yards_mean")
    plt.show()


if __name__ == '__main__':

    # Prepare Rushing Data
    seasons = range(2016, 2022 + 1)
    pbp = nfl.import_pbp_data(seasons)
    pbp_run = prepareRushingData(pbp)

    # Generate Scatter Plots for rushing yds vs yards to go
    sns.set_theme(style="whitegrid", palette="colorblind")

    #generateRushYardsScatterPlots(pbp_run)
    generateAveragedScatterPlot(pbp_run)

    # Simple linear regression for rushing yards as predicted by yards to go
    yards_to_go = smf.ols(formula='rushing_yards ~ 1 + ydstogo', data=pbp_run)

    # Based on the extremely low R-squared value we see the data wasn't predicted well
    # For reference: an R-squared of 1.00 corresponds to the model perfectly fitting the data
    print(yards_to_go.fit().summary())

    # Add a ryoe column to the dataframe by using the residuals of the model
    pbp_run["ryoe"] = yards_to_go.fit().resid
