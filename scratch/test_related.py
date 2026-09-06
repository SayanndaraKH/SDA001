# -*- coding: utf-8 -*-
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("app"))

import server

def test_related():
    # Test for the movie in user's screenshot: 超级雇佣兵荒岛求生
    res = server.dl_related(title="超级雇佣兵荒岛求生", limit=15)
    print("Test 1: 超级雇佣兵荒岛求生")
    print(f"  Total related dramas returned: {res.get('total')}")
    assert res.get("total") >= 10, f"Expected at least 10 related dramas, got {res.get('total')}"
    for i, item in enumerate(res.get("results", []), 1):
        print(f"  {i}. {item.get('title')} -> {item.get('title_km')} [{item.get('match_label')}] (Episodes: {item.get('episode_cnt')})")

    # Test 2: Actor match
    res2 = server.dl_related(actor="马秋元", limit=15)
    print("\nTest 2: Actor '马秋元'")
    print(f"  Total related dramas returned: {res2.get('total')}")
    assert res2.get("total") >= 10, f"Expected at least 10, got {res2.get('total')}"

    print("\n>>> RELATED DRAMAS TESTS PASSED! <<<")

if __name__ == "__main__":
    test_related()
