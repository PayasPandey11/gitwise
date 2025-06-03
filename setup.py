from setuptools import setup, find_packages
import os
from setuptools.command.install import install
import sys
import sysconfig

# Read version from package
version = {}
with open(os.path.join("gitwise", "__init__.py")) as f:
    exec(f.read(), version)

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

class CustomInstallCommand(install):
    def run(self):
        install.run(self)
        user_base = sysconfig.get_config_var('userbase')
        bin_dir = os.path.join(user_base, 'bin') if user_base else None
        msg = "\n[gitwise] If you see a warning about the 'gitwise' script not being on your PATH, add the following to your shell config (replace 3.x with your Python version):\n"
        msg += "\n    export PATH=\"$PATH:/Users/$(whoami)/Library/Python/3.x/bin\"\n"
        msg += "\nOr use a virtual environment for best results. See the README for details.\n"
        print(msg)

setup(
    name="gitwise",
    version=version["__version__"],  # Use version from __init__.py
    description="AI-powered Git assistant with privacy-first design. Choose between local (Ollama/Offline) or cloud AI to automate commits, PRs, and changelogs.",
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
    keywords="git ai conventional-commits changelog pull-request automation llm ollama",
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
    packages=find_packages(
        exclude=["tests*", ".internal*", ".venv*", "docs*", "examples*"]
    ),
    python_requires=">=3.8",
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.0.0",
        "requests>=2.0.0",
        "jinja2",
        "openai>=1.0.0",
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
        "offline": [
            "transformers>=4.36.0",
            "torch>=2.0.0",
        ],
        "cloud_llms": [
            "google-generativeai>=0.3.0",
            "openai>=1.0.0",
            "anthropic>=0.20.0",
        ],
        "all_llms": [
            "transformers>=4.36.0",
            "torch>=2.0.0",
            "google-generativeai>=0.3.0",
            "anthropic>=0.20.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gitwise=gitwise.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "gitwise": ["templates/*.md"],  # Include template files
    },
    zip_safe=False,
    cmdclass={
        'install': CustomInstallCommand,
    },
)

# Minimal post-install message for user
if os.environ.get("GITWISE_SETUP_MESSAGE", "1") == "1":
    print(
        "\n[gitwise] All LLM backends (Ollama, Offline, Online) are now available! By default, GitWise uses Ollama. To change backends, run 'gitwise init' or set GITWISE_LLM_BACKEND environment variable. See README for details.\n"
    )
