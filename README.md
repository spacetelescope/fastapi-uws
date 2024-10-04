# fastapi-uws

`fastapi-uws` is an open-source Python implementation of the IVOA UWS (Universal Worker Service) protocol, based on the [FastAPI](https://fastapi.tiangolo.com/) web framework.

This package is based off the prototype OpenAPI UWS specification developed as part of the 2024 IVOA Protocol Transition Tiger Team (P3T) effort. The UWS specification is still in development and may change in the future.

## Features

This package is intended to be customizable for a few use cases. Users need only implement handling classes for the UWS job and results stores, executor, and the package will handle the rest.

The package includes a complete FastAPI application, including the UWS routes and service logic. The package also includes a basic in-memory job store and executor for testing purposes.

## Installation

Until the package is published to PyPI, you can install it directly from the GitHub repository:

```bash
git clone https://github.com/spacetelescope/fastapi-uws.git
cd fastapi-uws
conda env create -f environment.yml
conda activate fastapi-uws
pip install -r requirements.txt
pip install .
```



