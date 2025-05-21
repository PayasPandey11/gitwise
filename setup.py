from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="gitwise",
    version="0.1.0",  # Update as needed
    description="AI-powered Git workflow assistant for fast, smart commits, PRs, and changelogs.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Payas Pandey",
    author_email="rpayaspandey@gmail.com",
    url="https://github.com/PayasPandey11/gitwise",
    project_urls={
        "Source": "https://github.com/PayasPandey11/gitwise",
        "Documentation": "https://github.com/PayasPandey11/gitwise/blob/main/README.md",
        "Issues": "https://github.com/PayasPandey11/gitwise/issues",
    },
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Utilities",
    ],
    packages=find_packages(exclude=["tests*", ".internal*", ".venv*", "docs*", "examples*"]),
    python_requires=">=3.8",
    install_requires=[
        "GitPython>=3.1.0",
        "transformers>=4.36.0",
        "torch>=2.0.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "flake8",
            "black",
            "isort",
            "mypy",
        ],
        "ollama": [
            "requests>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gitwise=gitwise.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        # Add non-Python files if needed
    },
    zip_safe=False,
)

# Minimal post-install message for user
if os.environ.get("GITWISE_SETUP_MESSAGE", "1") == "1":
    print("\n[gitwise] By default, GitWise uses Ollama as the LLM backend. If you want to override this, set GITWISE_LLM_BACKEND=offline or online. See README for details.\n") 