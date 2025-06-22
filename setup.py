# setup.py

from setuptools import setup, find_packages

setup(
    name="hikvision-analyzer",
    version="2.1.0",
    author="Pedro Aglailton",
    author_email="pedroaglailton@gmail.com",
    description="Módulo para análise de configurações de streaming em câmeras Hikvision",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/pedroaglailton/hikvision-analyzer",  # (opcional)
    packages=find_packages(),
    install_requires=[
        "requests",
        "pandas",
        "pillow",
        "openpyxl",
        "xmltodict",  
        "streamlit",  
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    keywords="hikvision camera streaming analyzer",
    include_package_data=True,
)