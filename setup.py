from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gitwise",
    version="0.1.0",
    author="Payas",
    author_email="",  # Add your email if you want
    description="AI-powered git assistant for generating smart commit messages, PR descriptions, and changelogs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gitwise",  # Update with your repo URL
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "typer[all]",
        "transformers",
        "torch",
        "gitpython",
    ],
    entry_points={
        "console_scripts": [
            "gitwise=gitwise.cli:app",
        ],
    },
    include_package_data=True,
) 