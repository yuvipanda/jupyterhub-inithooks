from setuptools import find_packages, setup

with open("README.md") as f:
    readme = f.read()

setup(
    name="jupyterhub-singleuser_inithooks",
    description="Commandline tool to manage pangeo-forge feedstocks",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Yuvi Panda",
    author_email="yuvipanda@gmail.com",
    version="0.3",
    packages=find_packages(),
    install_requires=[
        "traitlets",
    ],
    entry_points={
        "console_scripts": ["jupyterhub-singleuser-inithooks=jupyterhub_singleuser_inithooks:main"]
    },
)
