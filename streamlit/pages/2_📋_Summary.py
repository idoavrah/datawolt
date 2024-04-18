import json
import base64
import streamlit as st
import plotly.express as px
from firebase_admin import initialize_app, credentials, firestore


@st.cache_resource
def init_firebase():
    service_account = json.loads(
        base64.b64decode(st.secrets["firebase_service_account"])
    )
    cred = credentials.Certificate(service_account)
    initialize_app(cred)


st.header("Summary Dashboard 📋")

init_firebase()
with st.spinner("Loading summary data..."):
    db = firestore.client()
    orders_ref = db.collection("orders")

    order_totals = []
    dish_totals = {}
    restaurant_totals = []

    for user in orders_ref.stream():
        total_price = 0
        for order in user.get("orders"):
            total_price += order.get("total_price")
        for item in user.get("items"):
            dish_totals[
                (item.get("venue_name_fixed"), item.get("name"))
            ] = dish_totals.get(
                (item.get("venue_name_fixed"), item.get("name")), 0
            ) + item.get(
                "count"
            )

        if len(user.get("orders")) > 0:
            order_totals.append(
                {
                    "Yearly Expense": round(total_price),
                    "Num Orders": round(len(user.get("orders"))),
                    "Average Order Price": round(total_price / len(user.get("orders"))),
                }
            )

    st.subheader("Expenses Scatter Chart")

    st.scatter_chart(
        order_totals,
        x="Yearly Expense",
        y="Num Orders",
        size="Average Order Price",
        color="Average Order Price",
    )

    dish_totals = [
        {"venue_name_fixed": key[0], "name": key[1], "count": value}
        for key, value in dish_totals.items()
        if value > 10
    ]

    st.subheader("Top restaurants and items")

    chart = px.treemap(
        dish_totals,
        path=["venue_name_fixed", "name"],
        values=("count"),
        color_continuous_scale="RdBu",
        color="venue_name_fixed",
    )

    chart.update_traces(texttemplate="%{value}<br>%{label}")
    chart.update_layout(margin=dict(t=0, l=0, r=0, b=0))

    chart
