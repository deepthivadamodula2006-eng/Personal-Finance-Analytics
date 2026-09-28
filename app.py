from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import pickle
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

app.secret_key = "finance_analytics_secret_key_change_this"


# =========================================================
# DATABASE
# =========================================================

DATABASE = "login.db"
FINANCE_DATA_DATABASE = DATABASE

USER_DETAILS_EXPORT = Path(__file__).with_name(
    "finance_readable.md"
)


def get_db_connection():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


def get_finance_data_connection():

    conn = sqlite3.connect(FINANCE_DATA_DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


def export_user_details(conn):

    """Create a password-free readable report of users."""

    users = conn.execute(
        "SELECT id, name, email FROM users ORDER BY id"
    ).fetchall()

    def markdown_cell(value):

        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [

        "# Finance database - user details",

        "",

        "This report updates automatically after each successful registration.",

        "Passwords are never included.",

        "",

        "| ID | Name | Email |",

        "| ---: | --- | --- |"

    ]

    lines.extend(

        f"| {user['id']} | "
        f"{markdown_cell(user['name'])} | "
        f"{markdown_cell(user['email'])} |"

        for user in users

    )

    USER_DETAILS_EXPORT.write_text(

        "\n".join(lines) + "\n",

        encoding="utf-8"

    )


def merge_legacy_data(conn):

    """Copy old data into login.db without deleting or replacing accounts."""

    conn.execute("""
        CREATE TABLE IF NOT EXISTS data_migrations (
            source_file TEXT PRIMARY KEY,
            completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    for source_file in ("finance.db", "finance_data.db"):

        source_path = Path(source_file)

        if not source_path.exists() or conn.execute(
            "SELECT 1 FROM data_migrations WHERE source_file = ?",
            (source_file,)
        ).fetchone():

            continue

        source = sqlite3.connect(source_path)

        source.row_factory = sqlite3.Row

        try:

            tables = {
                row["name"]
                for row in source.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }

            user_ids = {}

            if "users" in tables:

                for user in source.execute(
                    "SELECT id, name, email, password FROM users"
                ):

                    conn.execute(
                        "INSERT OR IGNORE INTO users (name, email, password) VALUES (?, ?, ?)",
                        (
                            user["name"],
                            user["email"],
                            user["password"]
                        )
                    )

                    saved_user = conn.execute(
                        "SELECT id FROM users WHERE email = ?",
                        (user["email"],)
                    ).fetchone()

                    user_ids[user["id"]] = saved_user["id"]

            if "prediction_history" in tables:

                fields = [

                    "created_at",
                    "transaction_history",
                    "monthly_income",
                    "monthly_budget",
                    "current_savings",
                    "savings_goal",
                    "rent",
                    "food",
                    "transport",
                    "shopping",
                    "bills",
                    "entertainment",
                    "emi",
                    "other_expenses",
                    "total_expenses",
                    "budget_utilization",
                    "predicted_savings",
                    "remaining_budget",
                    "budget_used_percent",
                    "financial_score",
                    "financial_category"

                ]

                for history in source.execute(
                    "SELECT * FROM prediction_history ORDER BY id"
                ):

                    conn.execute(

                        "INSERT INTO prediction_history "
                        "(user_id, " + ", ".join(fields) + ") VALUES "
                        "(" + ", ".join(["?"] * 22) + ")",

                        [
                            user_ids.get(
                                history["user_id"],
                                history["user_id"]
                            )
                        ]
                        +
                        [
                            history[field]
                            for field in fields
                        ]

                    )

        finally:

            source.close()

        conn.execute(
            "INSERT INTO data_migrations (source_file) VALUES (?)",
            (source_file,)
        )


def init_db():

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL

        )

    """)

    conn.commit()

    export_user_details(conn)

    conn.close()

    finance_conn = get_finance_data_connection()

    finance_conn.execute("""
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            transaction_history TEXT NOT NULL,
            monthly_income REAL NOT NULL,
            monthly_budget REAL NOT NULL,
            current_savings REAL NOT NULL,
            savings_goal REAL NOT NULL,
            rent REAL NOT NULL,
            food REAL NOT NULL,
            transport REAL NOT NULL,
            shopping REAL NOT NULL,
            bills REAL NOT NULL,
            entertainment REAL NOT NULL,
            emi REAL NOT NULL,
            other_expenses REAL NOT NULL,
            total_expenses REAL NOT NULL,
            budget_utilization REAL NOT NULL,
            predicted_savings REAL NOT NULL,
            remaining_budget REAL NOT NULL,
            budget_used_percent REAL NOT NULL,
            financial_score REAL NOT NULL,
            financial_category TEXT NOT NULL
        )
    """)

    merge_legacy_data(finance_conn)

    finance_conn.commit()

    finance_conn.close()


def get_saved_result(user_id):

    """Return the user's most recent saved prediction in template format."""

    conn = get_finance_data_connection()

    try:

        record = conn.execute("""
            SELECT * FROM prediction_history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,)).fetchone()

    finally:

        conn.close()

    if not record:

        return {}

    # =====================================================
    # BUDGET DISPLAY CALCULATIONS
    # =====================================================

    monthly_budget = float(
        record["monthly_budget"]
    )

    total_expenses = float(
        record["total_expenses"]
    )

    if monthly_budget > 0:

        actual_budget_utilization = (
            total_expenses / monthly_budget
        ) * 100

    else:

        actual_budget_utilization = 0

    # Keep the dashboard progress display at a maximum of 100%.

    budget_used_display = min(
        actual_budget_utilization,
        100
    )

    # Amount and percentage spent above the budget.

    extra_amount = max(
        total_expenses - monthly_budget,
        0
    )

    if monthly_budget > 0:

        extra_percentage = (
            extra_amount / monthly_budget
        ) * 100

    else:

        extra_percentage = 0

    return {

        "income":
            record["monthly_income"],

        "budget":
            record["monthly_budget"],

        "expenses":
            record["total_expenses"],

        "savings":
            record["predicted_savings"],

        "predicted_savings":
            record["predicted_savings"],

        "current_savings":
            record["current_savings"],

        "savings_goal":
            record["savings_goal"],

        "goal":
            record["savings_goal"],

        "score":
            record["financial_score"],

        "recommendation":
            record["financial_category"],

        "remaining_budget":
            record["remaining_budget"],

        "budget_used_percent":
            budget_used_display,

        "extra_percentage":
            extra_percentage,

        "extra_amount":
            extra_amount,

        "recommendations_list":
            get_recommendations(
                record["financial_score"]
            ),

        "expense_data": {

            "Rent":
                record["rent"],

            "Food":
                record["food"],

            "Transport":
                record["transport"],

            "Shopping":
                record["shopping"],

            "Bills":
                record["bills"],

            "Entertainment":
                record["entertainment"],

            "EMI":
                record["emi"],

            "Other":
                record["other_expenses"]

        }

    }


# =========================================================
# LOAD MACHINE LEARNING MODEL
# =========================================================

MODEL_PATH = "Backend/model/finance_model.pkl"


with open(MODEL_PATH, "rb") as file:

    model = pickle.load(file)


# =========================================================
# LATEST PREDICTION RESULT
# =========================================================

result = {}


# =========================================================
# LOGIN CHECK
# =========================================================

def is_logged_in():

    return "user_id" in session


# =========================================================
# FINANCIAL HEALTH CATEGORY
# =========================================================

def get_category(score):

    if score >= 90:

        return "Excellent"

    elif score >= 80:

        return "Good"

    elif score >= 70:

        return "Average"

    elif score >= 50:

        return "Needs Improvement"

    else:

        return "Poor"


# =========================================================
# RECOMMENDATIONS
# =========================================================

def get_recommendations(score):

    recommendations = []

    if score >= 90:

        recommendations.extend([

            "Excellent financial health. Keep maintaining your savings.",

            "Continue investing for long-term goals.",

            "Maintain an emergency fund of at least 6 months.",

            "Review your investments regularly."

        ])

    elif score >= 80:

        recommendations.extend([

            "Your financial health is good.",

            "Increase monthly savings if possible.",

            "Reduce unnecessary expenses.",

            "Start investing in low-risk assets."

        ])

    elif score >= 70:

        recommendations.extend([

            "Your financial health is average.",

            "Track your monthly spending.",

            "Reduce entertainment and shopping expenses.",

            "Create a better monthly budget."

        ])

    elif score >= 50:

        recommendations.extend([

            "Spend carefully and avoid unnecessary purchases.",

            "Increase savings gradually.",

            "Review your budget every month.",

            "Avoid taking unnecessary loans."

        ])

    else:

        recommendations.extend([

            "Financial health needs improvement.",

            "Reduce expenses immediately.",

            "Build an emergency savings fund.",

            "Consult a financial advisor if needed."

        ])

    return recommendations


# =========================================================
# INITIALIZE DATABASE
# =========================================================

init_db()


# =========================================================
# ROOT
# =========================================================

@app.route("/")
def index():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    return redirect(
        url_for("home")
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not name or not email or not password:

            return render_template(
                "register.html",
                error="Please fill in all the fields."
            )

        if password != confirm_password:

            return render_template(
                "register.html",
                error="Passwords do not match."
            )

        if len(password) < 6:

            return render_template(
                "register.html",
                error="Password must contain at least 6 characters."
            )

        hashed_password = generate_password_hash(
            password
        )

        conn = None

        try:

            conn = get_db_connection()

            conn.execute(

                """
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
                """,

                (
                    name,
                    email,
                    hashed_password
                )

            )

            conn.commit()

            export_user_details(conn)

        except sqlite3.IntegrityError:

            return render_template(
                "register.html",
                error="An account with this email already exists."
            )

        finally:

            if conn:

                conn.close()

        return redirect(

            url_for(
                "login",
                registered="1"
            )

        )

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            return render_template(
                "login.html",
                error="Please enter your email and password."
            )

        conn = None

        try:

            conn = get_db_connection()

            user = conn.execute(

                """
                SELECT id, name, email, password
                FROM users
                WHERE email = ?
                """,

                (email,)

            ).fetchone()

        finally:

            if conn:

                conn.close()

        if user:

            stored_password = user["password"]

            if check_password_hash(
                stored_password,
                password
            ):

                session.clear()

                session["user_id"] = user["id"]

                session["user_name"] = user["name"]

                session["user_email"] = user["email"]

                session.permanent = True

                return redirect(
                    url_for("home")
                )

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    registered = request.args.get(
        "registered"
    )

    return render_template(
        "login.html",
        registered=registered
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/home")
def home():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    return render_template(
        "index.html",
        result=get_saved_result(
            session["user_id"]
        )
    )


# =========================================================
# ACCOUNT PAGE
# =========================================================

@app.route("/account")
def account():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    conn = None

    try:

        conn = get_db_connection()

        user = conn.execute(

            """
            SELECT id, name, email
            FROM users
            WHERE id = ?
            """,

            (session["user_id"],)

        ).fetchone()

    finally:

        if conn:

            conn.close()

    if not user:

        session.clear()

        return redirect(
            url_for("login")
        )

    return render_template(
        "account.html",
        user=user
    )


# =========================================================
# PREDICTION HISTORY
# =========================================================

@app.route("/history")
def history():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    conn = get_finance_data_connection()

    try:

        predictions = conn.execute("""
            SELECT id,
                   created_at,
                   monthly_income,
                   monthly_budget,
                   total_expenses,
                   predicted_savings,
                   financial_score,
                   financial_category
            FROM prediction_history
            WHERE user_id = ?
            ORDER BY id DESC
        """, (session["user_id"],)).fetchall()

    finally:

        conn.close()

    return render_template(
        "history.html",
        predictions=predictions
    )


# =========================================================
# PREDICTION INPUT PAGE
# =========================================================

@app.route("/predict_page")
def predict_page():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    return render_template(
        "predict.html"
    )


# =========================================================
# PREDICTION
# =========================================================

@app.route("/predict", methods=["POST"])
def predict():

    global result

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    try:

        # =================================================
        # DEFAULT MODEL VALUES
        # =================================================

        age = 25

        gender = "Female"

        occupation = "Student"

        city = "Visakhapatnam"

        month = "January"

        transaction_count = 0

        transaction_history = request.form.get(
            "Transaction_History",
            "Average"
        )


        # =================================================
        # USER INPUTS
        # =================================================

        income = float(
            request.form.get(
                "Monthly_Income",
                0
            )
        )

        budget = float(
            request.form.get(
                "Monthly_Budget",
                0
            )
        )

        current_savings = float(
            request.form.get(
                "Current_Savings",
                0
            )
        )

        savings_goal = float(
            request.form.get(
                "Savings_Goal",
                0
            )
        )

        rent = float(
            request.form.get(
                "Rent",
                0
            )
        )

        food = float(
            request.form.get(
                "Food",
                0
            )
        )

        transport = float(
            request.form.get(
                "Transport",
                0
            )
        )

        shopping = float(
            request.form.get(
                "Shopping",
                0
            )
        )

        bills = float(
            request.form.get(
                "Bills",
                0
            )
        )

        entertainment = float(
            request.form.get(
                "Entertainment",
                0
            )
        )

        emi = float(
            request.form.get(
                "EMI",
                0
            )
        )

        other = float(
            request.form.get(
                "Other_Expenses",
                0
            )
        )


        # =================================================
        # TOTAL EXPENSES
        # =================================================

        total_expenses = (

            rent
            + food
            + transport
            + shopping
            + bills
            + entertainment
            + emi
            + other

        )


        # =================================================
        # BUDGET UTILIZATION
        # =================================================

        if budget > 0:

            budget_utilization = (

                total_expenses / budget

            ) * 100

        else:

            budget_utilization = 0


        # =================================================
        # PREPARE DATA FOR ML MODEL
        # =================================================

        data = pd.DataFrame([{

            "Age":
                age,

            "Gender":
                gender,

            "Occupation":
                occupation,

            "City":
                city,

            "Month":
                month,

            "Transaction_History":
                transaction_history,

            "Monthly_Income":
                income,

            "Monthly_Budget":
                budget,

            "Rent":
                rent,

            "Food":
                food,

            "Transport":
                transport,

            "Shopping":
                shopping,

            "Bills":
                bills,

            "Entertainment":
                entertainment,

            "EMI":
                emi,

            "Other_Expenses":
                other,

            "Total_Monthly_Expenses":
                total_expenses,

            "Current_Savings":
                current_savings,

            "Savings_Goal":
                savings_goal,

            "Transaction_Count":
                transaction_count,

            "Budget_Utilization (%)":
                budget_utilization,

            "Recommendation":
                "Auto"

        }])


        # =================================================
        # MACHINE LEARNING PREDICTION
        # =================================================
        #
        # RULE 1:
        # No current savings = financial score 0.
        #
        # RULE 2:
        # If expenses are greater than BOTH the monthly
        # budget and current savings = financial score 0.
        #
        # RULE 3:
        # If there are no expenses and savings exist,
        # financial score = 100.
        #
        # RULE 4:
        # Otherwise use the Random Forest prediction.
        #
        # =================================================

        if current_savings <= 0:

            score = 0.0

        elif (
            total_expenses > budget
            and total_expenses > current_savings
        ):

            score = 0.0

        elif total_expenses == 0:

            score = 100.0

        else:

            score = round(
                float(
                    model.predict(data)[0]
                ),
                2
            )


        # =================================================
        # KEEP SCORE BETWEEN 0 AND 100
        # =================================================

        score = max(
            0,
            min(score, 100)
        )


        # =================================================
        # FINANCIAL CATEGORY
        # =================================================

        category = get_category(
            score
        )


        # =================================================
        # PREDICTED SAVINGS
        # =================================================
        #
        # This is NOT Current Savings.
        #
        # Predicted Savings =
        # Monthly Income - Total Expenses
        #
        # Example:
        # Income = ₹50,000
        # Expenses = ₹30,000
        # Predicted Savings = ₹20,000
        #
        # =================================================

        predicted_savings = max(

            income - total_expenses,

            0

        )


        # =================================================
        # REMAINING BUDGET
        # =================================================

        remaining_budget = max(

            budget - total_expenses,

            0

        )


        # =================================================
        # BUDGET DISPLAY CALCULATIONS
        # =================================================

        if budget > 0:

            actual_budget_utilization = (

                total_expenses / budget

            ) * 100

        else:

            actual_budget_utilization = 0


        # Display usage is capped at 100%.
        # The actual utilization is still stored separately above.

        budget_used_percent = min(
            actual_budget_utilization,
            100
        )


        # Calculate amount spent above budget.

        extra_amount = max(
            total_expenses - budget,
            0
        )


        # Calculate percentage spent above budget.

        if budget > 0:

            extra_percentage = (
                extra_amount / budget
            ) * 100

        else:

            extra_percentage = 0


        # =================================================
        # STORE RESULT
        # =================================================

        result = {

            # ---------------------------------------------
            # BASIC FINANCIAL VALUES
            # ---------------------------------------------

            "income":
                income,

            "budget":
                budget,

            "expenses":
                total_expenses,

            "extra_percentage":
                extra_percentage,

            "extra_amount":
                extra_amount,


            # ---------------------------------------------
            # PREDICTED SAVINGS
            # ---------------------------------------------

            "savings":
                predicted_savings,

            "predicted_savings":
                predicted_savings,


            # ---------------------------------------------
            # ACTUAL CURRENT SAVINGS
            # ---------------------------------------------

            "current_savings":
                current_savings,


            # ---------------------------------------------
            # SAVINGS GOAL
            # ---------------------------------------------

            "savings_goal":
                savings_goal,

            # Keep old key too for compatibility

            "goal":
                savings_goal,


            # ---------------------------------------------
            # SCORE
            # ---------------------------------------------

            "score":
                score,


            # ---------------------------------------------
            # RECOMMENDATION
            # ---------------------------------------------

            "recommendation":
                category,


            # ---------------------------------------------
            # BUDGET
            # ---------------------------------------------

            "remaining_budget":
                remaining_budget,

            "budget_used_percent":
                budget_used_percent,


            # ---------------------------------------------
            # RECOMMENDATIONS
            # ---------------------------------------------

            "recommendations_list":
                get_recommendations(
                    score
                ),


            # ---------------------------------------------
            # EXPENSE DATA
            # ---------------------------------------------

            "expense_data": {

                "Rent":
                    rent,

                "Food":
                    food,

                "Transport":
                    transport,

                "Shopping":
                    shopping,

                "Bills":
                    bills,

                "Entertainment":
                    entertainment,

                "EMI":
                    emi,

                "Other":
                    other

            }

        }


        # =================================================
        # SAVE PREDICTION HISTORY
        # =================================================

        conn = get_finance_data_connection()

        try:

            conn.execute("""
                INSERT INTO prediction_history (
                    user_id,
                    transaction_history,
                    monthly_income,
                    monthly_budget,
                    current_savings,
                    savings_goal,
                    rent,
                    food,
                    transport,
                    shopping,
                    bills,
                    entertainment,
                    emi,
                    other_expenses,
                    total_expenses,
                    budget_utilization,
                    predicted_savings,
                    remaining_budget,
                    budget_used_percent,
                    financial_score,
                    financial_category
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (

                session["user_id"],
                transaction_history,
                income,
                budget,
                current_savings,
                savings_goal,
                rent,
                food,
                transport,
                shopping,
                bills,
                entertainment,
                emi,
                other,
                total_expenses,
                budget_utilization,
                predicted_savings,
                remaining_budget,
                budget_used_percent,
                score,
                category

            ))

            conn.commit()

        finally:

            conn.close()


        # =================================================
        # REDIRECT TO DASHBOARD
        # =================================================

        return redirect(
            url_for("dashboard")
        )


    except (ValueError, TypeError):

        return render_template(

            "predict.html",

            error=(
                "Please enter valid numbers "
                "in all financial fields."
            )

        )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )


    saved_result = get_saved_result(
        session["user_id"]
    )


    if not saved_result:

        return redirect(
            url_for("predict_page")
        )


    return render_template(

        "dashboard.html",

        **saved_result

    )


# =========================================================
# BUDGET
# =========================================================

@app.route("/budget")
def budget():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )


    saved_result = get_saved_result(
        session["user_id"]
    )


    if not saved_result:

        return redirect(
            url_for("predict_page")
        )


    income = saved_result.get(
        "income",
        0
    )


    budget_value = saved_result.get(
        "budget",
        0
    )


    expenses = saved_result.get(
        "expenses",
        0
    )


    # Current savings already available.

    current_savings = saved_result.get(
        "current_savings",
        0
    )


    # Monthly savings are calculated from this month's income and expenses.

    monthly_savings = max(
        income - expenses,
        0
    )


    # Amount remaining inside the monthly budget.

    budget_left = max(
        budget_value - expenses,
        0
    )


    # Total available combines budget left,
    # monthly savings, and existing savings.

    total_available = (
        budget_left
        + monthly_savings
        + current_savings
    )


    if budget_value > 0:

        expense_percent = round(
            (expenses / budget_value) * 100,
            1
        )

    else:

        expense_percent = 0


    if income > 0:

        savings_percent = round(
            (monthly_savings / income) * 100,
            1
        )

    else:

        savings_percent = 0


    return render_template(

        "budget.html",

        income=income,

        budget=budget_value,

        expenses=expenses,

        savings=monthly_savings,

        current_savings=current_savings,

        budget_left=budget_left,

        total_available=total_available,

        expense_percent=expense_percent,

        savings_percent=savings_percent

    )


# =========================================================
# RECOMMENDATIONS
# =========================================================

@app.route("/recommendations")
def recommendations():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )


    saved_result = get_saved_result(
        session["user_id"]
    )


    if not saved_result:

        return redirect(
            url_for("predict_page")
        )


    return render_template(

        "recommendations.html",

        score=saved_result.get(
            "score",
            0
        ),

        recommendation=saved_result.get(
            "recommendation",
            ""
        ),

        recommendations=saved_result.get(
            "recommendations_list",
            []
        )

    )


# =========================================================
# SUMMARY
# =========================================================

@app.route("/summary")
def summary():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )


    saved_result = get_saved_result(
        session["user_id"]
    )


    if not saved_result:

        return redirect(
            url_for("predict_page")
        )


    return render_template(

        "summary.html",

        **saved_result

    )


# =========================================================
# ABOUT
# =========================================================

@app.route("/about")
def about():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )


    saved_result = get_saved_result(
        session["user_id"]
    )


    if not saved_result:

        return render_template(

            "about.html",

            income=0,

            expenses=0,

            savings=0,

            budget=0,

            score=0

        )


    return render_template(

        "about.html",

        income=saved_result.get(
            "income",
            0
        ),

        expenses=saved_result.get(
            "expenses",
            0
        ),

        savings=saved_result.get(
            "predicted_savings",
            0
        ),

        budget=saved_result.get(
            "budget",
            0
        ),

        score=saved_result.get(
            "score",
            0
        )

    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True,

        use_reloader=False

    )