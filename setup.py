from setuptools import find_packages, setup



setup(
    name='eTracker',
    version='0.1',
    packages=find_packages(),
    include_package_date=True,
    zip_safe=False,
    install_requires=[
        'flask',],
)
