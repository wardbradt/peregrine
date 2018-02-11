# Changelog
All notable changes to this project will be documented in this file. As this project was started for a class which requires I (wardbradt) record my daily changes, I will also daily record changes which may not be "notable."

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/).
## [0.2.5] - 2018-02-11
### Added
- Created ExchangeGraphBuilder
- Researched Networkx
- Did some graph theory research (mainly on k-core and multigraphs)
- Tests
### Changed
- Moved `_get_exchange` to utils
- test_build_collections.py to test_build_markets.py
## [0.2.4] - 2018-02-08
### Changed
- Continued Bellman Ford development
- Made Bellman Ford asynchronous
## [0.2.4] - 2018-02-07
### Added
- Began to implement Bellman Ford algorithm
### Changed
- readme and glossary
## [0.2.3] - 2018-02-06
### Added
- started js-dev branch
- examples/restrict_collections_with_kwargs_dict_argument.py
- glossary.md
- build_collections
- test_build_collections

### Changed
- Made it so that values of any type can be entered into kwargs instead of just `str`, `list`, and `dict` objects. Values which are not `list` or `dict` objects are treated as `str` objects previously were.

## [0.2.2] - 2018-02-06
### Added
- Empty `test_kwargs_with_dict_as_rule` method

### Changed
- Rules in async_build_markets.py to \*\*kwargs
- Updated tests to reflect this

## [0.2.1] - 2018-02-06
### Added
- outliers.py

### Changed
- Added `ccxt_errors` to several methods in async_build_markets.py
- Moved classes `SingularlyAvailableExchangeError`, `SingularlyAvailableExchangeError`, and `get_exchanges_for_market` from async_find_opportunities.py to utils.py so that they can be accessed from all files
- Added (but did not implement) `from_json` argument to `get_exchanges_for_market`

## [0.2.0] - 2018-02-05
### Added
- Cython version of code (under the /cythonperegrine directory)
- Examples directory (/examples)
- First speed comparison (in /examples)
- `calculate_time` in examples/calculate_time.py, a utility for measuring the speed of functions
- type aliases to some function declarations in peregrine/

### Removed
- Unnecessary print statement at start of async_find_opportunities.py

### Changed
- Cleaned up some doc strings
- test_bid_and_ask to _test_bid_and_ask to denote that it should not be accessed by users

## [0.1.1] - 2018-02-01
### Added
- Unit tests for async_build_markets.py in peregrine/tests/test_build_collections.py

### Changed
- Moved src files to peregrine subdirectory.

## [0.1.0] - 2018-02-01
### Added
- Initial Commit
