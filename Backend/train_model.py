import pandas as pd
import pickle

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# ==========================================
# Load Dataset
# ==========================================

df = pd.read_excel("data/Cleaned Dataset.xlsx")

# ==========================================
# Remove Unnecessary Columns
# ==========================================

for col in ["User_ID", "Name"]:
    if col in df.columns:
        df.drop(columns=col, inplace=True)

# ==========================================
# Features and Target
# ==========================================

X = df.drop(columns=["Financial_Health_Score"])
y = df["Financial_Health_Score"]

# ==========================================
# Categorical and Numerical Columns
# ==========================================

categorical_columns = X.select_dtypes(include=["object"]).columns

numeric_columns = X.select_dtypes(exclude=["object"]).columns

# ==========================================
# Preprocessing
# ==========================================

numeric_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="median"))
])

categorical_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore"))
])

preprocessor = ColumnTransformer([
    ("num", numeric_transformer, numeric_columns),
    ("cat", categorical_transformer, categorical_columns)
])

# ==========================================
# Model Pipeline
# ==========================================

model = Pipeline([
    ("preprocessor", preprocessor),
    ("regressor", RandomForestRegressor(
        n_estimators=200,
        random_state=42
    ))
])

# ==========================================
# Train-Test Split
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

# ==========================================
# Train Model
# ==========================================

print("Training Started...")

model.fit(X_train, y_train)

print("Training Completed")

# ==========================================
# Show 200 Tree Predictions
# ==========================================

forest = model.named_steps["regressor"]

print("\n==========================================")
print("RANDOM FOREST - 200 TREE INFORMATION")
print("==========================================")

print("Number of Trees:", len(forest.estimators_))

# Predictions of all trees on the TEST DATA
X_test_transformed = model.named_steps["preprocessor"].transform(X_test)

tree_predictions = []

for i, tree in enumerate(forest.estimators_, start=1):

    tree_prediction = tree.predict(X_test_transformed)

    tree_predictions.append(tree_prediction)

    print(f"\nTree {i}")
    print("Predictions:", tree_prediction)

print("\n==========================================")
print("200 TREE CALCULATION COMPLETED")
print("==========================================")

# ==========================================
# Evaluate Model
# ==========================================

predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, predictions)

r2 = r2_score(y_test, predictions)

print("Mean Absolute Error (MAE):", round(mae, 2))

print("R2 Score:", round(r2, 4))

print("Model Performance:", round(r2 * 100, 2), "%")

# ==========================================
# Save Model
# ==========================================

pickle.dump(
    model,
    open("Backend/model/finance_model.pkl", "wb")
)

print("Model Saved Successfully")