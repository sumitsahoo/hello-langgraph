# Hello LangGraph

This repository contains proof-of-concept (POC) notebooks demonstrating the use of [LangGraph](https://github.com/langchain-ai/langgraph) for building simple agent workflows in Python.

## Overview

LangGraph is a library for constructing stateful, composable, and extensible agent graphs. It allows you to define nodes (functions) and connect them to form complex workflows, making it easy to build and experiment with agent-based systems.

## Notebooks

- `hello_langgraph_1.ipynb`: Demonstrates a simple greeting agent using LangGraph.
- `hello_langgraph_2.ipynb`: Shows a basic calculator agent that performs arithmetic operations using a state graph.

## Libraries Used

- **langgraph**: For building and compiling agent graphs.
- **ipykernel**: For running Jupyter notebooks interactively.
- **Python 3.11+**: Required for compatibility with LangGraph and type annotations.

## Dependency Management

This project uses [Poetry](https://python-poetry.org/) for dependency management and packaging. Poetry ensures reproducible environments and easy management of dependencies.

### Installing Dependencies

1. Install Poetry if you haven't already:
   ```sh
   curl -sSL https://install.python-poetry.org | python3 -
   ```
2. Install project dependencies:
   ```sh
   poetry install
   ```

### Activating the Environment

To activate the virtual environment created by Poetry:
```sh
poetry shell
```

## Running the Notebooks

1. Launch Jupyter Lab or Notebook:
   ```sh
   poetry run jupyter lab
   # or
   poetry run jupyter notebook
   ```
2. Open the desired notebook and run the cells.

## License

This project is licensed under the MIT License.
