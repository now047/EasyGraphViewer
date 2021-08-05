from bokeh.io import output_notebook
import streamlit as st


import custom
import summary


if __name__ == '__main__':
    output_notebook()

    apps = {
        'Summary graph': summary.app,
        'Custom graph': custom.app,
    }
    st.set_page_config('GraphCSV', layout='wide')
    st.sidebar.header("Applications")
    selected_app_name = st.sidebar.selectbox(
        label='Select App',
        options=list(apps.keys()), index=1)

    render_func = apps[selected_app_name]
    render_func()
