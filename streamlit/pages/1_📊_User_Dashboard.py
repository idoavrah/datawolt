import re
import json
import pytz
import base64
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from firebase_admin import initialize_app, credentials, firestore


@st.cache_resource
def init_firebase():
    service_account = json.loads(
        base64.b64decode(st.secrets["firebase_service_account"])
    )
    cred = credentials.Certificate(service_account)
    initialize_app(cred)


def stop_rendering():
    st.error(
        "No data found. Please make sure you have the DataWolt extension installed and then visit the Wolt order history page."
    )
    st.stop()


def prepare_data():
    try:
        with st.spinner("Loading user data..."):
            db = firestore.client()
            blob = (
                db.collection("orders")
                .document(st.session_state["userid"])
                .get()
                .to_dict()
            )

            if not blob:
                raise Exception("No data found")

            orders = blob.get("orders", [])
            items = blob.get("items", [])
            if not orders:
                raise Exception("No data found")

            orders = pd.json_normalize(orders)
            items = pd.json_normalize(items)

            monthly = (
                orders.groupby(["currency", "year-month"])
                .sum("total_price")
                .sort_values(["total_price"])
            ).reset_index(level=["currency", "year-month"])

            totals = (
                orders[["currency", "total_price"]]
                .groupby(["currency"])
                .sum()
                .sort_values("total_price", ascending=False)
            ).to_dict()["total_price"]

            averages = (
                orders[["currency", "total_price"]]
                .groupby(["currency"])
                .mean()
                .sort_values("total_price", ascending=False)
            ).to_dict()["total_price"]

            everything = (
                items.groupby(["currency", "venue_name_fixed", "name"])
                .sum("price")
                .reset_index()
            )

            locations = orders.groupby("venue_name").agg(
                latitude=("latitude", "mean"),
                longitude=("longitude", "mean"),
                count=("venue_name", lambda x: x.size * 10),
            )

    except Exception as e:
        if e.args[0] == "No data found":
            stop_rendering()

    return orders, monthly, totals, averages, everything, locations


def build_dashboard(orders, monthly, totals, averages, everything, locations):
    st.metric(
        "Order count",
        f"{len(orders)} (one every {365/len(orders):.3} days)",
        label_visibility="visible",
    )
    st.metric(
        "Total expenses",
        " / ".join(f"{tup[1]:,.1f} {tup[0]}" for tup in list(totals.items())),
        label_visibility="visible",
    )
    st.metric(
        "Average order price",
        " / ".join(f"{tup[1]:,.1f} {tup[0]}" for tup in list(averages.items())),
        label_visibility="visible",
    )

    orders_heatmap = pd.DataFrame(np.zeros((5, 7)))

    for index, row in orders.iterrows():
        timezone = pytz.timezone(row["venue_timezone"])
        timestamp = datetime.fromtimestamp(row["delivery_time"] / 1000, timezone)

        weekday = int(timestamp.strftime("%w"))
        hour = int(timestamp.strftime("%H"))

        if hour <= 6:
            timeofday = 4
        elif hour <= 12:
            timeofday = 0
        elif hour <= 16:
            timeofday = 1
        elif hour <= 19:
            timeofday = 2
        elif hour <= 24:
            timeofday = 3
        else:
            timeofday = 4

        orders_heatmap.loc[timeofday, weekday] = (
            orders_heatmap.loc[timeofday, weekday] + 1
        )

    chart = px.bar(
        monthly,
        text_auto=True,
        barmode="group",
        color="currency",
        x="year-month",
        y="total_price",
        labels={"total_price": "Total Expense", "year-month": "Month"},
    )
    chart.update_xaxes(tickangle=30, showticklabels=True)

    st.subheader("Monthly Expenses")
    chart

    labels_x = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    labels_y = [
        "Morning (6-12)",
        "Noon (12-16)",
        "Afternoon (16-19)",
        "Evening (19-22)",
        "Night (22-6)",
    ]

    chart = px.imshow(
        orders_heatmap,
        y=labels_y,
        x=labels_x,
        aspect="auto",
        text_auto=True,
    )
    chart.update_layout(coloraxis_showscale=False)
    chart.update_xaxes(side="top")

    st.subheader("Delivery Time Distribution")
    chart

    chart = px.treemap(
        everything,
        path=["currency", "venue_name_fixed", "name"],
        values=("price"),
        color_continuous_scale="RdBu",
        color="venue_name_fixed",
    )
    chart.update_traces(texttemplate="%{value}<br>%{label}")
    chart.update_layout(margin=dict(t=0, l=0, r=0, b=0))

    st.subheader("Restaurant and Item Treemap")
    chart

    st.subheader("Restaurant Locations")
    st.map(locations, size="count")


st.header("User Dashboard 📊")

if "userid" in st.session_state:
    del st.session_state["userid"]

if "userid" in st.query_params:
    st.session_state["userid"] = st.query_params.get("userid")
else:
    userid = st.text_input("User ID")
    if userid:
        st.session_state["userid"] = userid

if "userid" in st.session_state:
    if not re.fullmatch(r"^[0-9a-z]*$", st.session_state["userid"]):
        st.error(f"invalid userid: {st.session_state['userid']}")

    else:
        init_firebase()
        orders, monthly, totals, averages, everything, locations = prepare_data()
        build_dashboard(orders, monthly, totals, averages, everything, locations)
