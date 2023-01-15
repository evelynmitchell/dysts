"""
Test the models and regularizer
> python test_generation.py
"""
#!/usr/bin/env python
import os
import numpy as np
import unittest

WORKING_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(WORKING_DIR, 'tests', 'test_data')
print(WORKING_DIR)

import sys

sys.path.insert(1, os.path.join(WORKING_DIR, "dysts"))
from dysts.flows import Lorenz
from dysts.base import make_trajectory_ensemble


class TestModels(unittest.TestCase):
    """
    Tests integration and models
    """
    def test_trajectory(self):
        """
        Test generating a trajectory
        """
        model = Lorenz()
        sol = model.make_trajectory(100)
        assert sol.shape == (100, 3), "Generated time series has the wrong shape"
        
    def test_trajectory_noise(self):
        """
        Test generating a trajectory with stochasticity
        """
        model = Lorenz()
        sol = model.make_trajectory(100, noise=0.01)
        assert sol.shape == (100, 3), "Generated time series has the wrong shape"
        
    def test_ensemble(self):
        """
        Test all systems in the database
        """
        all_trajectories = make_trajectory_ensemble(5, method="Radau", resample=True)
        assert len(all_trajectories.keys()) >= 131

        xvals = np.array([all_trajectories[key][:, 0] for key in all_trajectories.keys()])
        xvals_reference = np.load(os.path.join(DATA_PATH, "all_trajectories.npy"), allow_pickle=True)
        diff_names = np.array(list(all_trajectories.keys()))[np.sum(np.abs(xvals - xvals_reference), axis=1) > 0]
        assert np.allclose(xvals, xvals_reference), "Generated trajectories do not match reference values for system {}".format(diff_names)

        
    def test_precomputed(self):
        """
        Test loading a precomputed time series for a single system
        """
        eq = Lorenz()
        tpts, sol = eq.load_trajectory(
            subsets="test", 
            noise=False, 
            granularity="fine", 
            standardize=True, 
            return_times=True
        )
        assert sol.shape == (1200, 3), "Generated time series has the wrong shape"
        assert tpts.shape == (1200,), "Time indices have the wrong shape"
        
        
if __name__ == "__main__":
    unittest.main()