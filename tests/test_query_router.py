import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    Evidence,
    EvidenceArchive,
    EvidenceStore,
    Modality,
    PerceptualQuery,
    QueryDecisionKind,
    QueryRouter,
    QueryScope,
    WorldState,
)


class QueryRouterTests(unittest.TestCase):
    def test_current_query_uses_state_then_requests_refresh_when_missing(self):
        world = WorldState(EvidenceStore())
        router = QueryRouter(world)
        q = PerceptualQuery(("browser.url",), QueryScope.CURRENT)
        self.assertEqual(
            router.route(q).kind,
            QueryDecisionKind.REFRESH_CURRENT,
        )
        world.revise(
            Evidence(
                "browser.url",
                "https://a",
                Modality.STRUCTURED,
                "b",
                0.99,
                0.1,
            )
        )
        self.assertEqual(
            router.route(q).kind,
            QueryDecisionKind.ANSWER_FROM_STATE,
        )

    def test_historical_query_routes_to_revisit_when_asset_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            world = WorldState(EvidenceStore())
            archive = EvidenceArchive(tmp)
            asset = archive.store_asset(b"x", extension=".png")
            ev = Evidence(
                "warning.level",
                "high",
                Modality.VISION,
                "v",
                0.9,
                1.0,
                pointer=str(asset),
            )
            world.revise(ev)
            archive.record(ev, asset_path=asset)
            router = QueryRouter(world, archive=archive)
            q = PerceptualQuery(("warning.level",), QueryScope.HISTORICAL)
            self.assertEqual(
                router.route(q).kind,
                QueryDecisionKind.HISTORICAL_REVISIT,
            )


if __name__ == "__main__":
    unittest.main()
