
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

df = pd.read_csv("business_training_data.csv")

features = [
    "Revenue",
    "Expenses",
    "Cost_of_Goods",
    "Cash_Flow",
    "Inventory",
    "Debt",
    "Transactions",
    "Profit_Margin"
]

X = df[features]
y = df["Loss_Next_Month"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced"
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    predictions
)

print("Model training completed.")
print("Training records:", len(X_train))
print("Testing records:", len(X_test))
print("Model accuracy:", round(accuracy * 100, 2), "%")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        predictions
    )
)

joblib.dump(
    model,
    "business_loss_model.pkl"
)

print("Model saved as business_loss_model.pkl")
