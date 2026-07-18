import pytest
from ml.training.evaluate import evaluate_trained_model

@pytest.mark.anyio
async def test_evaluation_pipeline_execution():
    # Verify that the evaluation pipeline runs successfully without raising exceptions
    # even when there are no checkpoints or databases are empty (graceful fallback)
    try:
        await evaluate_trained_model()
    except Exception as e:
        pytest.fail(f"Evaluation pipeline failed with exception: {e}")
