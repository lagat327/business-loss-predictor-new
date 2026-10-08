
import sqlite3
import os
import joblib
import pandas as pd

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_file
)

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)

app = Flask("business_loss_predictor")

model = joblib.load(
    "business_loss_model.pkl"
)

UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def get_business_id(business_name):

    connection = sqlite3.connect(
        "database.db"
    )

    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM businesses WHERE business_name = ?",
        (business_name,)
    )

    result = cursor.fetchone()

    if result:

        business_id = result[0]

    else:

        cursor.execute(
            """
            INSERT INTO businesses
            (business_name)
            VALUES (?)
            """,
            (business_name,)
        )

        business_id = cursor.lastrowid

        connection.commit()

    connection.close()

    return business_id


def save_monthly_data(
    business_id,
    dataframe
):

    connection = sqlite3.connect(
        "database.db"
    )

    cursor = connection.cursor()

    for _, row in dataframe.iterrows():

        month = int(row["Month"])

        revenue = float(row["Revenue"])

        expenses = float(row["Expenses"])

        cost_of_goods = float(
            row["Cost_of_Goods"]
        )

        cash_flow = float(
            row["Cash_Flow"]
        )

        inventory = float(
            row["Inventory"]
        )

        debt = float(
            row["Debt"]
        )

        transactions = int(
            row["Transactions"]
        )

        cursor.execute(
            """
            SELECT id
            FROM financial_data
            WHERE business_id = ?
            AND month = ?
            """,
            (
                business_id,
                month
            )
        )

        existing = cursor.fetchone()

        if existing:

            cursor.execute(
                """
                UPDATE financial_data
                SET
                    revenue = ?,
                    expenses = ?,
                    cost_of_goods = ?,
                    cash_flow = ?,
                    inventory = ?,
                    debt = ?,
                    transactions = ?
                WHERE business_id = ?
                AND month = ?
                """,
                (
                    revenue,
                    expenses,
                    cost_of_goods,
                    cash_flow,
                    inventory,
                    debt,
                    transactions,
                    business_id,
                    month
                )
            )

        else:

            cursor.execute(
                """
                INSERT INTO financial_data
                (
                    business_id,
                    month,
                    revenue,
                    expenses,
                    cost_of_goods,
                    cash_flow,
                    inventory,
                    debt,
                    transactions
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    business_id,
                    month,
                    revenue,
                    expenses,
                    cost_of_goods,
                    cash_flow,
                    inventory,
                    debt,
                    transactions
                )
            )

    connection.commit()

    connection.close()


@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        business_name = request.form[
            "business_name"
        ]

        business_id = get_business_id(
            business_name
        )

        data = []

        for month in range(1, 13):

            data.append({

                "Month": month,

                "Revenue": float(
                    request.form[
                        f"revenue_{month}"
                    ]
                ),

                "Expenses": float(
                    request.form[
                        f"expenses_{month}"
                    ]
                ),

                "Cost_of_Goods": float(
                    request.form[
                        f"cost_of_goods_{month}"
                    ]
                ),

                "Cash_Flow": float(
                    request.form[
                        f"cash_flow_{month}"
                    ]
                ),

                "Inventory": float(
                    request.form[
                        f"inventory_{month}"
                    ]
                ),

                "Debt": float(
                    request.form[
                        f"debt_{month}"
                    ]
                ),

                "Transactions": int(
                    request.form[
                        f"transactions_{month}"
                    ]
                )
            })

        dataframe = pd.DataFrame(
            data
        )

        save_monthly_data(
            business_id,
            dataframe
        )

        return redirect(
            url_for(
                "predict",
                business_id=business_id
            )
        )

    return render_template(
        "index.html"
    )


@app.route("/upload", methods=["GET", "POST"])
def upload():

    if request.method == "POST":

        business_name = request.form[
            "business_name"
        ]

        uploaded_file = request.files.get(
            "file"
        )

        if not business_name:

            return render_template(
                "upload.html",
                error="Please enter the business name."
            )

        if not uploaded_file:

            return render_template(
                "upload.html",
                error="Please select an Excel or CSV file."
            )

        filename = uploaded_file.filename

        if not filename:

            return render_template(
                "upload.html",
                error="Please select a file."
            )

        extension = os.path.splitext(
            filename
        )[1].lower()

        if extension not in [
            ".csv",
            ".xlsx"
        ]:

            return render_template(
                "upload.html",
                error="Only CSV and Excel (.xlsx) files are supported."
            )

        saved_filename = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        uploaded_file.save(
            saved_filename
        )

        try:

            if extension == ".csv":

                dataframe = pd.read_csv(
                    saved_filename
                )

            else:

                dataframe = pd.read_excel(
                    saved_filename
                )

        except Exception:

            return render_template(
                "upload.html",
                error="The file could not be read. Check that it is a valid CSV or Excel file."
            )

        required_columns = [
            "Month",
            "Revenue",
            "Expenses",
            "Cost_of_Goods",
            "Cash_Flow",
            "Inventory",
            "Debt",
            "Transactions"
        ]

        missing_columns = [

            column

            for column in required_columns

            if column not in dataframe.columns

        ]

        if missing_columns:

            return render_template(
                "upload.html",
                error=(
                    "Missing columns: "
                    + ", ".join(
                        missing_columns
                    )
                )
            )

        if len(dataframe) != 12:

            return render_template(
                "upload.html",
                error="The file must contain exactly 12 rows, one for each month."
            )

        try:

            dataframe = dataframe[
                required_columns
            ].copy()

            dataframe["Month"] = pd.to_numeric(
                dataframe["Month"]
            )

            dataframe["Revenue"] = pd.to_numeric(
                dataframe["Revenue"]
            )

            dataframe["Expenses"] = pd.to_numeric(
                dataframe["Expenses"]
            )

            dataframe["Cost_of_Goods"] = pd.to_numeric(
                dataframe["Cost_of_Goods"]
            )

            dataframe["Cash_Flow"] = pd.to_numeric(
                dataframe["Cash_Flow"]
            )

            dataframe["Inventory"] = pd.to_numeric(
                dataframe["Inventory"]
            )

            dataframe["Debt"] = pd.to_numeric(
                dataframe["Debt"]
            )

            dataframe["Transactions"] = pd.to_numeric(
                dataframe["Transactions"]
            )

        except Exception:

            return render_template(
                "upload.html",
                error="All financial values must be numeric."
            )

        months = sorted(
            dataframe["Month"].tolist()
        )

        if months != list(
            range(1, 13)
        ):

            return render_template(
                "upload.html",
                error="The Month column must contain numbers from 1 to 12."
            )

        if dataframe.isnull().any().any():

            return render_template(
                "upload.html",
                error="The file contains empty or invalid values."
            )

        if (
            dataframe["Transactions"] < 0
        ).any():

            return render_template(
                "upload.html",
                error="Transactions cannot be negative."
            )

        business_id = get_business_id(
            business_name
        )

        save_monthly_data(
            business_id,
            dataframe
        )

        try:

            os.remove(
                saved_filename
            )

        except OSError:

            pass

        return redirect(
            url_for(
                "predict",
                business_id=business_id
            )
        )

    return render_template(
        "upload.html"
    )


@app.route("/download-template")
def download_template():

    dataframe = pd.DataFrame({

        "Month": range(1, 13),

        "Revenue": [0] * 12,

        "Expenses": [0] * 12,

        "Cost_of_Goods": [0] * 12,

        "Cash_Flow": [0] * 12,

        "Inventory": [0] * 12,

        "Debt": [0] * 12,

        "Transactions": [0] * 12

    })

    filepath = os.path.join(
        os.getcwd(),
        "business_financial_template.xlsx"
    )

    dataframe.to_excel(
        filepath,
        index=False
    )

    return send_file(
        filepath,
        as_attachment=True,
        download_name="business_financial_template.xlsx"
    )


def get_report_data(business_id):

    connection = sqlite3.connect(
        "database.db"
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT business_name
        FROM businesses
        WHERE id = ?
        """,
        (business_id,)
    )

    business = cursor.fetchone()

    cursor.execute(
        """
        SELECT
            month,
            revenue,
            expenses,
            cost_of_goods,
            cash_flow,
            inventory,
            debt,
            transactions
        FROM financial_data
        WHERE business_id = ?
        ORDER BY month
        """,
        (business_id,)
    )

    rows = cursor.fetchall()

    connection.close()

    if not business or not rows:

        return None

    latest = rows[-1]

    revenue = float(
        latest["revenue"]
    )

    expenses = float(
        latest["expenses"]
    )

    cost_of_goods = float(
        latest["cost_of_goods"]
    )

    cash_flow = float(
        latest["cash_flow"]
    )

    inventory = float(
        latest["inventory"]
    )

    debt = float(
        latest["debt"]
    )

    transactions = int(
        latest["transactions"]
    )

    profit = (
        revenue
        - expenses
        - cost_of_goods
    )

    if revenue != 0:

        profit_margin = (
            profit / revenue
        ) * 100

    else:

        profit_margin = 0

    input_data = [[
        revenue,
        expenses,
        cost_of_goods,
        cash_flow,
        inventory,
        debt,
        transactions,
        profit_margin
    ]]

    prediction = model.predict(
        input_data
    )[0]

    probability = model.predict_proba(
        input_data
    )[0][1]

    risk_score = round(
        probability * 100,
        2
    )

    if risk_score >= 70:

        risk_level = "High"

    elif risk_score >= 40:

        risk_level = "Medium"

    else:

        risk_level = "Low"

    monthly_data = []

    total_revenue = 0
    total_expenses = 0
    total_cost_of_goods = 0
    total_profit = 0
    total_transactions = 0

    for row in rows:

        row_revenue = float(
            row["revenue"]
        )

        row_expenses = float(
            row["expenses"]
        )

        row_cost = float(
            row["cost_of_goods"]
        )

        row_cash_flow = float(
            row["cash_flow"]
        )

        row_inventory = float(
            row["inventory"]
        )

        row_debt = float(
            row["debt"]
        )

        row_transactions = int(
            row["transactions"]
        )

        row_profit = (
            row_revenue
            - row_expenses
            - row_cost
        )

        if row_revenue != 0:

            row_margin = (
                row_profit
                / row_revenue
            ) * 100

        else:

            row_margin = 0

        monthly_data.append({

            "month": row["month"],

            "revenue": round(
                row_revenue,
                2
            ),

            "expenses": round(
                row_expenses,
                2
            ),

            "cost_of_goods": round(
                row_cost,
                2
            ),

            "cash_flow": round(
                row_cash_flow,
                2
            ),

            "inventory": round(
                row_inventory,
                2
            ),

            "debt": round(
                row_debt,
                2
            ),

            "transactions": row_transactions,

            "profit": round(
                row_profit,
                2
            ),

            "profit_margin": round(
                row_margin,
                2
            )
        })

        total_revenue += row_revenue

        total_expenses += row_expenses

        total_cost_of_goods += row_cost

        total_profit += row_profit

        total_transactions += row_transactions

    if total_revenue != 0:

        average_profit_margin = (
            total_profit
            / total_revenue
        ) * 100

    else:

        average_profit_margin = 0

    average_monthly_profit = (
        total_profit / len(monthly_data)
        if monthly_data
        else 0
    )

    best_month = max(
        monthly_data,
        key=lambda row: row["profit"]
    )

    worst_month = min(
        monthly_data,
        key=lambda row: row["profit"]
    )

    highest_revenue_month = max(
        monthly_data,
        key=lambda row: row["revenue"]
    )

    lowest_revenue_month = min(
        monthly_data,
        key=lambda row: row["revenue"]
    )

    risk_factors = []

    recommendations = []

    if len(rows) >= 2:

        previous = rows[-2]

        previous_revenue = float(
            previous["revenue"]
        )

        previous_expenses = float(
            previous["expenses"]
        )

        previous_cash_flow = float(
            previous["cash_flow"]
        )

        previous_profit = (
            previous_revenue
            - previous_expenses
            - float(
                previous["cost_of_goods"]
            )
        )

        if revenue < previous_revenue:

            risk_factors.append(
                "Revenue is declining compared with the previous month."
            )

            recommendations.append(
                "Investigate the cause of declining sales and improve customer acquisition."
            )

        if (
            expenses > previous_expenses
            and revenue <= previous_revenue
        ):

            risk_factors.append(
                "Expenses are increasing while revenue is not increasing."
            )

            recommendations.append(
                "Review operating expenses and reduce unnecessary costs."
            )

        if profit < previous_profit:

            risk_factors.append(
                "Profit is declining compared with the previous month."
            )

            recommendations.append(
                "Review pricing, expenses and cost of goods to protect profit."
            )

        if cash_flow < previous_cash_flow:

            risk_factors.append(
                "Cash flow is declining."
            )

            recommendations.append(
                "Improve cash collection and control outgoing payments."
            )

    if profit_margin < 10:

        risk_factors.append(
            "Profit margin is below 10%."
        )

        recommendations.append(
            "Improve margins by controlling costs or reviewing pricing."
        )

    if revenue > 0:

        debt_ratio = (
            debt / revenue
        ) * 100

        if debt_ratio > 50:

            risk_factors.append(
                "Debt is high relative to revenue."
            )

            recommendations.append(
                "Reduce debt exposure and avoid unnecessary borrowing."
            )

    if cash_flow < 0:

        risk_factors.append(
            "Cash flow is negative."
        )

        recommendations.append(
            "Prioritize positive cash flow and maintain sufficient working capital."
        )

    if profit < 0:

        risk_factors.append(
            "The latest month shows a loss."
        )

        recommendations.append(
            "Urgently review revenue, expenses and cost of goods."
        )

    if not risk_factors:

        risk_factors.append(
            "No major financial warning signs were detected."
        )

    if not recommendations:

        recommendations.append(
            "Continue monitoring the business financial indicators every month."
        )

    return {
        "business_name": business["business_name"],
        "risk_score": risk_score,
        "risk_level": risk_level,
        "prediction": int(prediction),
        "monthly_data": monthly_data,
        "total_revenue": round(total_revenue, 2),
        "total_expenses": round(total_expenses, 2),
        "total_cost_of_goods": round(
            total_cost_of_goods,
            2
        ),
        "total_profit": round(
            total_profit,
            2
        ),
        "average_profit_margin": round(
            average_profit_margin,
            2
        ),
        "total_transactions": total_transactions,
        "average_monthly_profit": round(
            average_monthly_profit,
            2
        ),
        "best_month": best_month,
        "worst_month": worst_month,
        "highest_revenue_month": highest_revenue_month,
        "lowest_revenue_month": lowest_revenue_month,
        "risk_factors": risk_factors,
        "recommendations": recommendations
    }


@app.route("/predict/<int:business_id>")
def predict(business_id):

    report = get_report_data(
        business_id
    )

    if not report:

        return "Business data not found."

    return render_template(
        "report.html",
        **report
    )


@app.route("/pdf/<int:business_id>")
def download_pdf(business_id):

    report = get_report_data(
        business_id
    )

    if not report:

        return "Business data not found."

    filename = (
        f"annual_report_{business_id}.pdf"
    )

    filepath = os.path.join(
        os.getcwd(),
        filename
    )

    document = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "Annual Financial Report",
            styles["Title"]
        )
    )

    story.append(
        Spacer(1, 8)
    )

    story.append(
        Paragraph(
            f"Business: {report['business_name']}",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            "Financial analysis based on 12 months of business data.",
            styles["BodyText"]
        )
    )

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "Annual Financial Summary",
            styles["Heading2"]
        )
    )

    summary_data = [

        ["Financial Indicator", "Annual Result"],

        [
            "Total Revenue",
            f"{report['total_revenue']:,.2f}"
        ],

        [
            "Total Expenses",
            f"{report['total_expenses']:,.2f}"
        ],

        [
            "Total Cost of Goods",
            f"{report['total_cost_of_goods']:,.2f}"
        ],

        [
            "Total Annual Profit",
            f"{report['total_profit']:,.2f}"
        ],

        [
            "Average Profit Margin",
            f"{report['average_profit_margin']}%"
        ],

        [
            "Total Transactions",
            f"{report['total_transactions']:,}"
        ],

        [
            "Average Monthly Profit",
            f"{report['average_monthly_profit']:,.2f}"
        ]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            90 * mm,
            80 * mm
        ]
    )

    summary_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    story.append(
        summary_table
    )

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "Annual Performance Analysis",
            styles["Heading2"]
        )
    )

    analysis_data = [

        ["Analysis", "Result"],

        [
            "Best Performing Month",
            f"Month {report['best_month']['month']} - Profit {report['best_month']['profit']:,.2f}"
        ],

        [
            "Worst Performing Month",
            f"Month {report['worst_month']['month']} - Profit {report['worst_month']['profit']:,.2f}"
        ],

        [
            "Highest Revenue Month",
            f"Month {report['highest_revenue_month']['month']} - Revenue {report['highest_revenue_month']['revenue']:,.2f}"
        ],

        [
            "Lowest Revenue Month",
            f"Month {report['lowest_revenue_month']['month']} - Revenue {report['lowest_revenue_month']['revenue']:,.2f}"
        ]
    ]

    analysis_table = Table(
        analysis_data,
        colWidths=[
            70 * mm,
            100 * mm
        ]
    )

    analysis_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    story.append(
        analysis_table
    )

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "Next-Month Loss Prediction",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            f"Risk Level: {report['risk_level']}",
            styles["BodyText"]
        )
    )

    story.append(
        Paragraph(
            f"Risk Score: {report['risk_score']}%",
            styles["BodyText"]
        )
    )

    if report["prediction"] == 1:

        prediction_text = (
            "The model predicts that the business may "
            "operate at a loss next month."
        )

    else:

        prediction_text = (
            "The model predicts that the business is "
            "unlikely to operate at a loss next month."
        )

    story.append(
        Paragraph(
            prediction_text,
            styles["BodyText"]
        )
    )

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "Risk Factors",
            styles["Heading2"]
        )
    )

    for factor in report["risk_factors"]:

        story.append(
            Paragraph(
                f"• {factor}",
                styles["BodyText"]
            )
        )

        story.append(
            Spacer(1, 5)
        )

    story.append(
        Spacer(1, 10)
    )

    story.append(
        Paragraph(
            "Recommendations",
            styles["Heading2"]
        )
    )

    for recommendation in report["recommendations"]:

        story.append(
            Paragraph(
                f"• {recommendation}",
                styles["BodyText"]
            )
        )

        story.append(
            Spacer(1, 5)
        )

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "Monthly Financial Data",
            styles["Heading2"]
        )
    )

    monthly_table_data = [

        [
            "Month",
            "Revenue",
            "Expenses",
            "COGS",
            "Cash Flow",
            "Debt",
            "Profit",
            "Margin"
        ]
    ]

    for row in report["monthly_data"]:

        monthly_table_data.append([

            f"Month {row['month']}",

            f"{row['revenue']:,.0f}",

            f"{row['expenses']:,.0f}",

            f"{row['cost_of_goods']:,.0f}",

            f"{row['cash_flow']:,.0f}",

            f"{row['debt']:,.0f}",

            f"{row['profit']:,.0f}",

            f"{row['profit_margin']:.2f}%"
        ])

    monthly_table = Table(
        monthly_table_data,
        repeatRows=1,
        colWidths=[
            20 * mm,
            25 * mm,
            25 * mm,
            23 * mm,
            25 * mm,
            23 * mm,
            25 * mm,
            20 * mm
        ]
    )

    monthly_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                4
            )
        ])
    )

    story.append(
        monthly_table
    )

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "Conclusion",
            styles["Heading2"]
        )
    )

    if report["total_profit"] > 0:

        conclusion = (
            "The business generated a positive annual profit "
            "based on the 12 months of financial information provided."
        )

    else:

        conclusion = (
            "The business recorded an overall annual loss "
            "based on the 12 months of financial information provided."
        )

    story.append(
        Paragraph(
            conclusion,
            styles["BodyText"]
        )
    )

    document.build(
        story
    )

    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename
    )


if __name__ == "__main__":

    app.run(
        debug=True
    )

