# LoopStructural - QGIS Plugin

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)




## Generated options

### Plugin

| Cookiecutter option | Picked value |
| :-- | :--: |
| Plugin name | LoopStructural |
| Plugin name slugified | loopstructural |
| Plugin name class (used in code) | Loopstructural |
| Plugin category | None |
| Plugin description short | Implict 3D geological modelling in QGIS |
| Plugin description long | This plugin provides an interface to LoopStructural a 3D geological modelling library. |
| Plugin tags | geology,structural geology,3D geology,mining |
| Plugin icon | default_icon.png |
| Plugin with processing provider | False |
| Author name | Lachlan GROSE |
| Author organization | Company |
| Author email | lachlan.grose@monash.edu |
| Minimum QGIS version | 3.28 |
| Maximum QGIS version | 3.99 |
| Git repository URL | https://github.com/Loop3d/loopstructural-qgis/ |
| Git default branch | main |
| License | GPLv2+ |
| Python linter | None |
| CI/CD platform | GitHub |
| IDE | VSCode |

### Tooling

This project is configured with the following tools:

- [Black](https://black.readthedocs.io/en/stable/) to format the code without any existential question
- [iSort](https://pycqa.github.io/isort/) to sort the Python imports

Code rules are enforced with [pre-commit](https://pre-commit.com/) hooks.

See also: [contribution guidelines](CONTRIBUTING.md).

## CI/CD

Plugin is linted, tested, packaged and published with GitHub.

If you mean to deploy it to the [official QGIS plugins repository](https://plugins.qgis.org/), remember to set your OSGeo credentials (`OSGEO_USER_NAME` and `OSGEO_USER_PASSWORD`) as environment variables in your CI/CD tool. 


### Documentation

The documentation is generated using Sphinx and is automatically generated through the CI and published on Pages.

- homepage: <https://github.com/Loop3d/loopstructural-qgis/>
- repository: <https://github.com/Loop3d/loopstructural-qgis/>
- tracker: <https://github.com/Loop3d/loopstructural-qgis//issues/>

----

## Next steps

### Set up development environment

> Typical commands on Linux (Ubuntu).

1. If you don't pick the `git init` option, initialize your local repository:

    ```sh
    git init
    ```

1. Follow the [embedded documentation to set up your development environment](./docs/development/environment.md)
1. Add all files to git index to prepare initial commit:

    ```sh
    git add -A
    ```

1. Run the git hooks to ensure that everything runs OK and to start developing on quality standards:

    ```sh
    pre-commit run -a
    ```

### Try to build documentation locally

1. Have a look to the [plugin's metadata.txt file](loopstructural/metadata.txt): review it, complete it or fix it if needed (URLs, etc.).
1. Follow the [embedded documentation to build plugin documentation locally](./docs/development/environment.md)

----

## License

Distributed under the terms of the [`GPLv2+` license](LICENSE).
