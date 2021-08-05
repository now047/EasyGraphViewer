import os
from datetime import date, datetime, timedelta
import textwrap


from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import Range1d, LinearAxis
import pandas as pd
import streamlit as st


from common import ALL_COLLORS, DATA_DEATH_URL, datetime_format_help_df


@st.cache(allow_output_mutation=True)
def load_csv(csv_file):
    df = pd.read_csv(csv_file)
    return df


def app():

    st.title('Custom graph generator')
    script_text = textwrap.dedent('''
            from datetime import datetime, timedelta

            from bokeh.io import show
            from bokeh.models import Range1d, LinearAxis
            from bokeh.plotting import figure, ColumnDataSource
            import pandas as pd

    ''')

    with st.form("source_csv"):
        csv_file = st.text_input('Source csv file', value=DATA_DEATH_URL)
        st.form_submit_button(label='Apply')

    if not os.path.exists(csv_file):
        st.error(f"File not found: {csv_file}")

    df = load_csv(csv_file).copy()
    script_text += textwrap.dedent(f'''
        csv_file = "{csv_file}"
        df = pd.read_csv(csv_file)
    ''')

    if st.checkbox('Show raw data'):
        st.dataframe(df)

    graph_data = []
    with st.sidebar:
        st.markdown('---')
        st.header("Graph Configuration")
        title_txt = st.text_input('Title:')

        st.markdown('---')
        st.subheader("X Axis")
        x_axis_column = st.selectbox(
            "Column:",
            df.columns,
            key='x_axis_column')
        x_axis_type = st.selectbox(
            'Type:',
            ['auto', 'datetime', 'linear', 'log', 'mercator'],
            index=0,
            key='x_axis_type')

        if x_axis_type == 'datetime':
            custom_datetime_format = None
            is_utc_time = False
            if st.checkbox('Use custom datetime format', key='datetime_format_help'):
                custom_datetime_format = st.text_input(
                    'Use custom date/time format',
                    value='%Y-%M-%dT%H:%m:%S.%f',
                    key='custom_datetime_format',
                    help='Specify data/time format the column filed is described')
                if st.checkbox('Help?', key='datetime_format_help'):
                    st.dataframe(datetime_format_help_df)
            else:
                is_utc_time = st.checkbox('Use UNIX time', key='is_utc_time')

            start_date = st.date_input('Start date:',
                                       min_value=date(2019, 1, 1),
                                       max_value=date(2032, 12, 31),
                                       value=date.today() - timedelta(weeks=2))
            start_time = st.time_input('Start time:')
            start_datetime = datetime.combine(start_date, start_time)
            st.write(start_datetime)

            end_date = st.date_input('End date:',
                                     min_value=date(2019, 1, 1),
                                     max_value=date(2032, 12, 31),
                                     value=date.today())
            end_time = st.time_input('End time:')
            end_datetime = datetime.combine(end_date, end_time)
            st.write(end_datetime)

            timezone_shift = st.number_input('Time shift', min_value=-23.5, max_value=23.5,
                                             value=.0, step=0.5, key='timezone_shift',
                                             help='If you want to convert GMT/local times when displying, specifiy the time diffs.')

        st.markdown('---')
        st.subheader("Y Axis")
        y_range_max = st.number_input(
            'Max value:', min_value=0, value=1000)

        add_second_y_axis = st.checkbox(
            'Add second Y axis', key='second_y_axis_enabled')
        if add_second_y_axis:
            second_y_axis_label = st.text_input(
                'Label:', key='second_y_axis_label')
            second_y_axis_max_value = st.number_input(
                'Max value:', min_value=0, key='second_y_axis_max_value')

        st.markdown('---')
        st.subheader("Select columns to plot")
        for name in df.columns:
            if name == x_axis_column:
                continue
            name_selected = st.checkbox(name, False)
            if name_selected:
                plot_type = st.selectbox(
                    'Type:',
                    ['line', 'circle', 'cross', 'triangle'],
                    key='plot_type_'+name,
                    index=1)
                legend = name

                color = None
                is_legend_filed = st.checkbox(
                    'Cotegorize by coloring?')
                if plot_type != 'line' and is_legend_filed:
                    legend = st.selectbox(
                        'Select a column to categorize', df.columns)
                    color_map = {}
                    color_index = 0
                    for cat in set(df[legend]):
                        col = st.selectbox(
                            label=f'Color for {cat}:',
                            options=ALL_COLLORS,
                            index=color_index,
                            key='color_' + str(cat),
                        )
                        color_map.update({cat: col})
                        color_index += 1
                        color_index = color_index % len(ALL_COLLORS)
                    df['color_' + name] = [color_map[x] for x in df[legend]]
                    script_text += textwrap.dedent(f'''
                            df['{'color_' + name}'] = {[color_map[x] for x in df[legend]]}
                        ''')
                else:
                    color = st.color_picker(
                        label='Color:',
                        key='color_' + name,
                    )

                use_second_y_axis = False
                if add_second_y_axis:
                    use_second_y_axis = st.checkbox(
                        'Use second y axis?', key='use_second_y_axis')

                alpha = st.slider(
                    'Alpha:',
                    0.0, 1.0,
                    value=1.0,
                    key='alpha_'+name,
                )

                graph_data.append({
                    'name': name,
                    'plot_type': plot_type,
                    'legend': legend,
                    'is_legend_field': is_legend_filed,
                    'color': color,
                    'second_y_axis': use_second_y_axis,
                    'alpha': alpha})
                st.markdown('---')

            if x_axis_type == 'datetime':
                if is_utc_time:
                    df[x_axis_column] = pd.to_datetime(
                        df[x_axis_column], unit='s')
                    script_text += textwrap.dedent(f'''
                            df["{x_axis_column}"] = pd.to_datetime(df["{x_axis_column}"], unit='s')''')
                elif custom_datetime_format:
                    df[x_axis_column] = pd.to_datetime(
                        df[x_axis_column], format=custom_datetime_format)
                    script_text += textwrap.dedent(f'''
                            df["{x_axis_column}"] = pd.to_datetime(df["{x_axis_column}"], format='{custom_datetime_format}')''')
                else:
                    script_text += textwrap.dedent(f'''
                            df["{x_axis_column}"] = pd.to_datetime(df["{x_axis_column}"])''')
                    df[x_axis_column] = pd.to_datetime(df[x_axis_column])

                df = df.query(
                    '@start_datetime <= @df[@x_axis_column] <= @end_datetime')

                script_text += textwrap.dedent(f'''
                        start_datetime = datetime.fromisoformat("{start_datetime}")
                        end_datetime = datetime.fromisoformat("{end_datetime}")
                        df = df.query('@start_datetime <= {x_axis_column} <= @end_datetime')
                ''')

                if timezone_shift:
                    df[x_axis_column] = df[x_axis_column] + \
                        timedelta(hours=timezone_shift)
                    script_text += textwrap.dedent(f'''
                            df["{x_axis_column}"] = df["{x_axis_column}"] + timedelta(hours={timezone_shift})''')

    source = ColumnDataSource(df)
    fig = figure(title=title_txt,
                 x_axis_type=x_axis_type,
                 y_range=Range1d(0, y_range_max))

    script_text += textwrap.dedent(f'''
        source = ColumnDataSource(df)
        fig = figure(
            \ttitle="{title_txt}",
            \ty_range=Range1d(0, {y_range_max}),
            \tx_axis_type="{x_axis_type}"
            )
    ''')

    if add_second_y_axis:
        fig.extra_y_ranges = {"second": Range1d(start=0,
                                                end=second_y_axis_max_value)
                              }
        fig.add_layout(LinearAxis(axis_label=second_y_axis_label,
                                  y_range_name="second"),
                       'right')

        script_text += textwrap.dedent(f'''
            fig.extra_y_ranges = {{"second": Range1d(start=0, end={second_y_axis_max_value})}}
            fig.add_layout(LinearAxis(
            \t\t\taxis_label="{second_y_axis_label}",
            \t\t\ty_range_name="second"),
            \t\t'right'
            \t)
            ''')

    def gen_plot_text(type: str, name: str, legend: str, color: str, use_second_axis: bool, alpha: float):
        if name == legend:
            legend = legend + '_'  # handles ambiguos of legend
        y_range_name = 'second' if use_second_axis else 'default'

        return textwrap.dedent(f'''
                fig.{type}(
                    \tx="{x_axis_column}",
                    \ty="{name}",
                    \tsource=source,
                    \tlegend="{legend}",
                    \tcolor="{color}",
                    \talpha={str(alpha)},
                    \ty_range_name="{y_range_name}",
                    )
                ''')

    for g in graph_data:
        if g["plot_type"] == 'line':
            plot_text = gen_plot_text(
                type='line',
                name=g['name'],
                legend=g['legend'],
                color=g['color'],
                use_second_axis=g['second_y_axis'],
                alpha=g['alpha']
            )
            eval(plot_text)
            script_text += plot_text
        elif g["plot_type"] == 'circle':
            plot_text = gen_plot_text(
                type='circle',
                name=g['name'],
                legend=g['legend'],
                color='color_' +
                g['name'] if g['is_legend_field'] else g['color'],
                use_second_axis=g['second_y_axis'],
                alpha=g['alpha']
            )
            eval(plot_text)
            script_text += plot_text
        elif g["plot_type"] == 'cross':
            plot_text = gen_plot_text(
                type='cross',
                name=g['name'],
                legend=g['legend'],
                color='color_' +
                g['name'] if g['is_legend_field'] else g['color'],
                use_second_axis=g['second_y_axis'],
                alpha=g['alpha']
            )
            eval(plot_text)
            script_text += plot_text
        elif g["plot_type"] == 'triangle':
            plot_text = gen_plot_text(
                type='triangle',
                name=g['name'],
                legend=g['legend'],
                color='color_' +
                g['name'] if g['is_legend_field'] else g['color'],
                use_second_axis=g['second_y_axis'],
                alpha=g['alpha']
            )
            eval(plot_text)
            script_text += plot_text

        st.bokeh_chart(fig, use_container_width=False)

        script_text += textwrap.dedent('''
        show(fig)''')
        st.subheader('Code to generate this graph')
        st.code(script_text)
