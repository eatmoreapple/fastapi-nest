from setuptools import setup, find_packages

setup(
    name="imp",
    version="0.0.1",
    author="eatmoreapple",
    description="class base view for fastapi",
    url="https://github.com/eatmoreapple/imp",
    packages=find_packages(),
    author_email="eatmoreorange@gmail.com",
    install_requires=[
        'fastapi',
    ]
)
