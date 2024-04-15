import json
import jwt
import requests
import hashlib
import os
from datetime import datetime, UTC
from time import mktime
from dateutil.relativedelta import relativedelta
from firebase_functions import https_fn
from firebase_admin import initialize_app, credentials, firestore

if os.path.isfile("creds.json"):
    cred = credentials.Certificate("creds.json")
    initialize_app(cred)
else:
    initialize_app()


def parse_orders(token):
    limit = 100
    skip = 0
    items = []
    orders = []

    url = "https://restaurant-api.wolt.com/v2/order_details/?limit={limit}&skip={skip}"
    headers = {"Authorization": "Bearer " + token}

    lastYear = (
        mktime(
            (
                datetime.today().date().replace(day=1) - relativedelta(years=1)
            ).timetuple()
        )
        * 1000
    )

    while True:
        response = requests.get(url.format(limit=limit, skip=skip), headers=headers)
        if response.status_code != 200:
            break
        data = response.json()
        if not data:
            break
        for order in data:
            delivery_time = order.get("delivery_time", {}).get("$date", 0)
            if order.get("status") != "delivered":
                continue
            if delivery_time < lastYear:
                break

            order_id = order.get("order_id")
            filtered_order = {
                "order_id": order_id,
                "total_price": float(order.get("total_price_share", 0)) / 100
                if float(order.get("total_price_share", 0)) / 100 > 0
                else float(order.get("total_price", 0)) / 100,
                "currency": order.get("currency"),
                "latitude": round(order.get("venue_coordinates", [32, 34])[1], 10),
                "longitude": round(order.get("venue_coordinates", [32, 34])[0], 10),
                "venue_name": order.get("venue_name"),
                "venue_name_fixed": order.get("venue_name").split("|")[0].strip(),
                "venue_timezone": order.get("venue_timezone"),
                "delivery_time": order.get("delivery_time", {}).get("$date"),
                "year-month": datetime.fromtimestamp(
                    delivery_time / 1000, UTC
                ).strftime("%Y-%m"),
            }

            for item in order.get("items", []):
                filtered_item = {
                    "order_id": order_id,
                    "item_id": item.get("id"),
                    "name": item.get("name"),
                    "price": float(item.get("end_amount", 0)) / 100,
                    "currency": order.get("currency"),
                    "venue_name_fixed": order.get("venue_name").split("|")[0].strip(),
                    "count": item.get("count"),
                }
                items.append(filtered_item)

            orders.append(filtered_order)

        skip += limit

    return orders, items


def push_orders(user_id, orders, items):
    db = firestore.client()
    orders_collection = db.collection("orders")
    orders_collection.document(user_id).set({"orders": orders, "items": items})


@https_fn.on_request()
def datawolt(req: https_fn.Request) -> https_fn.Response:
    headers = {
        "Access-Control-Allow-Origin": "https://wolt.com",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "3600",
    }

    if req.method == "OPTIONS":
        return ("", 204, headers)

    token = req.get_json().get("token")

    if req.method != "POST":
        return https_fn.Response("", status=403)

    decoded_token = jwt.decode(token, options={"verify_signature": False})
    userid = hashlib.sha256(decoded_token.get("user").get("id").encode()).hexdigest()[
        :32
    ]
    orders, items = parse_orders(token)
    push_orders(userid, orders, items)

    return https_fn.Response(
        json.dumps(
            {"userid": userid, "order_count": len(orders), "item_count": len(items)}
        ),
        headers=headers,
    )


def main():
    token = ""

    decoded_token = jwt.decode(token, options={"verify_signature": False})
    userid = hashlib.sha256(decoded_token.get("user").get("id").encode()).hexdigest()[
        :32
    ]
    orders, items = parse_orders(token)
    push_orders(userid, orders, items)
    print(f"userid: {userid}, order_count: {len(orders)}, item_count: {len(items)}")


if __name__ == "__main__":
    main()
