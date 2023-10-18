import setuptools

with open("README.md", "r")as f:
    long_description = f.read()

setuptools.setup(
    name="pyscrapetrain",
    packages=['pyscrapetrain'],
    version="0.1.1",
    description="CLI for downloading TrakTrain tracks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Tim Morriss",
    url="https://github.com/tim-morriss/pyscrapeTrain",
    download_url="https://github.com/tim-morriss/pyscrapeTrain/archive/refs/tags/v0.1.1.tar.gz",
    license="MIT",
    keywords=['traktrain', 'scrapeTrain'],
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
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Multimedia :: Sound/Audio',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13'
    ]
)
