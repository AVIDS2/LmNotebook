import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

# Ensure src/backend is importable when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api import chat  # noqa: E402


class ApplyModelProviderOverrideTests(unittest.IsolatedAsyncioTestCase):
    async def test_no_provider_id_skips_switch(self):
        switched = await chat.apply_model_provider_override(None)
        self.assertFalse(switched)

    async def test_unknown_provider_id_skips_switch(self):
        fake_manager = SimpleNamespace(
            get_providers=lambda: [{"id": "a"}],
            get_active_provider=lambda: {"id": "a"},
            set_active_provider=lambda _pid: (_ for _ in ()).throw(AssertionError("must not switch")),
        )
        original_manager = chat.model_manager
        chat.model_manager = fake_manager
        try:
            switched = await chat.apply_model_provider_override("missing")
            self.assertFalse(switched)
        finally:
            chat.model_manager = original_manager

    async def test_switches_when_provider_differs_and_invalidates_runtime(self):
        calls = []

        def set_active(pid: str):
            calls.append(("set_active", pid))

        fake_manager = SimpleNamespace(
            get_providers=lambda: [
                {"id": "a", "name": "A", "modelName": "m-a"},
                {"id": "b", "name": "B", "modelName": "m-b"},
            ],
            get_active_provider=lambda: {"id": "a", "name": "A", "modelName": "m-a"},
            set_active_provider=set_active,
        )

        async def fake_invalidate():
            calls.append(("invalidate", None))

        original_manager = chat.model_manager
        original_invalidate = chat.invalidate_agent_runtime_cache
        chat.model_manager = fake_manager
        chat.invalidate_agent_runtime_cache = fake_invalidate
        try:
            switched = await chat.apply_model_provider_override("b")
            self.assertTrue(switched)
            self.assertEqual(calls, [("set_active", "b"), ("invalidate", None)])
        finally:
            chat.model_manager = original_manager
            chat.invalidate_agent_runtime_cache = original_invalidate

    async def test_switches_model_within_same_provider_and_invalidates_runtime(self):
        calls = []

        def set_active_model(provider_id: str, model_name: str):
            calls.append(("set_active_model", provider_id, model_name))
            return True

        fake_manager = SimpleNamespace(
            get_providers=lambda: [
                {
                    "id": "a",
                    "name": "A",
                    "modelName": "m-a",
                    "models": ["m-a", "m-a-2"],
                    "activeModel": "m-a",
                }
            ],
            get_active_provider=lambda: {
                "id": "a",
                "name": "A",
                "modelName": "m-a",
                "models": ["m-a", "m-a-2"],
                "activeModel": "m-a",
            },
            set_active_provider=lambda _pid: calls.append(("set_active_provider", _pid)),
            set_provider_active_model=set_active_model,
        )

        async def fake_invalidate():
            calls.append(("invalidate", None))

        original_manager = chat.model_manager
        original_invalidate = chat.invalidate_agent_runtime_cache
        chat.model_manager = fake_manager
        chat.invalidate_agent_runtime_cache = fake_invalidate
        try:
            switched = await chat.apply_model_provider_override("a", "m-a-2")
            self.assertTrue(switched)
            self.assertEqual(
                calls,
                [("set_active_model", "a", "m-a-2"), ("invalidate", None)],
            )
        finally:
            chat.model_manager = original_manager
            chat.invalidate_agent_runtime_cache = original_invalidate

    async def test_ignores_unknown_model_name_within_provider(self):
        calls = []

        fake_manager = SimpleNamespace(
            get_providers=lambda: [
                {"id": "a", "name": "A", "modelName": "m-a", "models": ["m-a"], "activeModel": "m-a"}
            ],
            get_active_provider=lambda: {"id": "a", "name": "A", "modelName": "m-a", "models": ["m-a"], "activeModel": "m-a"},
            set_active_provider=lambda _pid: calls.append(("set_active_provider", _pid)),
            set_provider_active_model=lambda _pid, _model: calls.append(("set_active_model", _pid, _model)),
        )

        async def fake_invalidate():
            calls.append(("invalidate", None))

        original_manager = chat.model_manager
        original_invalidate = chat.invalidate_agent_runtime_cache
        chat.model_manager = fake_manager
        chat.invalidate_agent_runtime_cache = fake_invalidate
        try:
            switched = await chat.apply_model_provider_override("a", "missing-model")
            self.assertFalse(switched)
            self.assertEqual(calls, [])
        finally:
            chat.model_manager = original_manager
            chat.invalidate_agent_runtime_cache = original_invalidate


if __name__ == "__main__":
    unittest.main()
