from setuptools import setup, find_packages

setup(
    name='roadroute-lib',
    version='0.1.1',
    packages=find_packages(),
    install_requires=[
        'shapely',  # Add other dependencies here
    ],
    author='Raven van Ewijk',
    author_email='ravenvanewijk1@gmail.com',
    description='A library for computing road routes using taxicab distance.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/roadroute-lib',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
