from setuptools import setup


setup(
    name='peregrinearb',
    version='1.1.2',
    description='A Python library which provides several algorithms to detect arbitrage opportunities across over 90 cryptocurrency markets in 34 countries',
    author='Ward Bradt',
    author_email='wardbradt5@gmail.com',
    packages=['peregrinearb', 'peregrinearb.utils', 'peregrinearb.tests'],
    license='MIT',
    url='https://github.com/wardbradt/peregrinearb',
)
