# openapify

###### OpenAPI Specification generation for code lovers

[![Latest Version](https://img.shields.io/pypi/v/openapify.svg)](https://pypi.python.org/pypi/openapify)
[![Python Version](https://img.shields.io/pypi/pyversions/openapify.svg)](https://pypi.python.org/pypi/openapify)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

---

This library is designed for code-first people who don't want to bother diving
into the details
of [OpenAPI Specification](https://spec.openapis.org/oas/v3.1.0), but who
instead want to use advantages of Python typing system, IDE code-completion and
static type checkers to continuously build the API documentation and keep it
always up to date.

Openapify is based on the idea of applying decorators on route handlers. Any
web-framework has a routing system that let you link a route to a handler
(a high-level function or a class method). By using decorators, you can add
information about requests, responses and other details that will then be used
to create an entire OpenAPI document.

> **Warning**
>
> This library is currently in pre-release stage and may have backward
> incompatible changes prior to version 1.0. Please use caution when using this
> library in production environments and be sure to thoroughly test any updates
> before upgrading to a new version.

Table of contents
--------------------------------------------------------------------------------

* [Installation](#installation)
* [Quickstart](#quickstart)
* [Integration with web-frameworks](#integration-with-web-frameworks)
    * aiohttp
    * Writing your own integration
* [Entity schema builders](#entity-schema-builders)
    * dataclasses
    * Writing your own integration

Installation
--------------------------------------------------------------------------------

Use pip to install:

```shell
$ pip install openapify
```

Quickstart
--------------------------------------------------------------------------------

> **Note**
>
> In the following example, we will intentionally demonstrate the process of
> creating an OpenAPI document without being tied to a specific web-framework.
> However, this process may be easier on a supported web-framework.
> See [Integration with web-frameworks](#integration-with-web-frameworks) for
> more info.

Let's see how to build an OpenAPI document with openapify. Suppose we are
writing an app for a bookstore that return a book by title. Here we have a
dataclass model `Book` that would be used as a response model in a real-life
scenario. A function `get_book` is our handler.

```python
from dataclasses import dataclass

@dataclass
class Book:
    title: str
    author: str
    year: int

def get_book(...):
    ...
```

Now we want to say that our handler returns a json serialized book found by
the `title` parameter. We use `request_schema` and `response_schema` decorators
accordingly:

```python
from openapify import request_schema, response_schema

@request_schema(query_params={"title": str})
@response_schema(Book)
def get_book(...):
    ...
```

And now we need to collect all the route definitions and pass them to the
`build_spec` function. This function returns an object that has `to_yaml`
method.

```python
from openapify import build_spec
from openapify.core.models import RouteDef

routes = [RouteDef("/book", "get", get_book)]
spec = build_spec(routes)
print(spec.to_yaml())
```

As a result, we will get the following OpenAPI document which can be rendered
using tools such as Swagger UI:

```yaml
paths:
  /book:
    get:
      parameters:
      - name: title
        in: query
        required: true
        schema:
          type: string
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Book'
info:
  title: API
  version: 1.0.0
openapi: 3.1.0
components:
  schemas:
    Book:
      type: object
      title: Book
      properties:
        title:
          type: string
        author:
          type: string
      additionalProperties: false
      required:
      - title
      - author
```

Integration with web-frameworks
--------------------------------------------------------------------------------

Entity schema builders
--------------------------------------------------------------------------------
