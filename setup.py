from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    INSTALL_REQUIRES = [line.strip() for line in f.readlines()]

setup(
    name='roadroute-lib',
    version='0.3.1',
    packages=find_packages(),
    install_requires=INSTALL_REQUIRES,
    author='Raven van Ewijk',
    author_email='ravenvanewijk1@gmail.com',
    description='A library for computing road routes using taxicab distance.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ravenvanewijk/roadroute-lib',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
