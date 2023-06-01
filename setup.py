
from setuptools import setup

repo_name = 'liteobj'

__version__ = None
with open(f"{repo_name}/__init__.py", "r") as f:
    version_statement = f.readline()

exec(version_statement)

requirements_fn = "requirements.txt"
install_requirements = open(f"{repo_name}/{requirements_fn}").read().split()

setup(
      name=repo_name,
      version=__version__,
      description='Create lightweight configs for instantiating ML experiments',
      author='1lint',
      author_email='105617163+1lint@users.noreply.github.com',
      url=f'https://github.com/1lint/{repo_name}', 
      install_requires=install_requirements,
      packages=[repo_name],
      package_data={repo_name: [requirements_fn]},
      entry_points={
            'console_scripts': [
                  "lite = liteobj:main"
            ]
      },
)

