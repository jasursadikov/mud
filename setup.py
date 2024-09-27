from setuptools import setup, find_packages

setup(
    name='git-mud',
    version='1.0.0',
    packages=find_packages(),
    install_requires=['prettytable'],
    description='Multi repository git utility. Manage multiple git-repositories simultaneously.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/jasursadikov/mud',
    author='Your Name',
    author_email='jasur@sadikoff.com',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.12',  # Specify your Python version support
)
