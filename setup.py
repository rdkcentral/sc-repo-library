import setuptools

def read_version():
    with open("VERSION", "r") as f:
        return f.read().strip()

setuptools.setup(
    name="repo_library",
    version=read_version(),
    author="Bobi Martens",
    author_email="bobi.martens@sky.uk",
    description="This library provides interface to Google's repo tool.",
    packages=setuptools.find_packages(),
    install_requires=[
        'gitpython>=3',
    ]
)