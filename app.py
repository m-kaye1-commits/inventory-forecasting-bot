import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from forecast_engine import forecast_product_demand
from inventory_math import (
    calculate_daily_stats,
    calculate_safety_stock,
    calculate_reorder_point,
    calculate_recommended_order_qty
)

st.set_page_config(page_title="Leonard Inventory Copilot", layout="wide")

# ----------------------------
# PAGE HEADER
# ----------------------------
st.title("Leonard Inventory Copilot")
st.write(
    "A conversational inventory forecasting and replenishment assistant "
    "for identifying stockout risk, reorder timing, and recommended order quantities."
)

# ----------------------------
# FILE INPUT
# ----------------------------
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    st.info("No file uploaded yet. Using sample file if available.")
    try:
        df = pd.read_csv("data/sample_inventory.csv")
    except FileNotFoundError:
        st.error("No sample file found. Please upload a CSV.")
        st.stop()

# ----------------------------
# REQUIRED COLUMNS CHECK
# ----------------------------
required_columns = [
    "date",
    "product",
    "current_inventory",
    "units_sold",
    "lead_time_days",
    "min_order_qty"
]

missing = [col for col in required_columns if col not in df.columns]
if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

# ----------------------------
# DATA CLEANING
# ----------------------------
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])
df = df.sort_values(["product", "date"])

products = df["product"].dropna().unique().tolist()

if not products:
    st.error("No products found in the file.")
    st.stop()

# ----------------------------
# SIDEBAR CONTROLS
# ----------------------------
st.sidebar.header("Planner Controls")

selected_product = st.sidebar.selectbox("Choose a product", products)
forecast_days = st.sidebar.slider("Forecast days", min_value=7, max_value=180, value=30)
service_level = st.sidebar.selectbox("Service level", ["90%", "95%", "99%"], index=1)

service_z_map = {
    "90%": 1.28,
    "95%": 1.65,
    "99%": 2.33
}
service_z = service_z_map[service_level]

# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def get_risk_level(current_inventory, reorder_point):
    if current_inventory < reorder_point:
        return "HIGH"
    elif current_inventory < reorder_point * 1.15:
        return "MEDIUM"
    return "LOW"


def get_days_of_cover(current_inventory, avg_daily_demand):
    if avg_daily_demand <= 0:
        return 9999
    return current_inventory / avg_daily_demand


def get_urgency_score(current_inventory, reorder_point, lead_time_days, days_of_cover):
    gap = max(reorder_point - current_inventory, 0)
    cover_penalty = max(60 - days_of_cover, 0)
    return round(gap + (lead_time_days * 2) + cover_penalty, 0)


def explain_product(
    product_name,
    current_inventory,
    avg_daily_demand,
    lead_time_days,
    reorder_point,
    safety_stock,
    demand_during_lead_time,
    recommended_order_qty,
    risk_level,
    days_of_cover
):
    if recommended_order_qty > 0:
        return (
            f"{product_name} is at risk of stockout. Current inventory is {current_inventory:,.0f} units, "
            f"which covers about {days_of_cover:.1f} days of demand. Projected demand during the supplier "
            f"lead time is about {demand_during_lead_time:,.0f} units. The reorder point is {reorder_point:,.0f} "
            f"units and safety stock is {safety_stock:,.0f} units. Because inventory is below or too close to the "
            f"reorder threshold, the recommended action is to order {recommended_order_qty:,.0f} units now. "
            f"Risk level is {risk_level}."
        )
    return (
        f"{product_name} inventory is currently healthy. Current inventory is {current_inventory:,.0f} units, "
        f"which covers about {days_of_cover:.1f} days of demand. Projected demand during supplier lead time is "
        f"about {demand_during_lead_time:,.0f} units. Because available stock remains above the reorder threshold, "
        f"no immediate purchase is required. Risk level is {risk_level}."
    )


def build_all_product_table(source_df, service_z_value):
    results = []

    for product in source_df["product"].dropna().unique():
        product_df_loop = source_df[source_df["product"] == product].copy().sort_values("date")

        if len(product_df_loop) < 2:
            continue

        latest_row_loop = product_df_loop.iloc[-1]

        current_inventory_loop = float(latest_row_loop["current_inventory"])
        lead_time_loop = int(latest_row_loop["lead_time_days"])
        min_order_loop = int(latest_row_loop["min_order_qty"])

        avg_demand_loop, std_loop = calculate_daily_stats(product_df_loop)

        safety_loop = calculate_safety_stock(
            avg_daily_demand=avg_demand_loop,
            demand_std=std_loop,
            lead_time_days=lead_time_loop,
            service_z=service_z_value
        )

        reorder_loop = calculate_reorder_point(
            avg_daily_demand=avg_demand_loop,
            lead_time_days=lead_time_loop,
            safety_stock=safety_loop
        )

        demand_during_lead_time_loop = avg_demand_loop * lead_time_loop

        recommended_loop = calculate_recommended_order_qty(
            current_inventory=current_inventory_loop,
            reorder_point=reorder_loop,
            forecast_demand_next_30=demand_during_lead_time_loop,
            min_order_qty=min_order_loop
        )

        days_of_cover_loop = get_days_of_cover(current_inventory_loop, avg_demand_loop)
        risk_loop = get_risk_level(current_inventory_loop, reorder_loop)
        urgency_loop = get_urgency_score(
            current_inventory=current_inventory_loop,
            reorder_point=reorder_loop,
            lead_time_days=lead_time_loop,
            days_of_cover=days_of_cover_loop
        )

        results.append({
            "Product": product,
            "Current Inventory": round(current_inventory_loop, 0),
            "Avg Daily Demand": round(avg_demand_loop, 2),
            "Lead Time (Days)": lead_time_loop,
            "Demand During Lead Time": round(demand_during_lead_time_loop, 0),
            "Safety Stock": round(safety_loop, 0),
            "Reorder Point": round(reorder_loop, 0),
            "Days of Cover": round(days_of_cover_loop, 1),
            "Recommended Order Qty": round(recommended_loop, 0),
            "Risk": risk_loop,
            "Urgency": urgency_loop
        })

    if not results:
        return pd.DataFrame()

    results_df_local = pd.DataFrame(results)
    results_df_local["Risk Rank"] = results_df_local["Risk"].map({"HIGH": 3, "MEDIUM": 2, "LOW": 1})
    results_df_local = results_df_local.sort_values(
        by=["Risk Rank", "Urgency", "Recommended Order Qty"],
        ascending=[False, False, False]
    ).drop(columns=["Risk Rank"])

    return results_df_local


def answer_question(
    question,
    selected_product_name,
    selected_metrics,
    all_results_df
):
    q = question.lower().strip()

    product = selected_product_name
    current_inventory_local = selected_metrics["current_inventory"]
    avg_daily_demand_local = selected_metrics["avg_daily_demand"]
    lead_time_days_local = selected_metrics["lead_time_days"]
    reorder_point_local = selected_metrics["reorder_point"]
    safety_stock_local = selected_metrics["safety_stock"]
    recommended_order_qty_local = selected_metrics["recommended_order_qty"]
    risk_level_local = selected_metrics["risk_level"]
    days_of_cover_local = selected_metrics["days_of_cover"]
    demand_during_lead_time_local = selected_metrics["demand_during_lead_time"]

    urgent_df = all_results_df[all_results_df["Risk"] == "HIGH"].copy()
    high_or_medium_df = all_results_df[all_results_df["Risk"].isin(["HIGH", "MEDIUM"])].copy()

    if "what should we order" in q or ("order" in q and "what" in q):
        if urgent_df.empty:
            return (
                "There are currently no HIGH-risk items that require immediate action. "
                "Use the product selector to review individual items or ask for a summary."
            )
        top_items = urgent_df.head(5)
        item_lines = []
        for _, row in top_items.iterrows():
            item_lines.append(
                f"- {row['Product']}: order {int(row['Recommended Order Qty']):,} units "
                f"(inventory {int(row['Current Inventory']):,}, reorder point {int(row['Reorder Point']):,}, risk {row['Risk']})"
            )
        return (
            "These are the top items that should be reviewed for purchase right now:\n\n"
            + "\n".join(item_lines)
        )

    elif "why" in q:
        return explain_product(
            product_name=product,
            current_inventory=current_inventory_local,
            avg_daily_demand=avg_daily_demand_local,
            lead_time_days=lead_time_days_local,
            reorder_point=reorder_point_local,
            safety_stock=safety_stock_local,
            demand_during_lead_time=demand_during_lead_time_local,
            recommended_order_qty=recommended_order_qty_local,
            risk_level=risk_level_local,
            days_of_cover=days_of_cover_local
        )

    elif "risk" in q and "supplier" not in q:
        return (
            f"{product} is currently rated {risk_level_local} risk. "
            f"It has about {current_inventory_local:,.0f} units on hand, "
            f"{days_of_cover_local:.1f} days of cover, and a reorder point of {reorder_point_local:,.0f}."
        )

    elif "summary" in q or "leadership" in q or "executive" in q:
        high_count = (all_results_df["Risk"] == "HIGH").sum()
        medium_count = (all_results_df["Risk"] == "MEDIUM").sum()
        low_count = (all_results_df["Risk"] == "LOW").sum()

        if all_results_df.empty:
            return "No product summary is available because the results table is empty."

        top_urgent = all_results_df.head(3)["Product"].tolist()
        top_urgent_text = ", ".join(top_urgent) if top_urgent else "none"

        return (
            f"Inventory risk is concentrated in a limited number of items. "
            f"There are {high_count} HIGH-risk products, {medium_count} MEDIUM-risk products, "
            f"and {low_count} LOW-risk products in the current file. "
            f"The most urgent items right now are {top_urgent_text}. "
            f"These products should be reviewed first because current inventory is not comfortably covering "
            f"projected demand during supplier lead time."
        )

    elif "all products" in q or "all skus" in q or "everything" in q:
        if all_results_df.empty:
            return "No all-product recommendation table is available."
        preview = all_results_df[["Product", "Recommended Order Qty", "Risk", "Urgency"]].head(10)
        return preview.to_markdown(index=False)

    elif "days of cover" in q or "cover" in q:
        return (
            f"{product} currently has about {days_of_cover_local:.1f} days of cover "
            f"based on average daily demand of {avg_daily_demand_local:.1f} units."
        )

    else:
        return (
            "Try asking one of these:\n\n"
            "- What should we order?\n"
            "- Why is this product risky?\n"
            "- Give me a summary\n"
            "- Show all products\n"
            "- What is the risk?\n"
            "- How many days of cover do we have?"
        )


# ----------------------------
# SINGLE PRODUCT ANALYSIS
# ----------------------------
product_df = df[df["product"] == selected_product].copy().sort_values("date")

if len(product_df) < 2:
    st.warning("This product does not have enough history to analyze.")
    st.stop()

latest_row = product_df.iloc[-1]

current_inventory = float(latest_row["current_inventory"])
lead_time_days = int(latest_row["lead_time_days"])
min_order_qty = int(latest_row["min_order_qty"])

avg_daily_demand, demand_std = calculate_daily_stats(product_df)

if len(product_df) < 14:
    st.warning("This product has less than 14 rows of history. Forecast confidence may be weaker.")

# Use lead time demand as the planning demand for reorder recommendation
demand_during_lead_time = avg_daily_demand * lead_time_days

try:
    model, forecast_df, total_forecast = forecast_product_demand(product_df, forecast_days=forecast_days)

    safety_stock = calculate_safety_stock(
        avg_daily_demand=avg_daily_demand,
        demand_std=demand_std,
        lead_time_days=lead_time_days,
        service_z=service_z
    )

    reorder_point = calculate_reorder_point(
        avg_daily_demand=avg_daily_demand,
        lead_time_days=lead_time_days,
        safety_stock=safety_stock
    )

    recommended_order_qty = calculate_recommended_order_qty(
        current_inventory=current_inventory,
        reorder_point=reorder_point,
        forecast_demand_next_30=demand_during_lead_time,
        min_order_qty=min_order_qty
    )

    risk_level = get_risk_level(current_inventory, reorder_point)
    days_of_cover = get_days_of_cover(current_inventory, avg_daily_demand)
    urgency_score = get_urgency_score(current_inventory, reorder_point, lead_time_days, days_of_cover)

    # ----------------------------
    # TOP KPIs
    # ----------------------------
    st.subheader(f"Selected Product: {selected_product}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Inventory", f"{current_inventory:,.0f}")
    col2.metric("Reorder Point", f"{reorder_point:,.0f}")
    col3.metric("Safety Stock", f"{safety_stock:,.0f}")
    col4.metric("Recommended Order Qty", f"{recommended_order_qty:,.0f}")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Lead Time (Days)", f"{lead_time_days}")
    col6.metric("Avg Daily Demand", f"{avg_daily_demand:.1f}")
    col7.metric("Days of Cover", f"{days_of_cover:.1f}")
    col8.metric("Urgency Score", f"{urgency_score:,.0f}")

    # ----------------------------
    # DECISION BOX
    # ----------------------------
    st.subheader("Decision")

    if recommended_order_qty > 0:
        st.error(
            f"Order {recommended_order_qty:,.0f} units of {selected_product} now. "
            f"Risk level: {risk_level}."
        )
    else:
        st.success(
            f"No immediate order needed for {selected_product}. "
            f"Risk level: {risk_level}."
        )

    # ----------------------------
    # INSIGHT BLOCK
    # ----------------------------
    st.subheader("Leonard Copilot Insight")
    st.write(
        explain_product(
            product_name=selected_product,
            current_inventory=current_inventory,
            avg_daily_demand=avg_daily_demand,
            lead_time_days=lead_time_days,
            reorder_point=reorder_point,
            safety_stock=safety_stock,
            demand_during_lead_time=demand_during_lead_time,
            recommended_order_qty=recommended_order_qty,
            risk_level=risk_level,
            days_of_cover=days_of_cover
        )
    )

    # ----------------------------
    # CHARTS
    # ----------------------------
    st.subheader("Historical Demand")
    fig1, ax1 = plt.subplots()
    ax1.plot(product_df["date"], product_df["units_sold"])
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Units Sold")
    ax1.set_title(f"Historical Demand - {selected_product}")
    st.pyplot(fig1)

    st.subheader("Forecast")
    fig2, ax2 = plt.subplots()
    ax2.plot(forecast_df["ds"], forecast_df["yhat"], label="Forecast")
    ax2.fill_between(
        forecast_df["ds"],
        forecast_df["yhat_lower"],
        forecast_df["yhat_upper"],
        alpha=0.2
    )
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Forecast Units")
    ax2.set_title(f"{forecast_days}-Day Forecast - {selected_product}")
    ax2.legend()
    st.pyplot(fig2)

    st.subheader("Forecast Table")
    st.dataframe(forecast_df, use_container_width=True)

    # ----------------------------
    # ALL PRODUCT TABLE
    # ----------------------------
    st.divider()
    st.header("All Product Recommendations")

    results_df = build_all_product_table(df, service_z)

    if results_df.empty:
        st.warning("No all-product recommendations available.")
    else:
        st.dataframe(results_df, use_container_width=True)

        csv_export = results_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Recommendation Table as CSV",
            data=csv_export,
            file_name="inventory_recommendations.csv",
            mime="text/csv"
        )

    # ----------------------------
    # CONVERSATIONAL COPILOT
    # ----------------------------
    st.divider()
    st.header("Ask Leonard Inventory Copilot")

    st.caption(
        "Example questions: What should we order? | Why is this risky? | Give me a summary | Show all products"
    )

    user_question = st.text_input("Ask a question about inventory:")

    if user_question:
        selected_metrics = {
            "current_inventory": current_inventory,
            "avg_daily_demand": avg_daily_demand,
            "lead_time_days": lead_time_days,
            "reorder_point": reorder_point,
            "safety_stock": safety_stock,
            "recommended_order_qty": recommended_order_qty,
            "risk_level": risk_level,
            "days_of_cover": days_of_cover,
            "demand_during_lead_time": demand_during_lead_time
        }

        bot_answer = answer_question(
            question=user_question,
            selected_product_name=selected_product,
            selected_metrics=selected_metrics,
            all_results_df=results_df
        )

        st.subheader("Copilot Response")
        st.write(bot_answer)

except Exception as e:
    st.error(f"Something went wrong while running the app: {e}")
