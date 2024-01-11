import nfl_data_py as nfl
import seaborn as sns
import matplotlib.pyplot as plt

def organizeTDTOData(pbp):
    # get passing play data for each qb
    pbp_tds_tos_pass = pbp.groupby(['passer', 'passer_id', 'season']).agg({'pass_touchdown': ["sum", "count"],
                                                                           'interception': ["sum"],
                                                                           'rush_touchdown': ["sum"],
                                                                           'fumble_lost': ["sum"]})
    pbp_tds_tos_pass.columns = [f"{col[0]}_{col[1]}" if col[1] != '' else col[0] for col in pbp_tds_tos_pass.columns]
    pbp_tds_tos_pass.reset_index(inplace=True)

    # get rushing play data for each qb
    pbp_tds_tos_rush = pbp.groupby(['rusher_id', 'season']).agg(
        {'rush_touchdown': ["sum"],
         'fumble_lost': ["sum"]})
    pbp_tds_tos_rush.columns = [f"{col[0]}_{col[1]}" if col[1] != '' else col[0] for col in pbp_tds_tos_rush.columns]
    pbp_tds_tos_rush.reset_index(inplace=True)

    #merge rushing and passing for each qb
    pbp_tds_tos_pass['player_id'] = pbp_tds_tos_pass['passer_id']
    pbp_tds_tos_rush['player_id'] = pbp_tds_tos_rush['rusher_id']
    pbp_tds_tos = pbp_tds_tos_pass.merge(pbp_tds_tos_rush, how='inner', on=['player_id', 'season'])
    pbp_tds_tos.reset_index(inplace=True)

    #clean up column names and merge the totals
    pbp_tds_tos = pbp_tds_tos.rename(columns={'pass_touchdown_count': 'attempts'})
    pbp_tds_tos['total_tds'] = pbp_tds_tos['rush_touchdown_sum_x'] + pbp_tds_tos['rush_touchdown_sum_y'] + pbp_tds_tos[
        'pass_touchdown_sum']
    pbp_tds_tos['total_tos'] = pbp_tds_tos['interception_sum'] + pbp_tds_tos['fumble_lost_sum_x'] + pbp_tds_tos[
        'fumble_lost_sum_y']

    #calculate ratio
    pbp_tds_tos['td_vs_to_ratio'] = pbp_tds_tos['total_tds'] / pbp_tds_tos['total_tos']

    return pbp_tds_tos

#Generate the averages in each quartile for each stat
def calculate_quartile_means(data, lower_bound, upper_bound):
    # Use provided bounds to filter the data
    quartile_df = data.query(f"{lower_bound} < td_vs_to_ratio <= {upper_bound}")[['td_vs_to_ratio', 'season', 'total_tds', 'total_tos']]
    quartile_df_means = quartile_df.groupby(['season']).agg({
        'td_vs_to_ratio': ["mean"],
        'total_tds': ["mean"],
        'total_tos': ["mean"]
    }).reset_index()
    #Clean up columns
    quartile_df_means.columns = quartile_df_means.columns.droplevel()
    quartile_df_means.columns = ['season', 'td_vs_to_ratio_mean', 'total_tds_mean', 'total_tos_mean']
    return quartile_df_means

#Plot the data based on the provided labels and columns
def generate_regplots(df_list, y_column, ylabel, title):
    #iterate over quartiles in df_list
    for quartile, df_means in enumerate(df_list, start=1):
        sns.regplot(x=df_means['season'], y=df_means[y_column], label=f'Quartile {quartile}')

    plt.xlabel('Season')
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.show()


if __name__ == '__main__':
    # Prepare pbp Data
    sns.set_theme(style="whitegrid", palette="colorblind")
    seasons = range(2020, 2023 + 1)
    pbp = nfl.import_pbp_data(seasons)

    pbp_tds_tos = organizeTDTOData(pbp)

    # Filter data (other filters commented below)
    pbp_tds_tos = pbp_tds_tos.query("attempts > 500")
    #pbp_tds_tos = pbp_tds_tos.query("total_tos > 30")
    #pbp_tds_tos = pbp_tds_tos.query("passer == 'J.Allen'")

    #Sort Data
    pbp_tds_tos_sorted = pbp_tds_tos[['passer', 'season', 'td_vs_to_ratio', 'total_tds', 'total_tos']].sort_values(by='td_vs_to_ratio', ascending=False)

    # Get cutoffs for each quartile
    quartile1_mark = pbp_tds_tos_sorted['td_vs_to_ratio'].describe().loc['25%']
    quartile2_mark = pbp_tds_tos_sorted['td_vs_to_ratio'].describe().loc['50%']
    quartile3_mark = pbp_tds_tos_sorted['td_vs_to_ratio'].describe().loc['75%']

    #Get df for quartile cutoffs
    q1_df_means = calculate_quartile_means(pbp_tds_tos_sorted, 0, quartile1_mark)
    q2_df_means = calculate_quartile_means(pbp_tds_tos_sorted, quartile1_mark, quartile2_mark)
    q3_df_means = calculate_quartile_means(pbp_tds_tos_sorted, quartile2_mark, quartile3_mark)
    q4_df_means = calculate_quartile_means(pbp_tds_tos_sorted, quartile3_mark, float('inf'))

    qList = [q1_df_means, q2_df_means, q3_df_means, q4_df_means]
    generate_regplots(qList, 'td_vs_to_ratio_mean', 'td_vs_to_ratio_mean', 'Quartile QB TD:TO Ratio Mean per Season for 2000-2023')
    generate_regplots(qList, 'total_tds_mean', 'total_tds_mean', 'Quartile QB TD Mean per Season for 2000-2023')
    generate_regplots(qList, 'total_tos_mean', 'total_tos_mean', 'Quartile QB TO Mean per Season for 2000-2023')

