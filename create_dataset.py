
import pandas as pd
import numpy as np

np.random.seed(42)

businesses = 300
months = 12

data = []

for business_id in range(1, businesses + 1):

    base_revenue = np.random.randint(50000, 500000)

    business_condition = np.random.choice(
        ["healthy", "unstable", "struggling"],
        p=[0.50, 0.30, 0.20]
    )

    for month in range(1, months + 1):

        if business_condition == "healthy":
            revenue_growth = np.random.normal(0.03, 0.05)
            expenses_rate = np.random.uniform(0.25, 0.40)
            cost_rate = np.random.uniform(0.20, 0.35)

        elif business_condition == "unstable":
            revenue_growth = np.random.normal(-0.02, 0.08)
            expenses_rate = np.random.uniform(0.35, 0.55)
            cost_rate = np.random.uniform(0.30, 0.50)

        else:
            revenue_growth = np.random.normal(-0.05, 0.10)
            expenses_rate = np.random.uniform(0.45, 0.70)
            cost_rate = np.random.uniform(0.35, 0.60)

        revenue = base_revenue * (
            1 + revenue_growth
        )

        revenue = max(revenue, 10000)

        expenses = revenue * expenses_rate

        cost_of_goods = revenue * cost_rate

        if business_condition == "struggling":
            expenses += revenue * np.random.uniform(0.05, 0.20)

        if np.random.random() < 0.10:
            unexpected_cost = revenue * np.random.uniform(0.20, 0.50)
            expenses += unexpected_cost

        cash_flow = (
            revenue
            - expenses
            - cost_of_goods
        )

        inventory = revenue * np.random.uniform(
            0.05, 0.30
        )

        debt = revenue * np.random.uniform(
            0.05, 1.00
        )

        transactions = int(
            revenue / np.random.uniform(500, 2500)
        )

        profit = (
            revenue
            - expenses
            - cost_of_goods
        )

        profit_margin = (
            profit / revenue * 100
            if revenue != 0
            else 0
        )

        data.append({
            "Business_ID": business_id,
            "Month": month,
            "Revenue": round(revenue, 2),
            "Expenses": round(expenses, 2),
            "Cost_of_Goods": round(cost_of_goods, 2),
            "Cash_Flow": round(cash_flow, 2),
            "Inventory": round(inventory, 2),
            "Debt": round(debt, 2),
            "Transactions": transactions,
            "Profit": round(profit, 2),
            "Profit_Margin": round(profit_margin, 2)
        })


df = pd.DataFrame(data)

df["Next_Month_Profit"] = (
    df.groupby("Business_ID")["Profit"]
    .shift(-1)
)

df["Loss_Next_Month"] = (
    df["Next_Month_Profit"] < 0
).astype(int)

df = df.dropna(
    subset=["Next_Month_Profit"]
)

df.to_csv(
    "business_training_data.csv",
    index=False
)

print("Dataset created successfully.")
print("Businesses:", businesses)
print("Months per business:", months)
print("Training records:", len(df))
print("Loss cases:", df["Loss_Next_Month"].sum())
print(
    "Non-loss cases:",
    (df["Loss_Next_Month"] == 0).sum()
)
print(
    "Loss percentage:",
    round(
        df["Loss_Next_Month"].mean() * 100,
        2
    ),
    "%"
)
print("Saved as: business_training_data.csv")
