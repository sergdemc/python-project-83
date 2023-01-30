### Hexlet tests, linter status and status CI:
[![Actions Status](https://github.com/sergdemc/python-project-83/workflows/hexlet-check/badge.svg)](https://github.com/sergdemc/python-project-83/actions)  [![page_analyzer_ci](https://github.com/sergdemc/python-project-83/actions/workflows/page_analyzer_ci.yml/badge.svg)](https://github.com/sergdemc/python-project-83/actions/workflows/page_analyzer_ci.yml)  [![Maintainability](https://api.codeclimate.com/v1/badges/78e109af2178ca20c04e/maintainability)](https://codeclimate.com/github/sergdemc/python-project-83/maintainability)

---

## Page Analyzer
Page Analyzer is a full-featured application based on the Flask framework that analyzes specified pages for SEO suitability. Makes HTTP GET request to certain URL, shows status code and content of next tags:
* h1
* title
* meta name="description" content="..."

---

## Installation

### Prerequisites

#### Python

Before installing the package make sure you have Python version 3.8 or higher installed:

```bash
>> python --version
Python 3.8+
```

#### Poetry

The project uses the Poetry dependency manager. To install Poetry use its [official instruction](https://python-poetry.org/docs/#installation).

#### PostgreSQL

As database the PostgreSQL database system is being used. You need to install it first. You can download the ready-to-use package from [official website](https://www.postgresql.org/download/) or use Homebrew:
```shell
>> brew install postgresql
```

### Application

To use the application, you need to clone the repository to your computer. This is done using the `git clone` command. Clone the project:

```bash
>> git clone https://github.com/sergdemc/python-project-83.git && cd python-project-83
```

Then you have to install all necessary dependencies:

```bash
>> make install
```

Create .env file in the root folder and add following variables:
```
DATABASE_URL = postgresql://{provider}://{user}:{password}@{host}:{port}/{db}
SECRET_KEY = '{your secret key}'
```
Run commands from `database.sql` to create the required tables.

---

## Usage

Start the gunicorn Flask server by running:
```bash
make start
```
By default, the server will be available at http://0.0.0.0:8000. 

_It is also possible to start it local in development mode with debugger active using:_
```bash
make dev
```
_The dev server will be at http://127.0.0.1:5000._


To add a new site, enter its address into the form on the home page. The specified address will be validated and then added to the database.

After the site is added, you can start checking it. A button appears on the page of a particular site, and clicking on it creates an entry in the validation table.

You can see all added URLs on the `/urls` page.
https://python-project-83-production-0eb9.up.railway.app