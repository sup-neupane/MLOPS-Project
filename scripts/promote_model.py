# promote model

import os
import mlflow

def promote_model():
    # Set up DagsHub credentials for MLflow tracking
    dagshub_token = os.getenv("CAPSTONE_TEST")
    repo_owner = os.getenv("DAGSHUB_REPO_OWNER")
    repo_name = os.getenv("DAGSHUB_REPO_NAME")

    if dagshub_token:
        os.environ["MLFLOW_TRACKING_USERNAME"] = repo_owner or dagshub_token
        os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token

    # Set up MLflow tracking URI
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")

    if not MLFLOW_TRACKING_URI:
        raise EnvironmentError("MLFLOW_TRACKING_URI is not set in .env")

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    client = mlflow.MlflowClient()

    model_name = "my_model"
    # Get the latest version in staging
    latest_version_staging = client.get_latest_versions(model_name, stages=["Staging"])[0].version

    # Archive the current production model
    prod_versions = client.get_latest_versions(model_name, stages=["Production"])
    for version in prod_versions:
        client.transition_model_version_stage(
            name=model_name,
            version=version.version,
            stage="Archived"
        )

    # Promote the new model to production
    client.transition_model_version_stage(
        name=model_name,
        version=latest_version_staging,
        stage="Production"
    )
    print(f"Model version {latest_version_staging} promoted to Production")

if __name__ == "__main__":
    promote_model()