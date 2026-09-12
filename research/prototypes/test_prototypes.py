import unittest
from itertools import combinations
import numpy as np
from research.prototypes.sparse_epistasis_tensor import SparseEpistasisTensor, BayesianRidge
from research.prototypes.voi_acquisition import select_batch
from research.prototypes.run_offline_backtest import Oracle, campaign


class ProjectionTests(unittest.TestCase):
    def test_distinct_site_formula_and_cold_zero(self):
        enc=SparseEpistasisTensor(reference='AAAA',rank=4,degree=4)
        seq=['AAAA','CAAA','CCAA','CCCA','CCCC']; x=enc.transform(seq)
        for row,s in enumerate(seq):
            z=[enc.factors[i,enc.alternatives[i].index('C')] for i,a in enumerate(s) if a=='C']
            for k in (2,3,4):
                expected=sum((np.prod(c,axis=0) for c in combinations(z,k)),start=np.zeros(4))/2
                np.testing.assert_allclose(x[row,enc.epi_start+(k-2)*4:enc.epi_start+(k-1)*4],expected)
        np.testing.assert_array_equal(x[:3,enc.epi_start+4:],0)

    def test_ridge_fit_and_unidentified_prior(self):
        enc=SparseEpistasisTensor(reference='AAA',rank=4,degree=3)
        x=enc.transform(['AAA','CAA','ACA','AAC','CCA','CAC','ACC'])
        y=np.arange(7.)
        model=BayesianRidge().fit(x,y)
        np.testing.assert_allclose(model.coef,np.linalg.solve(x.T@x+10*np.eye(x.shape[1]),x.T@y),atol=1e-12)
        np.testing.assert_array_equal(model.coef[-4:],0)
        np.testing.assert_allclose(np.diag(model.covariance)[-4:],.1)
        pred,var=model.predict(enc.transform(['CCC']))
        self.assertTrue(np.isfinite(pred).all() and (var>0).all())


class AcquisitionTests(unittest.TestCase):
    def test_degenerate_greedy(self):
        x=np.eye(4); mean=np.array([1.,3.,3.,2.])
        for cov,weights,remaining in [(x,(0,0),3),(x,(2,2),1),(x*0,(2,2),3)]:
            picks,_=select_batch(mean,x,cov,3,information_weight=weights[0],epistasis_weight=weights[1],remaining_rounds=remaining,total_rounds=3)
            np.testing.assert_array_equal(picks,[1,2,3])

    def test_exact_batch_information_and_trace(self):
        x=np.array([[1.,0.],[1.,0.],[0.,1.]])
        cov=np.eye(2)
        picks,stats=select_batch(np.zeros(3),x,cov,2,information_weight=1,epistasis_weight=1,epi_start=1,remaining_rounds=2,total_rounds=2)
        self.assertEqual(set(picks),{0,2})
        post=np.linalg.inv(np.eye(2)+x[picks].T@x[picks])
        self.assertAlmostEqual(stats['information_nats'],.5*np.linalg.slogdet(np.eye(2)+x[picks]@x[picks].T)[1])
        self.assertAlmostEqual(stats['epistasis_trace_reduction'],cov[1,1]-post[1,1])

    def test_reject_invalid(self):
        with self.assertRaises(ValueError): select_batch([1],np.eye(1),-np.eye(1),1)
        with self.assertRaises(ValueError): select_batch([1],np.eye(1),np.eye(1),2)

    def test_oracle_and_no_first_batch_label_leakage(self):
        x=np.column_stack([np.ones(20),np.arange(20)/20])
        initial=np.arange(5); candidates=np.arange(5,20)
        initial_y=np.arange(5.)
        outcomes=[]
        for future in (np.zeros(15),np.ones(15)*999):
            oracle=Oracle(np.r_[initial_y,future],initial)
            out=campaign(x,initial_y,initial,candidates,oracle,'voi_full',3,2,1,3.)
            outcomes.append(out)
            self.assertEqual(oracle.spent,6)
            self.assertEqual(len(set(out['queried_ids'])),6)
            with self.assertRaises(ValueError): oracle.query(out['queried_ids'][:1])
            with self.assertRaises(ValueError): oracle.query([19,19])
        self.assertEqual(outcomes[0]['trajectory'][0]['ids'],outcomes[1]['trajectory'][0]['ids'])
        self.assertEqual(outcomes[0]['trajectory'][0]['predictions'],outcomes[1]['trajectory'][0]['predictions'])

if __name__ == '__main__': unittest.main()
