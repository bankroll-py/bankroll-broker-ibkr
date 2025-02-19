from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="bankroll-broker-ibkr",
    version="0.4.0",
    author="Justin Spahr-Summers",
    author_email="justin@jspahrsummers.com",
    description="Interactive Brokers support for bankroll",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/bankroll-py/bankroll-broker-ibkr",
    packages=["bankroll.brokers.ibkr"],
    package_data={"bankroll.brokers.ibkr": ["py.typed"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3",
        "Topic :: Office/Business :: Financial :: Investment",
        "Typing :: Typed",
    ],
    install_requires=[
        "backoff ~= 1.8",
        "bankroll_broker ~= 0.4.0",
        "bankroll_marketdata ~= 0.4.0",
        "bankroll_model ~= 0.4.0",
        "ib-insync ~= 0.9.50",
        "pandas ~= 0.25.1",
        "progress ~= 1.5",
    ],
    keywords="trading investing finance portfolio ib ibkr tws",
)

