import unittest
from valuation import dcf, analyze
class Tests(unittest.TestCase):
    def test_flat(self): self.assertAlmostEqual(dcf(10,0,.1,0),100)
    def test_invalid(self): self.assertIsNone(dcf(-1,.03,.12,.02))
    def test_reverse(self):
        a=analyze(dict(price=dcf(5,.03,.12,.02),fcf=5,eps=4,book=10)); self.assertAlmostEqual(a['reverse'],.03)
    def test_bank(self): self.assertIsNone(analyze(dict(price=10,fcf=5,sector='Financial Services'))['fair'])
if __name__=='__main__': unittest.main()
