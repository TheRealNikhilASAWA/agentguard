from pathlib import Path
import pytest
from agentguard.policy import load_policy


@pytest.fixture(scope="session")
def policy():
    return load_policy(Path(__file__).parents[1] / "policy" / "default.yaml")
