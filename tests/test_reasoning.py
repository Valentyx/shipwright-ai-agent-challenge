import os
import unittest
from unittest.mock import patch

from shipwright.adk_app import LocalAgentSpec, create_root_agent
from shipwright.evaluation import build_seeded_coordinator
from shipwright.reasoning import (
    DeterministicReasoningProvider,
    ReasoningRequest,
    reasoning_provider_from_env,
)

os.environ["SHIPWRIGHT_QUIET_LOGS"] = "1"


class ReasoningProviderTests(unittest.TestCase):
    def setUp(self):
        self.previous_provider = os.environ.pop("SHIPWRIGHT_REASONING_PROVIDER", None)
        self.previous_model = os.environ.pop("SHIPWRIGHT_REASONING_MODEL", None)

    def tearDown(self):
        if self.previous_provider is not None:
            os.environ["SHIPWRIGHT_REASONING_PROVIDER"] = self.previous_provider
        else:
            os.environ.pop("SHIPWRIGHT_REASONING_PROVIDER", None)
        if self.previous_model is not None:
            os.environ["SHIPWRIGHT_REASONING_MODEL"] = self.previous_model
        else:
            os.environ.pop("SHIPWRIGHT_REASONING_MODEL", None)

    def test_deterministic_provider_creates_stable_project_memory_text(self):
        provider = DeterministicReasoningProvider()

        result = provider.summarize_project_memory(
            ReasoningRequest(
                task_name="project_memory.nightly_summary",
                facts=("SHIP-100 is In Progress.", "Owner team is core-product."),
                source_ids=("SHIP-100",),
            )
        )

        self.assertEqual(result.text, "SHIP-100 is In Progress. Owner team is core-product.")
        self.assertEqual(result.provider_name, "deterministic")
        self.assertEqual(result.model_name, "deterministic-v1")
        self.assertIsNone(result.estimated_cost_usd)

    def test_memory_agent_uses_reasoning_provider_result(self):
        coordinator = build_seeded_coordinator()

        summary_id = coordinator.memory_agent.create_nightly_summary("SHIP-100")
        indexed = coordinator.memory_agent.memory.query("Known signoffs none yet", limit=10)

        self.assertEqual(summary_id, "brazil-payments-launch-nightly-memory")
        self.assertTrue(any("Known signoffs: none yet." in summary.body for summary in indexed))

    def test_env_config_defaults_to_deterministic_provider(self):
        provider = reasoning_provider_from_env()

        self.assertIsInstance(provider, DeterministicReasoningProvider)

    def test_adk_app_uses_configured_model_in_local_fallback(self):
        os.environ["SHIPWRIGHT_REASONING_MODEL"] = "gemini-test-model"

        real_import = __import__

        def block_adk_import(name, *args, **kwargs):
            if name == "google.adk.agents.llm_agent":
                raise ModuleNotFoundError(name)
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=block_adk_import):
            agent = create_root_agent()

        self.assertIsInstance(agent, LocalAgentSpec)
        self.assertEqual(agent.model, "gemini-test-model")
        self.assertTrue(agent.sub_agents)
        self.assertTrue(all(sub_agent.model == "gemini-test-model" for sub_agent in agent.sub_agents))


if __name__ == "__main__":
    unittest.main()
