from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pinterest-monitor",
    version="1.0.0",
    author="Sha-Dox",
    description="Real-time OSINT monitoring tool for Pinterest boards and user activity",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Sha-Dox/coral",
    packages=find_packages(),
    py_modules=["app", "config", "database", "monitor", "scheduler", "reset_db"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pinterest-monitor=app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["templates/*", "static/css/*", "static/js/*", "config.example.ini"],
    },
)
