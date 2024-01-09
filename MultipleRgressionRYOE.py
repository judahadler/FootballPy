import nfl_data_py as nfl
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

def prepareRushingData(pbp):

    query_str = 'play_type == "run" & rusher_id.notnull() & down.notnull() & run_location.notnull()'
    pbp_run = pbp.query(query_str).reset_index()

    pbp_run.loc[pbp_run.rushing_yards.isnull(), "rushing_yards"] = 0

    return pbp_run

def generateHistorgrams(pbp_run):
    pbp_run.down = pbp_run.down.astype(str)
    g = sns.FacetGrid(data=pbp_run, col="down", col_wrap=2)
    g.map_dataframe(sns.histplot, x="rushing_yards")
    plt.show()

def generateBoxplot(pbp_run):
    sns.boxplot(data=pbp_run.query("ydstogo == 10"), x="down", y="rushing_yards")
    plt.show()

def generateScatterPlot(pbp_run):
    sns.regplot(
        data=pbp_run,
        x="yardline_100",
        y="rushing_yards",
        scatter_kws={"alpha":0.25},
        line_kws={"color": "red"})

    plt.show()

def generateScatterPlotBinAve(pbp_run):
    pbp_run_y100 = pbp_run\
        .groupby(["yardline_100"])\
        .agg({"rushing_yards": ["mean"]})
    pbp_run_y100.columns = list(map("_".join, pbp_run_y100.columns))
    pbp_run_y100.reset_index(inplace=True)

    sns.regplot(
        data=pbp_run_y100,
        x="yardline_100",
        y="rushing_yards_mean",
        scatter_kws={"alpha": 0.25},
        line_kws={"color": "red"})

    plt.show()


def generateBoxPlotDirection(pbp_run):
    sns.boxplot(data=pbp_run, x="run_location", y="rushing_yards")
    plt.show()

def generateScatterPlotScoreDiff(pbp_run):
    pbp_run_sd = pbp_run\
        .groupby(["score_differential"])\
        .agg({"rushing_yards": ["mean"]})
    pbp_run_sd.columns = list(map("_".join, pbp_run_sd.columns))
    pbp_run_sd.reset_index(inplace=True)

    sns.regplot(
        data=pbp_run_sd,
        x="score_differential",
        y="rushing_yards_mean",
        scatter_kws={"alpha": 0.25},
        line_kws={"color": "red"})

    plt.show()

def ryoeModel(pbp_run):
    pbp_run.down = pbp_run.down.astype(str)
    expected_yards = smf.ols(
        data=pbp_run,
        formula="rushing_yards ~ 1 + down + ydstogo + " +
                "down:ydstogo + yardline_100 + run_location + score_differential").fit()

    pbp_run["ryoe"] = expected_yards.resid

    # print(expected_yards.summary())

    ryoe = pbp_run \
        .groupby(["season", "rusher", "rusher_id"]) \
        .agg({
        "ryoe": ["count", "mean", "sum"],
        "rushing_yards": ["mean"]
    })

    ryoe.columns = list(map("_".join, ryoe.columns))
    ryoe.reset_index(inplace=True)

    ryoe = ryoe.rename(columns={
        "ryoe_count": "n",
        "ryoe_sum": "ryoe_total",
        "ryoe_mean": "ryoe_per",
        "rushing_yards_mean": "yards_per_carry"})\
        .query("n > 50")
    print(ryoe[ryoe['rusher'].str.contains('Hall')])
    print(ryoe.sort_values("yards_per_carry", ascending=False, ignore_index=True).head(30))
    #print(ryoe.sort_values("ryoe_total", ascending=False, ignore_index=True).head(20))
    #print(ryoe.sort_values("ryoe_per", ascending=False, ignore_index=True).head(20))

    return ryoe

def ryoeStabilityAnalysis(ryoe):
    cols_keep = ["season", "rusher", "rusher_id", "ryoe_per", "yards_per_carry"]

    ryoe_now = ryoe[cols_keep].copy()

    ryoe_last = ryoe[cols_keep].copy()
    ryoe_last.rename(columns={'ryoe_per': 'ryoe_per_last',
                              'yards_per_carry': 'yards_per_carry_last'},
                     inplace=True)
    ryoe_last["season"] += 1
    ryoe_lag = ryoe_now.merge(ryoe_last,
                              how='inner',
                              on=['rusher_id', 'rusher', 'season'])
    print(ryoe_lag[["yards_per_carry_last", "yards_per_carry"]].corr())

    print(ryoe_lag[["ryoe_per_last", "ryoe_per"]].corr())


if __name__ == '__main__':
    # Prepare Rushing Data
    seasons = range(2023, 2023 + 1)
    pbp = nfl.import_pbp_data(seasons)

    pbp_run = prepareRushingData(pbp)

    sns.set_theme(style="whitegrid", palette="colorblind")

    # # This histogram shows us that seemingly rushing yards decrease with the Down
    # generateHistorgrams(pbp_run)
    # # This boxplot shows us that rushing yards increases (or at least remains constant) with the Down - simpsons paradox
    # generateBoxplot(pbp_run)
    #
    # # # Generate Scatterplot - a bit messy and time consuming
    # # generateScatterPlot(pbp_run)
    #
    # # Bin and average and then generate scatterplot: cleans up the data and shows a clear relationship between distance
    # # to endzone and ypc
    # generateScatterPlotBinAve(pbp_run)
    #
    # # Generate a box plot displaying rushing yard distance for rushes to different directions
    # # Shows slight differences so worth keeping it in the model
    # generateBoxPlotDirection(pbp_run)
    #
    # # Generate scatter plot for score differential - this shows us that as score differential goes up, teams expect the
    # # leading team to run more, which leads to lower rushing averages.  And when teams are down a lot, the leading team
    # # plays 'prevent' defense, leading to higher rushing averages
    # generateScatterPlotScoreDiff(pbp_run)

########################################################################################################################

    # Fit a model using the variables we explored above: ydstogo, down, distance to endzone,  score diff
    ryoe = ryoeModel(pbp_run)

########################################################################################################################

    # Stability analysis on new RYOE stat
    #ryoeStabilityAnalysis(ryoe)

########################################################################################################################

    # Exercises: (NOT DONE YET)


