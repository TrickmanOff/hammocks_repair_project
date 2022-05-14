from setuptools import setup

setup(name='hammocks_repair',
      url='https://github.com/TrickmanOff/hammocks_repair_project',
      version='0.0.1',
      py_modules=['hammocks_repair'],
      packages=['hammocks_repair',
                'hammocks_repair.conformance_analysis',
                'hammocks_repair.hammocks_covering', 'hammocks_repair.hammocks_covering.variants',
                'hammocks_repair.net_repair', 'hammocks_repair.net_repair.hammocks_replacement',
                'hammocks_repair.net_repair.naive_log_only', 'hammocks_repair.utils'],
      install_requires=['pm4py'],
)
