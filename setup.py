import setuptools

with open("README.md", "r")as f:
    long_description = f.read()

setuptools.setup(
    name="pyscrapetrain",
    version="0.1",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Tim Morriss",
    url="https://github.com/tim-morriss/pyscrapeTrain",
    description="CLI for downloading TrakTrain tracks",
    packages=['pyscrapetrain'],
    license="MIT",
    install_requires=[
        'setuptools',
        'beautifulsoup4',
        'mutagen',
        'requests',
        'tqdm',
        'simple-chalk',
        'halo'
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'pyscrapetrain=pyscrapetrain.pyscrapetrain:run'
        ]
    }
)
