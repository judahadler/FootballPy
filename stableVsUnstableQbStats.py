import pandas as pd
import numpy as np
import nfl_data_py as nfl
import seaborn as sns
import matplotlib.pyplot as plt

if __name__ == '__main__':

    #seasons = range(2016, 2017 + 1)
    seasons = range(2020, 2023 + 1)
    pbp_py = nfl.import_pbp_data(seasons)
    # This filter will remove any play that is not a pass (or is negated by a penalty).
    # It will also remove any pass plays without an intended WR - spikes, batted balls, throwaways
    filter_crit = 'play_type == "pass" & air_yards.notnull()'

    # Get passing plays
    pbp_py_p = pbp_py.query(filter_crit).reset_index()

    # define pass type (long vs short)
    pbp_py_p["pass_length_air_yards"] = np.where(
        pbp_py_p["air_yards"] >= 20, "long", "short"
    )

    # Make incomplete passes set to 0 and not NA (For this exercise)
    pbp_py_p["passing_yards"] = np.where(
        pbp_py_p["passing_yards"].isnull(), 0, pbp_py_p["passing_yards"]
    )

    short_passes = pbp_py_p.query('pass_length_air_yards == "short"')
    long_passes = pbp_py_p.query('pass_length_air_yards == "long"')

    # Set seaborn theme
    sns.set_theme(style="whitegrid", palette="colorblind")

    ####################################################################################################################

    # Using describe function to see important data information
    print("All Passing Stats Described: \n" +
          pbp_py_p["passing_yards"].describe().to_string() + "\n")

    # Notice the difference between the lower percentiles in both
    print("All Short Passing Stats Described: \n" +
          short_passes["passing_yards"].describe().to_string() + "\n")
    print("All Long Passing Stats Described: \n" +
          long_passes["passing_yards"].describe().to_string() + "\n")

    # Notice the difference in variability
    print("All Short Passing Stats EPA Described: \n" +
          short_passes["epa"].describe().to_string() + "\n")
    print("All Long Passing Stats EPA Described: \n" +
          long_passes["epa"].describe().to_string() + "\n")

    # Show Passing Yards depth per play histogram
    sns.displot(data=pbp_py, x="passing_yards")
    plt.show()

    ####################################################################################################################

    # Histogram for yards gained on short passing play
    pbp_py_hist_short = sns.displot(data=short_passes,
                                    binwidth=1,
                                    x="passing_yards").set(title='Short Passes Yardage Histogram')
    pbp_py_hist_short.set_axis_labels("Yards gained (or lost) during a short passing play", "Count")
    plt.show()

    # Histogram for yards gained on long passing play
    pbp_py_hist_long = sns.displot(data=long_passes,
                                    binwidth=1,
                                    x="passing_yards").set(title='long Passes Yardage Histogram')
    pbp_py_hist_long.set_axis_labels("Yards gained (or lost) during a long passing play", "Count")
    plt.show()

    ####################################################################################################################

    # Boxplots
    pass_boxplot = sns.boxplot(data=pbp_py_p, x="pass_length_air_yards", y="passing_yards")
    pass_boxplot.set(
        xlabel="Pass Length (long >= 20 yards, short < 20 yards)",
        ylabel="Yards Gained (or lost) during a passing play",
        title='Boxplot for long and short passes'
    )
    plt.show()

    ####################################################################################################################

    # Player level stability of seasonal YPA
    # Group by passer, rename columns
    pbp_py_p_s = pbp_py_p\
        .groupby(["passer_id", "passer", "season"])\
        .agg({"passing_yards": ["mean", "count"]})
    pbp_py_p_s.columns = list(map("_".join, pbp_py_p_s.columns.values))
    pbp_py_p_s.rename(columns={'passing_yards_mean': 'ypa',
                               'passing_yards_count': 'n'},
                      inplace=True)
    # Display any passers with over 100 pass attempts in a season and order from high to low in YPA
    print(pbp_py_p_s\
        .query('n >= 100')\
        .sort_values(by=["ypa"], ascending=False).head().to_string())

    ####################################################################################################################

    # Using the data to draw a conclusion
    # pbp_py_p_s_pl = (p)lay (b)y (p)lay (py)thon (p)assing (s)easons data (p)ass (l)ength
    pbp_py_p_s_pl = pbp_py_p \
        .groupby(["passer_id", "passer", "season", "pass_length_air_yards"]) \
        .agg({"passing_yards": ["mean", "count"]})

    pbp_py_p_s_pl.columns = list(map("_".join, pbp_py_p_s_pl.columns.values))
    pbp_py_p_s_pl.rename(columns={'passing_yards_mean': 'ypa',
                               'passing_yards_count': 'n'},
                      inplace=True)

    pbp_py_p_s_pl.reset_index(inplace=True)

    query_value = (
        '(n >= 100 & ' +
        'pass_length_air_yards == "short") | ' +
        '(n >= 30 & ' +
        'pass_length_air_yards == "long")'
    )
    pbp_py_p_s_pl = pbp_py_p_s_pl.query(query_value).reset_index()

    print(pbp_py_p_s_pl.head().to_string())

    # Copy only the columns we need for our analysis
    cols_save = ["passer_id", "passer", "season", "pass_length_air_yards", "ypa"]
    air_yards_py = pbp_py_p_s_pl[cols_save].copy()

    # Copy the data and add one to the year to be able to compare adjacent years
    # This maneuver of adding 1 to 'season' makes it so that when we merge the two DF's and join on the 'season' column
    # it will now have two columns for each year - the previous year and the current year
    air_yards_lag_py = air_yards_py.copy()
    air_yards_lag_py["season"] += 1
    air_yards_lag_py.rename(columns={'ypa':'ypa_last'},inplace=True)

    # Merge the two dataframes together and only save shared years for passer,season and pass type
    # Now that we have added one to the season column, when joining on 'season' we essentially join the current year
    # and the previous year
    pbp_py_p_s_pl = air_yards_py\
        .merge(air_yards_lag_py,
               how='inner',
               on=['passer_id', 'passer', 'season', 'pass_length_air_yards'])

    # See some examples
    print(
        pbp_py_p_s_pl[["pass_length_air_yards", "passer",
                       "season", "ypa", "ypa_last"]]
        .query('passer == "T.Brady" | passer == "A.Rodgers"')
        .sort_values(["passer", "pass_length_air_yards", "season"])
        .to_string()
        )

    # # Just two additional lines to take a quick look into the dataframe before continuing
    # pbp_py_p_s_pl.info()
    # print(len(pbp_py_p_s_pl.passer_id.unique()))

    # #Generate scatter plot to visualize any correlation between adjacent seasons YPA
    # sns.lmplot(data=pbp_py_p_s_pl,
    #            x="ypa",
    #            y="ypa_last",
    #            col="pass_length_air_yards")
    # plt.show()

    # Assess correlation numerically with pandas
    print(
        pbp_py_p_s_pl.query("ypa.notnull() & ypa_last.notnull()")\
        .groupby("pass_length_air_yards")[["ypa", "ypa_last"]]\
        .corr()
    )

    # See Leaders for 2023:
    print(
        pbp_py_p_s_pl
        .query('pass_length_air_yards == "long" & season == 2023')[["passer_id", "passer", "ypa"]]
        .sort_values(["ypa"], ascending=False)
        .head(10)
        .to_string()
    )

    # See Worst Qualified for 2023:
    print(
        pbp_py_p_s_pl
        .query('pass_length_air_yards == "long" & season == 2023')[["passer_id", "passer", "ypa"]]
        .sort_values(["ypa"], ascending=True)
        .head(10)
        .to_string()
    )

    ####################################################################################################################

    # #Exercise 1: Create a histogram for EPA per pass attempt
    # pbp_py_hist_epa = sns.displot(data=pbp_py_p,
    #                                 binwidth=1,
    #                                 x="epa").set(title='EPA per pass attempt')
    # pbp_py_hist_epa.set_axis_labels("EPA for a passing play", "Count")
    # plt.show()
    #
    # #Exercise 2: Create a boxplot for EPA per pass type
    # epa_boxplot = sns.boxplot(data=pbp_py_p, x="pass_length_air_yards", y="epa")
    # epa_boxplot.set(
    #     xlabel="Pass Length (long >= 20 yards, short < 20 yards)",
    #     ylabel="EPA during a passing play",
    #     title='Boxplot for long and short passes'
    # )
    # plt.show()

    #Exercise 3: Player level stability of seasonal EPA
    # # Group by passer, rename columns
    # pbp_py_p_s = pbp_py_p\
    #     .groupby(["passer_id", "passer", "season"])\
    #     .agg({"epa": ["mean", "count"]})
    # pbp_py_p_s.columns = list(map("_".join, pbp_py_p_s.columns.values))
    # pbp_py_p_s.rename(columns={'epa_mean': 'epa',
    #                            'epa_count': 'n'},
    #                   inplace=True)
    # # Display any passers with over 100 pass attempts in a season and order from high to low in YPA
    # print(pbp_py_p_s\
    #     .query('n >= 100')\
    #     .sort_values(by=["epa"], ascending=False).head(10).to_string())
    #
    # # pbp_py_p_s_pl = (p)lay (b)y (p)lay (py)thon (p)assing (s)easons data (p)ass (l)ength
    # pbp_py_p_s_pl = pbp_py_p \
    #     .groupby(["passer_id", "passer", "season", "pass_length_air_yards"]) \
    #     .agg({"epa": ["mean", "count"]})
    #
    # pbp_py_p_s_pl.columns = list(map("_".join, pbp_py_p_s_pl.columns.values))
    # pbp_py_p_s_pl.rename(columns={'epa_mean': 'epa',
    #                            'epa_count': 'n'},
    #                   inplace=True)
    #
    # pbp_py_p_s_pl.reset_index(inplace=True)
    #
    # query_value = (
    #     '(n >= 100 & ' +
    #     'pass_length_air_yards == "short") | ' +
    #     '(n >= 30 & ' +
    #     'pass_length_air_yards == "long")'
    # )
    # pbp_py_p_s_pl = pbp_py_p_s_pl.query(query_value).reset_index()
    #
    # print(pbp_py_p_s_pl.head().to_string())
    #
    # # Copy only the columns we need for our analysis
    # cols_save = ["passer_id", "passer", "season", "pass_length_air_yards", "epa"]
    # air_yards_py = pbp_py_p_s_pl[cols_save].copy()
    #
    # # Copy the data and add one to the year to be able to compare adjacent years
    # # This maneuver of adding 1 to 'season' makes it so that when we merge the two DF's and join on the 'season' column
    # # it will now have two columns for each year - the previous year and the current year
    # air_yards_lag_py = air_yards_py.copy()
    # air_yards_lag_py["season"] += 1
    # air_yards_lag_py.rename(columns={'epa':'epa_last'},inplace=True)
    #
    # # Merge the two dataframes together and only save shared years for passer,season and pass type
    # # Now that we have added one to the season column, when joining on 'season' we essentially join the current year
    # # and the previous year
    # pbp_py_p_s_pl = air_yards_py\
    #     .merge(air_yards_lag_py,
    #            how='inner',
    #            on=['passer_id', 'passer', 'season', 'pass_length_air_yards'])
    #
    # # See some examples
    # print(
    #     pbp_py_p_s_pl[["pass_length_air_yards", "passer",
    #                    "season", "epa", "epa_last"]]
    #     .query('passer == "T.Brady" | passer == "A.Rodgers" | passer == "J.Allen"')
    #     .sort_values(["passer", "pass_length_air_yards", "season"])
    #     .to_string()
    #     )
    #
    # # Just two additional lines to take a quick look into the dataframe before continuing
    # pbp_py_p_s_pl.info()
    # print(len(pbp_py_p_s_pl.passer_id.unique()))
    #
    # #Generate scatter plot to visualize any correlation between adjacent seasons YPA
    # sns.lmplot(data=pbp_py_p_s_pl,
    #            x="epa",
    #            y="epa_last",
    #            col="pass_length_air_yards")
    # plt.show()
    #
    # # Assess correlation numerically with pandas
    # print(
    #     pbp_py_p_s_pl.query("epa.notnull() & epa_last.notnull()")\
    #     .groupby("pass_length_air_yards")[["epa", "epa_last"]]\
    #     .corr()
    # )
    #
    # # See Leaders for 2023:
    # print(
    #     pbp_py_p_s_pl
    #     .query('pass_length_air_yards == "long" & season == 2023')[["passer_id", "passer", "epa"]]
    #     .sort_values(["epa"], ascending=False)
    #     .head(10)
    #     .to_string()
    # )
    #
    # # See Worst Qualified for 2023:
    # print(
    #     pbp_py_p_s_pl
    #     .query('pass_length_air_yards == "long" & season == 2023')[["passer_id", "passer", "epa"]]
    #     .sort_values(["epa"], ascending=True)
    #     .head(10)
    #     .to_string()
    # )