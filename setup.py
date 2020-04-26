import setuptools

import tornado_restful

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tornado-restful",
    version=tornado_restful.__version__,
    author="245967906",
    author_email="245967906@qq.com",
    description="Tornado REST framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/245967906/tornado-restful",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "aiomysql>=0.0.20",
        "inflection>=0.4.0",
        "marshmallow>=3.5.1",
        "passlib>=1.7.2",
        "peewee>=3.13.2",
        "peewee-async>=0.6.0a0",
        "pycrypto>=2.6.1",
        "pyjwt>=1.7.1",
        "tornado>=6.0.4",
    ],
)
