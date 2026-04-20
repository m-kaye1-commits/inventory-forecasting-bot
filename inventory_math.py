import math


def calculate_daily_stats(product_df):
    """
    Takes one product's historical rows and returns average daily demand
    and demand standard deviation.
    """
    avg_daily_demand = product_df["units_sold"].mean()
    demand_std = product_df["units_sold"].std(ddof=0)

    if math.isnan(demand_std):
        demand_std = 0.0

    return avg_daily_demand, demand_std


def calculate_safety_stock(avg_daily_demand, demand_std, lead_time_days, service_z=1.65):
    """
    Basic safety stock formula.
    """
    return service_z * demand_std * math.sqrt(lead_time_days)


def calculate_reorder_point(avg_daily_demand, lead_time_days, safety_stock):
    """
    Reorder Point = demand during lead time + safety stock
    """
    return (avg_daily_demand * lead_time_days) + safety_stock


def calculate_recommended_order_qty(
    current_inventory,
    reorder_point,
    forecast_demand_next_30,
    min_order_qty
):
    """
    Simple first version:
    if inventory is below reorder point, order enough to cover
    the next 30 days of expected demand.
    """
    target_stock = reorder_point + forecast_demand_next_30
    needed = target_stock - current_inventory

    if needed <= 0:
        return 0

    if needed < min_order_qty:
        return min_order_qty

    return math.ceil(needed)
