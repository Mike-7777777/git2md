"""
Git2MD - GitHub Repository Content Aggregator
"""
import os
from setuptools import setup, find_packages

# 读取README文件
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取requirements文件
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="git2md",
    version="1.0.0",
    author="Git2MD Contributors",
    author_email="your-email@example.com",
    description="将GitHub仓库的代码文件聚合导出为单个文件",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/git2md",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.12.0",
            "isort>=5.13.2",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            "pre-commit>=3.6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "git2md=app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["templates/*", "static/css/*", "static/js/*"],
    },
    zip_safe=False,
    keywords="github repository code aggregator markdown export",
) 