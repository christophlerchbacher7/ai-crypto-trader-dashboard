import unittest
from datetime import datetime,timezone
from scripts.update_public_markets import parse_ticker,build_snapshot,PAIRS

class PublicMarketSafetyTests(unittest.TestCase):
    def test_only_public_data_is_exported(self):
        payload={"error":[],"result":{"XXBTZEUR":{"c":["60000"],"b":["59999"],"a":["60001"]}}}
        d=build_snapshot(lambda pair:payload,datetime(2026,11,11,tzinfo=timezone.utc))
        self.assertEqual(set(d),{"source","as_of","account_data","execution_enabled","markets"})
        self.assertFalse(d["account_data"])
        self.assertFalse(d["execution_enabled"])
        self.assertEqual([x["symbol"] for x in d["markets"]],list(PAIRS))
    def test_fail_closed_on_missing_or_bad_quotes(self):
        for row in ({"error":["Fail"],"result":{}},
                    {"error":[],"result":{}},
                    {"error":[],"result":{"X":{"a":["2"],"b":["3"],"c":["2"]}}},
                    {"error":[],"result":{"X":{"a":["2"],"b":["1"],"c":["NaN"]}}}):
            with self.assertRaises((ValueError,TypeError)):parse_ticker(row,"BTC")

if __name__=="__main__":
    unittest.main()
