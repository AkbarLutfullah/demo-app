import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import plotly_express as px
from dateutil.relativedelta import relativedelta
from plotly.subplots import make_subplots
import warnings
import requests

# read in icon
url = "https://iili.io/iNZBLX.png"
im = Image.open(requests.get(url, stream=True).raw)

# setup page config
st.set_page_config(page_title="Harmonize", page_icon=im, layout="wide")


# add HE logo to sidebar
def add_logo():
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                background-image: url("https://www.harmonyenergy.co.uk/wp-content/themes/harmony/images/logo.svg");
                background-repeat: no-repeat;

                padding-top: 60px;
                background-size: 80% 50%;
                margin-left: 5px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


add_logo()
# hide made with streamlit
hide_streamlit_style = """
            <style>
            MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# streams
stream_to_id = {
    "contracted-energy-volumes-and-data": "6c33447d-4e15-448d-9ed0-4516a35657a4",
    "firm-frequency-response-auction-results": "340ae31e-b010-46fc-af87-e89778d438ef",
    "fast-reserve-tender-reports": "7f9357b2-0591-45d9-8e0d-0bd7d613a5ff",
    "balancing-services-charging-report-bcr": "06806fef-a9b8-40d7-bbb5-105d662eac14",
    "current-balancing-services-use-of-system-bsuos-data": "26b0f410-27d4-448a-9437-45277818b838",
    "weekly-wind-availability": "bb375594-dd0b-462b-9063-51e93c607e41",
    "mbss": "eb3afc32-fe39-4f33-8808-95b4463e20f8",
    "firm-frequency-response-market-information": "fa1c517f-44e5-470f-813c-5f690dc463fe",
    "balancing-services-use-of-system-bsuos-daily-cost": "b19a3594-3647-4d06-a119-7d97d538d496",
    "outturn-voltage-costs": "1b47a532-9f22-49c1-ae2a-d84dcc6d7408",
    "fast-reserve-market-information-reports": "37e68cbc-ac83-4e52-b10c-b4c49553365f",
    "bsuos-monthly-cost": "0d638634-1285-41ac-b965-d0e06964a302",
    "bsuos-monthly-forecast": "a7c7711a-fac4-4bb9-bf23-abea5a2ea616",
    "short-term-operating-reserve-stor": "ef2bbb5f-ee5c-40c3-bd4b-5a36d1d5f5dc",
    "system-frequency-data": "f0933bdd-1b0e-4dd3-aa7f-5498df1ba5b9",
    "short-term-operating-reserve-tender-reports": "88ef0c84-83c5-4c84-9846-6fd44d8a6037",
    "daily-wind-availability": "7aa508eb-36f5-4298-820f-2fa6745ae2e7",
    "historic-demand-data": "11252656-007c-45a4-87db-9d5cc6e8535a",
    "weekly-opmr": "693ca90e-9d48-4a29-92ad-0bf007bba5c2",
    "daily-opmr": "0eede912-8820-4c66-a58a-f7436d36b95f",
    "2-day-ahead-demand-forecast": "cda26f27-4bb6-4632-9fb5-2d029ca605e1",
    "day-ahead-constraint-flows-and-limits": "d7d4ea81-c14d-41a0-8ed2-f281ae9df8d7",
    "disaggregated-bsad": "48fbc6ea-381e-40d6-9633-d1be09a89a0b",
    "aggregated-bsad": "cfb65cd4-e41c-4587-9c78-31004827bee6",
    "balancing-services-adjustment-data-forward-contracts": "7ce8164f-0f0c-4940-b821-ca232e2eefaf",
    "thermal-constraint-costs": "d195f1d8-7d9e-46f1-96a6-4251e75e9bd0",
    "daily-demand-update": "177f6fa4-ae49-4182-81ea-0c6b35f26ca6",
    "balancing-services-use-of-system-bsuos-daily-forecast": "c1be6c7c-c36d-46cb-8038-098075599bb0",
    "obligatory-reactive-power-service-orps-utilisation": "d91e4fd2-1f27-4d0b-8473-b4b19af7f3dc",
    "7-day-ahead-national-forecast": "70d3d674-15a6-4e41-83b4-410440c0b0b9",
    "firm-frequency-response-post-tender-reports": "e692dc29-e94c-4be7-8067-4fc6af8bab22",
    "upcoming-trades": "48f96ddb-1038-4760-8a39-608713ba163f",
    "day-ahead-wind-forecast": "b2f03146-f05d-4824-a663-3a4f36090c71",
    "1-day-ahead-demand-forecast": "aec5601a-7f3e-4c4c-bf56-d8e4184d3c5b",
    "embedded-wind-and-solar-forecasts": "db6c038f-98af-4570-ab60-24d71ebd0ae5",
    "generation-mix-national": "0a168493-5d67-4a26-8344-2fe0a5d4d20b",
    "unit_dstack_response": "ddc4afde-d2bd-424d-891c-56ad49c13d1a",
}


# National Grid Data Portal class
class Wrapper:
    @st.cache
    def NG_request(self, params={}):
        url_root = "https://national-grid-admin.ckan.io/api/3/action/datastore_search"

        params.update({"resource_id": self.resource_id})

        if "sql" in params.keys():
            url_root += "_sql"

        r = requests.get(url_root, params=params)

        return r

    def raise_(self, err_txt, error=ValueError):
        raise error(err_txt)

    def check_request_success(self, r_json):
        if r_json["success"] == False:
            err_msg = r_json["error"]["message"]
            self.raise_(err_msg)

    date_between = (
        lambda self, dt_col, start_date, end_date: f'SELECT * from "{self.resource_id}" WHERE "{dt_col}" BETWEEN \'{start_date}\'::timestamp AND \'{end_date}\'::timestamp ORDER BY "{dt_col}"'
    )
    date_less_than = (
        lambda self, dt_col, date: f'SELECT * from "{self.resource_id}" WHERE "{dt_col}" < \'{date}\'::timestamp ORDER BY "{dt_col}"'
    )
    date_greater_than = (
        lambda self, dt_col, date: f'SELECT * from "{self.resource_id}" WHERE "{dt_col}" > \'{date}\'::timestamp ORDER BY "{dt_col}"'
    )

    def form_dt_rng_sql_query(self, dt_col, start_date=None, end_date=None):
        start_end_date_exist = (start_date != None, end_date != None)

        func_map = {
            (False, False): {"error": "A start and/or end date should be passed"},
            (True, True): self.date_between(dt_col, start_date, end_date),
            (False, True): self.date_less_than(dt_col, end_date),
            (True, False): self.date_greater_than(dt_col, start_date),
        }

        sql = func_map[start_end_date_exist]

        if not isinstance(sql, str):
            self.raise_(sql["error"])

        return sql

    def query_API(
        self,
        params={},
        start_date=None,
        end_date=None,
        dt_col=None,
        sql="",
        return_raw=False,
    ):
        ## Handling SQL queries
        if start_date or end_date:
            if sql != "":
                warnings.warn(
                    "The start and end date query will overwrite the provided SQL"
                )

            if not dt_col:
                warnings.warn(
                    "If a start or end date has been provided the 'dt_col' parameter must be provided"
                )

            sql = self.form_dt_rng_sql_query(
                dt_col, start_date=start_date, end_date=end_date
            )
            params.update({"sql": sql})

        elif sql != "":
            params.update({"sql": sql})

        elif "sql" in params.keys():
            params.pop("sql")

        ## Making the request
        r = self.NG_request(params=params)

        if return_raw == True:
            return r

        ## Checking and parsing the response
        r_json = r.json()
        self.check_request_success(r_json)

        df = pd.DataFrame(r_json["result"]["records"])

        return df

    def assign_stream(self, stream):
        self.stream = stream
        self.resource_id = stream_to_id[self.stream]

    def __init__(self, stream):
        self.assign_stream(stream)
        self.streams = list(stream_to_id.keys())


# instantiate unit dynamic stack response
unit_dstack_wrapper = Wrapper("unit_dstack_response")


def get_dynamic_units_df(wrapper_obj, start_date, end_date=None, dt_col=None):
    df = wrapper_obj.query_API(start_date=start_date, end_date=end_date, dt_col=dt_col)

    return df


def concat_dfs(df1, df2):
    df = pd.concat([df1, df2])

    return df


def filter_df(df):
    df = df.drop(
        columns=[
            "index",
            "Delivery Start",
            "Delivery End",
            "Company",
            "_full_text",
            "Location",
            "Cancelled",
            "_id",
            "Technology Type",
        ],
        axis=1,
    )
    df = df.reset_index(drop=True)

    return df


def cols_to_numeric(df):
    cols = ["Clearing Price", "Cleared Volume", "EFA"]
    df[cols] = df[cols].apply(pd.to_numeric, errors="coerce", axis=1)

    return df


def plot_frs_subplots(df):
    # fig = make_subplots(
    #     rows=2, cols=1
    # )

    fig1 = px.line(
        df,
        x="EFA",
        y="Clearing Price",
        line_group="Service",
        color="Service",
        markers=True,
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig2 = px.bar(
        df,
        x="EFA",
        y="Cleared Volume",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        template="plotly_dark",
        color="Service",
        pattern_shape="Service",
    )

    # code to make sublots with px
    # For as many traces that exist per Express figure, get the traces from each plot and store them in an array.
    # This is essentially breaking down the Express fig into it's traces
    figure1_traces = []
    figure2_traces = []
    for trace in range(len(fig1["data"])):
        figure1_traces.append(fig1["data"][trace])
    for trace in range(len(fig2["data"])):
        figure2_traces.append(fig2["data"][trace])

    # Create a 1x2 subplot
    this_figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=(
            "Market Clearing Price per EFA Block",
            "Volume procured by ESO per EFA Block",
        ),
    )

    # Get the Express fig broken down as traces and add the traces to the proper plot within in the subplot
    for traces in figure1_traces:
        this_figure.add_trace(traces, row=1, col=1)
    for traces in figure2_traces:
        this_figure.add_trace(traces, row=2, col=1)

    # edit axis labels
    this_figure["layout"]["xaxis"]["title"] = "EFA Block"
    this_figure["layout"]["xaxis2"]["title"] = "EFA Block"
    this_figure["layout"]["yaxis"]["title"] = "Price (£/MW/hour)"
    this_figure["layout"]["yaxis2"]["title"] = "Volume (MW)"
    this_figure["layout"]["height"] = 620

    return this_figure


# convert datetime obj to string
date_today = datetime.now().date()
today_date = date_today.strftime("%Y-%m-%d")
uk_date = date_today.strftime("%d-%m-%Y")
day_ahead = date_today + relativedelta(days=1)
day_ahead_UK_date = day_ahead.strftime("%d-%m-%Y")

# instantiate current df
current_df = get_dynamic_units_df(
    wrapper_obj=unit_dstack_wrapper,
    start_date=today_date,
    end_date=today_date,
    dt_col="EFA Date",
)

# instantiate day ahead
day_ahead_df = get_dynamic_units_df(
    wrapper_obj=unit_dstack_wrapper, start_date=today_date, dt_col="EFA Date"
)

# plotly config_dict
config_dict = {"displaylogo": False}

st.title("Frequency Response Services")

st.write("Choose a timeframe below")
tab1, tab2 = st.tabs(["Current Day", "Day Ahead"])

with tab1:
    st.success(f"Date : {uk_date}")
    contego_df = current_df[current_df["Unit Name"] == "CONTB-1"].reset_index()
    holes_df = current_df[current_df["Unit Name"] == "BHOLB-1"].reset_index()
    col1, col2 = st.columns(2, gap="large")
    with col1:
        col1.subheader("Contego")
        contego_df = filter_df(contego_df)
        contego_df = cols_to_numeric(contego_df)
        contego_df = contego_df.sort_values(by=["EFA"])
        st.plotly_chart(
            plot_frs_subplots(contego_df), use_container_width=True, config=config_dict
        )
        contego_rev_series = (
            contego_df["Clearing Price"] * contego_df["Cleared Volume"] * 4
        )
        contego_sum = round(contego_rev_series.sum(), 2)
        sum_display = "{:,}".format(contego_sum)
        st.metric("Potential day earnings", f"{sum_display} (£/MW/Day)")
    with col2:
        col2.subheader("Holes Bay")
        holes_df = filter_df(holes_df)
        holes_df = cols_to_numeric(holes_df)
        holes_df = holes_df.sort_values(by=["EFA"])
        st.plotly_chart(
            plot_frs_subplots(holes_df), use_container_width=True, config=config_dict
        )
        holes_rev_series = holes_df["Clearing Price"] * holes_df["Cleared Volume"] * 4
        holes_sum = round(holes_rev_series.sum(), 2)
        sum_display = "{:,}".format(holes_sum)
        st.metric("Potential day earnings", f"{sum_display} (£/MW/Day)")
with tab2:
    st.success(f"Date : {day_ahead_UK_date}")
    if len(day_ahead_df) == 0:
        st.info("National Grid ESO will publish this data after 4pm UK time.")
    else:
        contego_df = day_ahead_df[day_ahead_df["Unit Name"] == "CONTB-1"].reset_index()
        holes_df = day_ahead_df[day_ahead_df["Unit Name"] == "BHOLB-1"].reset_index()
        col1, col2 = st.columns(2)
        with col1:
            col1.subheader("Contego")
            contego_df = filter_df(contego_df)
            contego_df = cols_to_numeric(contego_df)
            contego_df = contego_df.sort_values(by=["EFA"])
            st.plotly_chart(
                plot_frs_subplots(contego_df),
                use_container_width=True,
                config=config_dict,
            )
            contego_rev_series = (
                contego_df["Clearing Price"] * contego_df["Cleared Volume"] * 4
            )
            contego_sum = round(contego_rev_series.sum(), 2)
            sum_display = "{:,}".format(contego_sum)
            st.metric("Potential day earnings", f"{sum_display} (£/MW/Day)")
        with col2:
            col2.subheader("Holes Bay")
            holes_df = filter_df(holes_df)
            holes_df = cols_to_numeric(holes_df)
            holes_df = holes_df.sort_values(by=["EFA"])
            st.plotly_chart(
                plot_frs_subplots(holes_df),
                use_container_width=True,
                config=config_dict,
            )
            holes_rev_series = (
                holes_df["Clearing Price"] * holes_df["Cleared Volume"] * 4
            )
            holes_sum = round(holes_rev_series.sum(), 2)
            sum_display = "{:,}".format(holes_sum)
            st.metric("Potential day earnings", f"{sum_display} (£/MW/Day)")

