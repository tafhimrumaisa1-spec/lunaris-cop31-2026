"""Unit tests rely exclusively on declared synthetic fixtures; no claimed NASA values."""
import unittest
from datetime import date, timedelta
from dubai_heat_case import process, build_url

class PipelineTest(unittest.TestCase):
    def fixture(self, drop=None):
        start=date(2024,1,1); end=date(2025,12,31)
        cols={x:{} for x in ('T2M','T2M_MAX','RH2M')}
        d=start
        while d<=end:
            k=d.strftime('%Y%m%d')
            for name,v in [('T2M',31.0),('T2M_MAX',40.0 if d.year==2024 else 41.0),('RH2M',55.0)]:
                cols[name][k]=-999 if drop==k else v
            d+=timedelta(days=1)
        return {'properties':{'parameter':cols}}
    def test_reproducible_scores_on_synthetic_fixture(self):
        res=process(self.fixture())
        self.assertEqual(res['periods']['observed_days'],731)
        self.assertEqual(res['evaluation']['persistence_mae_c'],0)
        self.assertEqual(res['evaluation']['prior_year_mae_c'],1)
        self.assertEqual(res['periods']['reference_summer_mean_max_c'],40)
        self.assertEqual(res['periods']['test_summer_mean_max_c'],41)
    def test_missing_record_not_mistaken_for_value(self):
        res=process(self.fixture('20240701'))
        self.assertEqual(res['periods']['missing_days'],1)
    def test_api_location_and_time_standard(self):
        url=build_url()
        self.assertIn('55.2962',url)
        self.assertIn('time-standard=UTC',url)
if __name__=='__main__':unittest.main()
