"""Python package installation"""

from pathlib import Path

import setuptools

def main():
    with open(Path(__file__).parent / "README.md", "r") as long_desc_file:
        long_description = long_desc_file.read()

    setuptools.setup(
        name="improver",
        use_scm_version=True,
        setup_requires=["setuptools_scm"],
        author="UK Met Office",
        author_email="ben.fitzpatrick@metoffice.gov.uk",
        description="Integrated Model post PROcessing and VERification",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/metoppv/improver",
        packages=setuptools.find_packages(),
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: BSD License",
            "Operating System :: OS Independent",
        ],
        python_requires=">=3.6",
        install_requires=[
            "scitools-iris==2.2",
            "clize",
            "sphinx",
            "scitools-pyke",
            "cftime==1.0.1",
            "numpy",
            "six",
            "stratify",
        ],
        extras_require={
            "dev": [
                "pytest",
                "black==19.10b0",
                "isort==4.3.21",
                "pylint==2.4.4",
                "bandit",
                "safety",
                "filelock",
                "mock",
            ],
            "full": ["pysteps"],
        },
        scripts=["bin/improver"],
    )

if __name__ == '__main__':
    main()