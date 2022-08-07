from setuptools import find_packages, setup

with open("README.md") as f:
    readme = f.read()

setup(
    name="jupyterhub-roothooks",
    version="0.2",
    description="Help run hooks as root before dropping privs & running as unprivileged user",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Yuvi Panda",
    author_email="yuvipanda@gmail.com",
    packages=find_packages(),
    install_requires=[
        "traitlets",
    ],
    entry_points={
        "console_scripts": ["jupyterhub-roothooks=jupyterhub_roothooks:main"]
    },
)
