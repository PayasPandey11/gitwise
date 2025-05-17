from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gitwise",
    version="0.1.0",
    author="Payas Pandey",
    author_email="rpayaspandey@gmail.com",
    description="An AI-powered Git assistant for better commit messages and PR descriptions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PayasPandey11/gitwise",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "typer[all]",
        "transformers",
        "torch",
        "gitpython",
        "openai",
    ],
    entry_points={
        "console_scripts": [
            "gitwise=gitwise.cli:app",
        ],
    },
    license="MIT",
    project_urls={
        "Bug Reports": "https://github.com/PayasPandey11/gitwise/issues",
        "Source": "https://github.com/PayasPandey11/gitwise",
    },
) 