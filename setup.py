#!/usr/bin/env python3
"""Setup script for DWIN HMI Converter package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="servo-hmi-dwin",
    version="1.0.0",
    author="ServoHMI Team",
    description="Convert HTML HMI designs to DWIN DGUS-compatible BMP images",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/servoHMI_dwin",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Manufacturing",
        "Topic :: Software Development :: Embedded Systems",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "dwin-convert=scripts.convert:main",
        ],
    },
)
