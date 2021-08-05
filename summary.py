from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import Range1d, LinearAxis
import pandas as pd
import streamlit as st

from common import DATA_DEATH_URL, DATA_TESTED_DAILY_URL, DATA_PCR_POSITIVE_URL


@st.cache(allow_output_mutation=True)
def load_data(stats_dir):
    print("loading data ...")
    tdf = pd.read_csv(DATA_TESTED_DAILY_URL)
    tdf["日付"] = pd.to_datetime(tdf["日付"])
    pdf = pd.read_csv(DATA_PCR_POSITIVE_URL)
    pdf["日付"] = pd.to_datetime(pdf["日付"])
    ddf = pd.read_csv(DATA_DEATH_URL)
    ddf["日付"] = pd.to_datetime(ddf["日付"])
    ddf["per_day"] = ddf["死亡者数"].diff()
    return tdf, pdf, ddf


def shift_dates(df, shift_days):
    ret_df = df
    ret_df["日付"] = pd.to_datetime(df["日付"])
    ret_df["shifted_date"] = df["日付"]
    ret_df.set_index('shifted_date', inplace=True)
    ret_df = ret_df.shift(freq=f'-{shift_days}D')
    ret_df.reset_index(inplace=True)
    return ret_df


def show_raw_data(df_list, key):
    if st.checkbox('Show raw data', key=key):
        for df in df_list:
            st.dataframe(df)


def get_stats_dir(key):
    with st.form(key):
        stats_dir = st.text_input(
            'Enter stats log directory path')
        st.form_submit_button(label='Apply')
    if not stats_dir.startswith('/export'):
        st.error('Stats dir must start with /export')
    return stats_dir


def app():
    st.title('Summary graph view')

    with st.sidebar:
        st.header('Options')
        pcr_shift_days = st.slider('PCR positive delay days', 0, 10, value=5)
        death_shift_days = st.slider('Death delay days', 0, 20, value=14)
        max_percentage = st.slider('Max parcentage', 10, 100)

    comparison_checked = st.checkbox('Compare', value=False,
                                     help='To compare the stats with other stats, specifiy another stats dir')

    containers = st.beta_columns(2 if comparison_checked else 1)

    for i, container in enumerate(containers):
        with container:
            stats_dir = get_stats_dir('stats_dir_' + str(i))

            tested_df, df2, df3 = load_data(stats_dir)

            positive_df = shift_dates(df2, pcr_shift_days)
            death_df = shift_dates(df3, death_shift_days - pcr_shift_days)

            show_raw_data([tested_df, positive_df, death_df],
                          'show_data_' + str(i))

            tested_src = ColumnDataSource(tested_df)
            positive_src = ColumnDataSource(positive_df)

            fig = figure(title="PCR検査実施人数",
                         x_axis_type='datetime',
                         y_range=Range1d(0, 250000))

            fig.extra_y_ranges = {"second": Range1d(
                start=0, end=max_percentage)}
            fig.add_layout(LinearAxis(axis_label="Positive %",
                                      y_range_name="second"),
                           'left')

            fig.line(x="日付",
                     y="PCR 検査実施件数(単日)",
                     source=tested_src,
                     legend_label="PCR tested")
            fig.vbar(x=death_df["shifted_date"],
                     top=100*death_df["per_day"]/positive_df["PCR 検査陽性者数(単日)"],
                     legend_label="Death%",
                     y_range_name="second",
                     color="red",
                     alpha=0.5)
            fig.vbar(x=positive_df["shifted_date"],
                     top=(100*positive_df["PCR 検査陽性者数(単日)"] /
                          tested_df["PCR 検査実施件数(単日)"]),
                     y_range_name="second",
                     legend_label="Positive%",
                     color="orange",
                     alpha=0.5)
            fig.line(x="日付", y="PCR 検査陽性者数(単日)",
                     source=positive_src,
                     color="seagreen",
                     legend_label="PCR positive")
            st.bokeh_chart(fig, use_container_width=False)
