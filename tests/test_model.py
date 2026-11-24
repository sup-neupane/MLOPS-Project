
# load test + signature test + performance test

import unittest
import mlflow
import os
import json
import pandas as pd
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pickle


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestModelLoading(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # Set up DagsHub credentials for MLflow tracking
        dagshub_token = os.getenv("CAPSTONE_TEST")
        repo_owner = os.getenv("DAGSHUB_REPO_OWNER")

        if not dagshub_token:
            raise EnvironmentError(
                "CAPSTONE_TEST environment variable is not set"
            )

        if not repo_owner:
            raise EnvironmentError(
                "DAGSHUB_REPO_OWNER environment variable is not set"
            )

        os.environ["MLFLOW_TRACKING_USERNAME"] = repo_owner
        os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token

        # Set up MLflow tracking URI
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI")

        if not tracking_uri:
            raise EnvironmentError(
                "MLFLOW_TRACKING_URI environment variable is not set"
            )

        mlflow.set_tracking_uri(tracking_uri)

        # Load model information saved during model evaluation
        model_info_path = PROJECT_ROOT / "reports" / "experiment_info.json"

        with open(model_info_path, "r") as file:
            model_info = json.load(file)

        # Load the model directly from its MLflow run artifact
        cls.new_model_uri = (
            f"runs:/{model_info['run_id']}/{model_info['model_path']}"
        )

        cls.new_model = mlflow.pyfunc.load_model(cls.new_model_uri)

        # Load the vectorizer
        vectorizer_path = PROJECT_ROOT / "models" / "vectorizer.pkl"

        with open(vectorizer_path, "rb") as file:
            cls.vectorizer = pickle.load(file)

        # Load holdout test data
        holdout_path = (
            PROJECT_ROOT / "data" / "processed" / "test_bow.csv"
        )

        cls.holdout_data = pd.read_csv(holdout_path)

    def test_model_loaded_properly(self):
        self.assertIsNotNone(self.new_model)

    def test_model_signature(self):
        # Create a dummy input for the model based on expected input shape
        input_text = "hi how are you"
        input_data = self.vectorizer.transform([input_text])

        input_df = pd.DataFrame(
            input_data.toarray(),
            columns=[str(i) for i in range(input_data.shape[1])]
        )

        # Predict using the new model to verify the input and output shapes
        prediction = self.new_model.predict(input_df)

        # Verify the input shape
        self.assertEqual(
            input_df.shape[1],
            len(self.vectorizer.get_feature_names_out())
        )

        # Verify the output shape
        self.assertEqual(len(prediction), input_df.shape[0])
        self.assertEqual(len(prediction.shape), 1)

    def test_model_performance(self):
        # Extract features and labels from holdout test data
        X_holdout = self.holdout_data.iloc[:, 0:-1]
        y_holdout = self.holdout_data.iloc[:, -1]

        # Predict using the new model
        y_pred_new = self.new_model.predict(X_holdout)

        # Calculate performance metrics for the new model
        accuracy_new = accuracy_score(y_holdout, y_pred_new)
        precision_new = precision_score(y_holdout, y_pred_new)
        recall_new = recall_score(y_holdout, y_pred_new)
        f1_new = f1_score(y_holdout, y_pred_new)

        # Define expected thresholds for the performance metrics
        expected_accuracy = 0.30
        expected_precision = 0.30
        expected_recall = 0.30
        expected_f1 = 0.30

        # Assert that the new model meets the performance thresholds
        self.assertGreaterEqual(
            accuracy_new,
            expected_accuracy,
            f'Accuracy should be at least {expected_accuracy}'
        )

        self.assertGreaterEqual(
            precision_new,
            expected_precision,
            f'Precision should be at least {expected_precision}'
        )

        self.assertGreaterEqual(
            recall_new,
            expected_recall,
            f'Recall should be at least {expected_recall}'
        )

        self.assertGreaterEqual(
            f1_new,
            expected_f1,
            f'F1 score should be at least {expected_f1}'
        )


if __name__ == "__main__":
    unittest.main()