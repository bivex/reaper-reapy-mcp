from setuptools import setup, find_packages

setup(
    name="reaper_api_usage",
    version="0.1",
    packages=find_packages(),
    test_suite="tests",
    install_requires=[
        # Add your dependencies here
    ],
    tests_require=[
        "pytest",
    ],
)
