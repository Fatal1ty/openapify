#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name="openapify",
    version="0.3.1",
    description=(
        "Framework agnostic OpenAPI Specification generation for code lovers"
    ),
    long_description=open("README.md", encoding="utf8").read(),
    long_description_content_type="text/markdown",
    platforms="all",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Development Status :: 3 - Alpha",
    ],
    license="Apache License, Version 2.0",
    author="Alexander Tikhonov",
    author_email="random.gauss@gmail.com",
    packages=find_packages(include=("openapify", "openapify.*")),
    package_data={"openapify": ["py.typed"]},
    python_requires=">=3.7",
    install_requires=[
        "apispec",
        "mashumaro>=3.6",
    ],
    extras_require={
        "aiohttp": ["aiohttp"],
    },
    zip_safe=False,
)
