import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import loomy_daily


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


def all_tasks_done(**overrides):
    done = {task[1]: True for task in loomy_daily.TASKS}
    done.update(overrides)
    return done


class FakeLoomy:
    def __init__(self, done, complete_keys=None, regress_keys=None, fail_readback_at=None):
        self.done = dict(done)
        self.complete_keys = set(complete_keys or [])
        self.regress_keys = set(regress_keys or [])
        self.fail_readback_at = fail_readback_at
        self.get_count = 0
        self.posts = []

    def _tasks_payload(self):
        return {
            "code": loomy_daily.SUCCESS_CODE,
            "data": {
                "tasks": {
                    key: bool(self.done.get(key))
                    for _group, key, _title, _points in loomy_daily.TASKS
                }
            },
        }

    def __call__(self, method, url, headers=None, body=None, timeout=20, retries=3):
        if method == "GET" and url.endswith(loomy_daily.TASKS_PATH):
            self.get_count += 1
            if self.get_count == self.fail_readback_at:
                raise RuntimeError("readback timeout")
            return FakeResponse(self._tasks_payload())
        if method == "POST" and url.endswith(loomy_daily.COMPLETE_PATH):
            key = (body or {}).get("key")
            self.posts.append(key)
            if key in self.complete_keys:
                self.done[key] = True
            for regress_key in self.regress_keys:
                self.done[regress_key] = False
            return FakeResponse({
                "code": loomy_daily.SUCCESS_CODE,
                "data": {"alreadyCompleted": False},
            })
        raise AssertionError("unexpected request: %s %s" % (method, url))


class LoomyClaimReadbackTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.state_path = Path(self.temp_dir.name) / "loomy_onboarding.json"
        self.state_patch = patch.object(loomy_daily, "STATE_FILE", str(self.state_path))
        self.state_patch.start()
        self.addCleanup(self.state_patch.stop)
        self.sleep_patch = patch.object(loomy_daily.time, "sleep", return_value=None)
        self.sleep_patch.start()
        self.addCleanup(self.sleep_patch.stop)

    def test_batch_claim_requires_readback_confirmation(self):
        key = loomy_daily.TASKS[0][1]
        points = loomy_daily.TASKS[0][3]
        remote = FakeLoomy(all_tasks_done(**{key: False}), complete_keys={key})

        with patch.object(loomy_daily, "request", side_effect=remote):
            newly, failed, payload = loomy_daily.claim_onboarding("token", refresh=True)

        self.assertEqual(remote.get_count, 2)
        self.assertEqual(remote.posts, [key])
        self.assertEqual(failed, [])
        self.assertEqual(len(newly), 1)
        self.assertEqual(payload["claimed"], 1)
        self.assertEqual(payload["claimedPoints"], points)
        self.assertEqual(payload["earnedBefore"], loomy_daily.TOTAL_POINTS - points)
        self.assertEqual(payload["earnedAfter"], loomy_daily.TOTAL_POINTS)
        self.assertEqual(payload["earnedDelta"], points)
        self.assertEqual(payload["results"][0]["status"], "confirmed")
        self.assertTrue(payload["results"][0]["ok"])
        self.assertTrue(payload["settled"])

    def test_batch_claim_without_state_change_is_pending(self):
        key = loomy_daily.TASKS[0][1]
        remote = FakeLoomy(all_tasks_done(**{key: False}))

        with patch.object(loomy_daily, "request", side_effect=remote):
            newly, failed, payload = loomy_daily.claim_onboarding("token", refresh=True)

        self.assertEqual(remote.get_count, 2)
        self.assertEqual(newly, [])
        self.assertEqual(failed, [])
        self.assertEqual(payload["claimed"], 0)
        self.assertEqual(payload["claimedPoints"], 0)
        self.assertEqual(payload["pending"], 1)
        self.assertEqual(payload["unconfirmed"], 0)
        self.assertEqual(payload["results"][0]["status"], "pending")
        self.assertFalse(payload["results"][0]["ok"])
        self.assertFalse(payload["settled"])

    def test_batch_readback_failure_is_unconfirmed_and_not_cached(self):
        key = loomy_daily.TASKS[0][1]
        remote = FakeLoomy(
            all_tasks_done(**{key: False}),
            complete_keys={key},
            fail_readback_at=2,
        )

        with patch.object(loomy_daily, "request", side_effect=remote):
            newly, failed, payload = loomy_daily.claim_onboarding("token", refresh=True)

        self.assertEqual(remote.get_count, 2)
        self.assertEqual(newly, [])
        self.assertEqual(failed, [])
        self.assertEqual(payload["claimed"], 0)
        self.assertEqual(payload["pending"], 0)
        self.assertEqual(payload["unconfirmed"], 1)
        self.assertEqual(payload["verification"], "unconfirmed")
        self.assertFalse(payload["readbackOk"])
        self.assertIsNone(payload["earnedAfter"])
        self.assertFalse(payload["settled"])
        self.assertEqual(payload["results"][0]["status"], "unconfirmed")
        self.assertFalse(os.path.exists(self.state_path))

    def test_batch_only_reports_confirmed_items_as_claimed(self):
        first_key = loomy_daily.TASKS[0][1]
        second_key = loomy_daily.TASKS[1][1]
        first_points = loomy_daily.TASKS[0][3]
        remote = FakeLoomy(
            all_tasks_done(**{first_key: False, second_key: False}),
            complete_keys={first_key},
        )

        with patch.object(loomy_daily, "request", side_effect=remote):
            newly, failed, payload = loomy_daily.claim_onboarding("token", refresh=True)

        statuses = {row["key"]: row["status"] for row in payload["results"]}
        self.assertEqual(statuses[first_key], "confirmed")
        self.assertEqual(statuses[second_key], "pending")
        self.assertEqual(payload["claimed"], 1)
        self.assertEqual(payload["pending"], 1)
        self.assertEqual(payload["claimedPoints"], first_points)
        self.assertEqual(payload["earnedDelta"], first_points)
        self.assertEqual(len(newly), 1)
        self.assertEqual(failed, [])

    def test_batch_task_state_without_earned_increment_is_unconfirmed(self):
        key = loomy_daily.TASKS[0][1]
        regressed_key = loomy_daily.TASKS[-1][1]
        remote = FakeLoomy(
            all_tasks_done(**{key: False}),
            complete_keys={key},
            regress_keys={regressed_key},
        )

        with patch.object(loomy_daily, "request", side_effect=remote):
            newly, failed, payload = loomy_daily.claim_onboarding("token", refresh=True)

        self.assertEqual(remote.get_count, 2)
        self.assertEqual(payload["claimed"], 0)
        self.assertEqual(payload["claimedPoints"], 0)
        self.assertEqual(payload["unconfirmed"], 1)
        self.assertLess(payload["earnedDelta"], loomy_daily.TASKS[0][3])
        self.assertEqual(payload["results"][0]["status"], "unconfirmed")
        self.assertTrue(payload["results"][0]["afterDone"])
        self.assertFalse(payload["results"][0]["ok"])
        self.assertEqual(newly, [])
        self.assertEqual(failed, [])

    def test_single_claim_uses_readback_result(self):
        key = loomy_daily.TASKS[0][1]
        points = loomy_daily.TASKS[0][3]
        remote = FakeLoomy(all_tasks_done(**{key: False}), complete_keys={key})

        with patch.object(loomy_daily, "request", side_effect=remote):
            payload = loomy_daily.claim_single("token", key, refresh=True)

        self.assertEqual(remote.get_count, 2)
        self.assertEqual(remote.posts, [key])
        self.assertEqual(payload["status"], "confirmed")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["claimedPoints"], points)
        self.assertEqual(payload["earnedDelta"], points)
        self.assertEqual(payload["verification"], "confirmed")


if __name__ == "__main__":
    unittest.main()
