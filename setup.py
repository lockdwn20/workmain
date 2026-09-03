from setuptools import setup, find_packages

setup(
    name="workmain",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'workmain=workmain.cli.interface:cli',
        ],
    },
    author="Lockdwn20",
    author_email="lockdwn20@gmail.com",
    description="Work Management AI - Intelligent personal work management system",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/lockdwn20/workmain",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)
