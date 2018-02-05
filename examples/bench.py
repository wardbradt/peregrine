# This file demonstrates the speed difference between the Cython and Python versions of peregrine
import pyximport
pyximport.install()
from cythonperegrine import build_specific_collections as cython_build
from cythonperegrine import OpportunityFinder as cython_finder
from peregrine import build_specific_collections as python_build
from peregrine import OpportunityFinder as python_finder
from examples.calculate_time import calculate_time


def test_cython():
    us_eth_btc_exchanges = cython_build({'countries': 'US'}, False, False)
    finder = cython_finder("ETH/BTC", us_eth_btc_exchanges["ETH/BTC"])
    finder.find_min_max()


def test_python():
    us_eth_btc_exchanges = python_build({'countries': 'US'})
    finder = python_finder("ETH/BTC", us_eth_btc_exchanges["ETH/BTC"])
    finder.find_min_max()


print("Cython speed: " + str(calculate_time(test_cython)))
print("Python speed: " + str(calculate_time(test_python)))
