import setuptools

with open("README.md", "r") as long_desc_file:
    long_description = long_desc_file.read()

setuptools.setup(
    name="improver",
    version="0.13.0",
    author="UK Met Office",
    author_email="ben.fitzpatrick@metoffice.gov.uk",
    description="Integrated Mdel post PROcessing and VERification",
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
    install_requires=["scitools-iris>=2.2", "clize>=4.1.0", "sphinx", "scitools-pyke"],
    extras_require={
        "dev": ["pytest>=5.0", "black==19.10b0", "isort==4.3.21", "pylint==2.4.4"]
    },
    scripts=["bin/improver"],
)
