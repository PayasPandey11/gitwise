from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gitwise",
    version="0.1.0",
    author="Payas Pandey",
    author_email="rpayaspandey@gmail.com",
    description="An AI-powered Git command-line assistant to streamline your workflow.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PayasPandey11/gitwise",
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,  # Ensures non-Python files are included if present
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Utilities",
        "Environment :: Console",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "typer[all]>=0.9.0",
        "openai>=1.0.0",
        "rich>=13.0.0",
        "GitPython>=3.1.0",
        "transformers>=4.36.0",
        "torch>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "gitwise=gitwise.cli:main",
        ],
    },
    license="MIT",
    project_urls={
        "Bug Reports": "https://github.com/PayasPandey11/gitwise/issues",
        "Source": "https://github.com/PayasPandey11/gitwise",
        "Documentation": "https://github.com/PayasPandey11/gitwise/blob/main/README.md",
    },
) 