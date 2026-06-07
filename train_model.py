import joblib
import warnings

from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

warnings.filterwarnings("ignore")


def main():
    # ------------------------------------------------------------------
    # 1. Load built-in Breast Cancer dataset
    # ------------------------------------------------------------------
    print("Loading Breast Cancer Wisconsin dataset...")
    data = load_breast_cancer()
    # Slice first 10 columns corresponding to the 'mean' features
    X = data.data[:, :10]
    y = data.target

    # Feature names for later validation in Flask
    feature_names = list(data.feature_names[:10])

    # Invert target so 1 = Malignant (High Risk), 0 = Benign (Low Risk)
    y = 1 - y

    print(f"Samples: {X.shape[0]}, Features: {X.shape[1]}")
    print(f"Benign (Low Risk): {(y == 0).sum()}")
    print(f"Malignant (High Risk): {(y == 1).sum()}\n")

    # ------------------------------------------------------------------
    # 2. Train / Test Split
    # ------------------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # ------------------------------------------------------------------
    # 3. Train Random Forest
    # ------------------------------------------------------------------
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=5,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    # ------------------------------------------------------------------
    # 4. Evaluate
    # ------------------------------------------------------------------
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"\nTest Accuracy: {acc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Low Risk", "High Risk"]))

    # ------------------------------------------------------------------
    # 5. Save artifact (model + metadata)
    # ------------------------------------------------------------------
    artifact = {
        "model": model,
        "feature_names": feature_names,
        "dataset_description": "Breast Cancer Wisconsin (built-in)",
        "target_mapping": {"0": "Benign / Low Risk", "1": "Malignant / High Risk"},
    }

    joblib.dump(artifact, "health_model.joblib")

    print("\n✅ Model artifact saved to 'health_model.joblib'")


if __name__ == "__main__":
    main()