from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define a list for extra dependencies, e.g., for local LLM support
extras_require = {
    'local_llm': ["transformers", "torch", "accelerate"], # accelerate is often useful with transformers
}

setup(
    name="gitwise",
    version="0.1.0", # Consider incrementing if significant changes are made
    author="Payas Pandey",
    author_email="rpayaspandey@gmail.com",
    description="An AI-powered Git command-line assistant to streamline your workflow.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PayasPandey11/gitwise",
    packages=find_packages(exclude=["tests", "tests.*"]), # Exclude tests from package
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
        "Programming Language :: Python :: 3.12", # Add 3.12 if tested
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "typer[all]>=0.9.0", # Specify a minimum version for Typer if new features are used
        "openai>=1.0.0",    # For OpenRouter/OpenAI API compatibility
        "rich>=13.0.0",     # For the UI components
        "GitPython>=3.1.0", # If GitPython is still to be used for some features
        # "transformers", # Moved to extras_require['local_llm']
        # "torch",        # Moved to extras_require['local_llm']
    ],
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "gitwise=gitwise.cli:main", # Corrected: points to main() in gitwise/cli/__init__.py
        ],
    },
    license="MIT",
    project_urls={
        "Bug Reports": "https://github.com/PayasPandey11/gitwise/issues",
        "Source": "https://github.com/PayasPandey11/gitwise",
        "Documentation": "https://github.com/PayasPandey11/gitwise/blob/main/README.md", # Added
    },
) 