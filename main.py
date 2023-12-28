import nfl_data_py as nfl
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf


if __name__ == '__main__':
    # Prepare Rushing Data
    seasons = range(2016, 2022 + 1)
    pbp = nfl.import_pbp_data(seasons)


