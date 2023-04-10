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
* [Decorators](#decorators)
    * [Generic operation info](#generic-operation-info)
    * [Request](#request)
    * [Response](#response)
    * [Security requirements](#security-requirements)
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
writing an app for a bookstore that return a list of new books. Here we have a
dataclass model `Book` that would be used as a response model in a real-life
scenario. A function `get_new_books` is our handler.

```python
from dataclasses import dataclass

@dataclass
class Book:
    title: str
    author: str
    year: int

def get_new_books(...):
    ...
```

Now we want to say that our handler returns a json serialized list of books
limited by the optional `count` parameter. We use `request_schema`
and `response_schema` decorators accordingly:

```python
from openapify import request_schema, response_schema

@request_schema(query_params={"count": int})
@response_schema(list[Book])
def get_new_books(...):
    ...
```

And now we need to collect all the route definitions and pass them to the
`build_spec` function. This function returns an object that has `to_yaml`
method.

```python
from openapify import build_spec
from openapify.core.models import RouteDef

routes = [RouteDef("/books", "get", get_new_books)]
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
      - name: count
        in: query
        schema:
          type: integer
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
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
        year:
          type: integer
      additionalProperties: false
      required:
      - title
      - author
      - year
```

Decorators
--------------------------------------------------------------------------------

Openapify has several decorators that embed necessary specific information for
later use when building the OpenAPI document. In general, decorators will
define the information that will be included in
the [Operaion Object](https://spec.openapis.org/oas/v3.1.0#operation-object)
which describes a single API operation on a path. We will look at what each
decorator parameter is responsible for and how it is reflected in the final
document.

### Generic operation info

Decorator `path_docs` adds generic information about the Operation object,
which includes summary, description, tags, external documentation and
deprecation marker.

```python
from openapify import path_docs
```

#### summary

An optional, string summary, intended to apply to the operation. This affects
the value of
the [`summary`](https://spec.openapis.org/oas/v3.1.0#operation-object) field of
the Operation object.

| Possible types | Examples              |
|----------------|-----------------------|
| `str`          | `"Getting new books"` |

#### description

An optional, string description, intended to apply to the
operation. [CommonMark syntax](https://spec.commonmark.org) MAY be used for
rich text representation. This affects the value of
the [`description`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object.

| Possible types | Examples                    |
|----------------|-----------------------------|
| `str`          | `"Returns a list of books"` |

#### tags

A list of tags for API documentation control. Tags can be used for logical
grouping of operations by resources or any other qualifier. This affects the
value of the [`tags`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object.

| Possible types  | Examples   |
|-----------------|------------|
| `Sequence[str]` | `["book"]` |

#### external_docs

Additional external documentation for the operation. It can be a single url or
(url, description) pair. This affects the value of
the [`summary`](https://spec.openapis.org/oas/v3.1.0#operation-object) field of
the Operation object.

| Possible types    | Examples                                                                  |
|-------------------|---------------------------------------------------------------------------|
| `str`             | `"https://example.org/docs/books"`                                        |
| `Tuple[str, str]` | `("https://example.org/docs/books", "External documentation for /books")` |

#### deprecated

Declares the operation to be deprecated. Consumers SHOULD refrain from usage
of the declared operation. Default value is false. This affects the value of
the [`deprecated`](https://spec.openapis.org/oas/v3.1.0#operation-object) field
of the Operation object.

| Possible types | Examples                       |
|----------------|--------------------------------|
| `bool`         | <code lang="python">True</pre> |

### Request

Decorator `request_schema` adds information about the operation requests.
Request can have a body, query parameters, headers and cookies.

```python
from openapify import request_schema
```

#### body

A request body can be described entirely by one `body` parameter of type `Body`
or partially by separate `body_*` parameters (see below).

In the first case it is `openapify.core.models.Body` object that has all the
separate `body_*` parameters inside. This affects the value of
the [`requestBody`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object.

In the second case it is the request body Python data type for which the JSON
Schema will be built. This affects the value of
the [`requestBody`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely,
the [`schema`](https://spec.openapis.org/oas/v3.1.0#media-type-object) field of
Media Type object inside
the value
of [`content`](https://spec.openapis.org/oas/v3.1.0#request-body-object) field
of Request Body object.

<table>
<tr>
<th>Possible types</th>
<th>Examples</th>
</tr>
<tr>
<td> <code>Type</code> </td>
<td>

```python
Book
```

</td>
</tr>
<tr>
<td> <code>Body</code> </td>
<td>

```python
Body(
    value_type=Book,
    media_type="application/json",
    required=True,
    description="A book",
    example={
        "title": "Anna Karenina",
        "author": "Leo Tolstoy",
        "year": 1877,
    },
)
```

</td>
</tr>
</table>

#### media_type

A media type
or [media type range](https://www.rfc-editor.org/rfc/rfc7231#appendix-D) of the
request body. This affects the value of
the [`requestBody`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely,
the key
of [`content`](https://spec.openapis.org/oas/v3.1.0#request-body-object) field
of Request Body object.

The default value is `"application/json"`.

| Possible types | Examples            |
|----------------|---------------------|
| `str`          | `"application/xml"` |

#### body_required

Determines if the request body is required in the request. Defaults to false.
This affects the value of
the [`requestBody`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely,
the [`required`](https://spec.openapis.org/oas/v3.1.0#request-body-object)
field of Request Body object.

| Possible types | Examples |
|----------------|----------|
| `bool`         | `True`   |

#### body_description

A brief description of the request body. This could contain examples of
use. [CommonMark syntax](https://spec.commonmark.org) MAY be used for rich text
representation. This affects the value of
the [`requestBody`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely,
the [`description`](https://spec.openapis.org/oas/v3.1.0#request-body-object)
field of Request Body object.

| Possible types | Examples   |
|----------------|------------|
| `str`          | `"A book"` |

#### body_example

Example of the request body. The example object SHOULD be in the correct format
as specified by the media type. This affects the value of
the [`requestBody`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely,
the [`example`](https://spec.openapis.org/oas/v3.1.0#media-type-object) field
of
Media Type object inside
the value
of [`content`](https://spec.openapis.org/oas/v3.1.0#request-body-object) field
of Request Body object.

<table>
<tr>
<th>Possible types</th>
<th>Examples</th>
</tr>
<tr>
<td> <code>Any</code> </td>
<td>

```python
{
    "title": "Anna Karenina",
    "author": "Leo Tolstoy",
    "year": 1877,
}
```

</td>
</tr>
</table>

#### body_examples

Examples of the request body. Each example object SHOULD match the media type
and specified schema if present. This affects the value of
the [`requestBody`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely,
the [`examples`](https://spec.openapis.org/oas/v3.1.0#media-type-object) field
of
Media Type object inside
the value
of [`content`](https://spec.openapis.org/oas/v3.1.0#request-body-object) field
of Request Body object.

The values of this dictionary could be either examples themselves,
or `openapify.core.openapi.models.Example` objects. In the latter case,
extended information about examples, such as a summary and description, can be
added to the [Example](https://spec.openapis.org/oas/v3.1.0#example-object)
object.

<table>
<tr>
<th>Possible types</th>
<th>Examples</th>
</tr>
<tr>
<td> <code>Mapping[str, Any]</code> </td>
<td>

```python
{
    "Anna Karenina": {
        "title": "Anna Karenina",
        "author": "Leo Tolstoy",
        "year": 1877,
    }
}
```

</td>
</tr>
<tr>
<td> <code>Mapping[str, Example]</code> </td>
<td>

```python
{
    "Anna Karenina": Example(
        value={
            "title": "Anna Karenina",
            "author": "Leo Tolstoy",
            "year": 1877,
        },
        summary="The book 'Anna Karenina'",
        description="An object illustrating the book 'Anna Karenina'",
    )
}
```

</td>
</tr>
</table>

#### query_params

Dictionary of query parameters applicable for the operation, where the key is
the parameter name and the value can be either a Python data type or
a `QueryParam` object.

In the first case it is the Python data type for the query parameter for which
the JSON Schema will be built. This affects the value of
the [`parameters`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely,
the [`schema`](https://spec.openapis.org/oas/v3.1.0#parameter-object) field of
Parameter object.

In the second case it is `openapify.core.models.QueryParam` object that can
have extended information about the parameter, such as a default value,
deprecation marker, examples etc.

<table>
<tr>
<th>Possible types</th>
<th>Examples</th>
</tr>
<tr>
<td> <code>Mapping[str, Type]</code> </td>
<td>

```python
{"count": int}
```

</td>
</tr>
<tr>
<td> <code>Mapping[str, QueryParam]</code> </td>
<td>

```python
{
    "count": QueryParam(
        value_type=int,
        default=10,
        required=False,
        description="Limits the number of books returned",
        deprecated=False,
        allowEmptyValue=False,
        example=42,
    )
}
```

</td>
</tr>
</table>

#### headers

Dictionary of request headers applicable for the operation, where the key is
the header name and the value can be either a string or a `Header` object.

In the first case it is the header description. This affects the value of
the [`parameters`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely,
the [`description`](https://spec.openapis.org/oas/v3.1.0#parameter-object)
field of Parameter object.

In the second case it is `openapify.core.models.Header` object that can have
extended information about the header, such as a description, deprecation
marker, examples etc.

<table>
<tr>
<th>Possible types</th>
<th>Examples</th>
</tr>
<tr>
<td> <code>Mapping[str, str]</code> </td>
<td>

```python
{"X-Requested-With": "Information about the creation of the request"}
```

</td>
</tr>
<tr>
<td> <code>Mapping[str, Header]</code> </td>
<td>

```python
{
    "X-Requested-With": Header(
        description="Information about the creation of the request",
        required=False,
        value_type=str,
        deprecated=False,
        allowEmptyValue=False,
        example="XMLHttpRequest",
    )
}
```

</td>
</tr>
</table>

#### cookies

Dictionary of request cookies applicable for the operation, where the key is
the cookie name and the value can be either a string or a `Cookie` object.

In the first case it is the cookie description. This affects the value of
the [`parameters`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely,
the [`description`](https://spec.openapis.org/oas/v3.1.0#parameter-object)
field of Parameter object.

In the second case it is `openapify.core.models.Cookie` object that can have
extended information about the cookie, such as a description, deprecation
marker, examples etc.

<table>
<tr>
<th>Possible types</th>
<th>Examples</th>
</tr>
<tr>
<td> <code>Mapping[str, str]</code> </td>
<td>

```python
{"__ga": "A randomly generated number as a client identifier"}
```

</td>
</tr>
<tr>
<td> <code>Mapping[str, Cookie]</code> </td>
<td>

```python
{
    "__ga": Cookie(
        description="A randomly generated number as a client identifier",
        required=False,
        value_type=str,
        deprecated=False,
        allowEmptyValue=False,
        example="1.2.345678901.2345678901",
    )
}
```

</td>
</tr>
</table>

### Response

Decorator `response_schema` describes a single response from the API Operation.
Response can have an HTTP code, body and headers. If the Operation supports
more than one response, then the decorator must be applied multiple times to
cover each of them.

```python
from openapify import response_schema
```

#### body

A Python data type for the response body for which
the JSON Schema will be built. This affects the value of
the [`responses`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely,
the [`schema`](https://spec.openapis.org/oas/v3.1.0#media-type-object) field of
Media Type object inside the value
of [`content`](https://spec.openapis.org/oas/v3.1.0#response-object) field
of Response object.

| Possible types | Examples |
|----------------|----------|
| `Type`         | `Book`   |

#### http_code

An HTTP code of the response. This affects the value of
the [`responses`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely, the patterned key in
the [Responses](https://spec.openapis.org/oas/v3.1.0#responses-object) object.

| Possible types | Examples |
|----------------|----------|
| `str`          | `"200"`  |
| `int`          | `400`    |

#### media_type

A media type
or [media type range](https://www.rfc-editor.org/rfc/rfc7231#appendix-D) of the
response body. This affects the value of
the [`responses`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely, the key
of [`content`](https://spec.openapis.org/oas/v3.1.0#response-object) field of
Response object.

The default value is `"application/json"`.

| Possible types | Examples            |
|----------------|---------------------|
| `str`          | `"application/xml"` |

####

#### description

A description of the response. [CommonMark syntax](https://spec.commonmark.org)
MAY be used for rich text representation. This affects the value of
the [`responses`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely,
the [`description`](https://spec.openapis.org/oas/v3.1.0#response-object) field
of Response object.


| Possible types | Examples                |
|----------------|-------------------------|
| `str`          | `"Invalid ID Supplied"` |

#### headers

Dictionary of response headers applicable for the operation, where the key is
the header name and the value can be either a string or a `Header` object.

In the first case it is the header description. This affects the value of
the [`responses`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely,
the [`description`](https://spec.openapis.org/oas/v3.1.0#header-object)
field of Header object.

In the second case it is `openapify.core.models.Header` object that can have
extended information about the header, such as a description, deprecation
marker, examples etc.

<table>
<tr>
<th>Possible types</th>
<th>Examples</th>
</tr>
<tr>
<td> <code>Mapping[str, str]</code> </td>
<td>

```python
{"Content-Location": "An alternate location for the returned data"}
```

</td>
</tr>
<tr>
<td> <code>Mapping[str, Header]</code> </td>
<td>

```python
{
    "Content-Location": Header(
        description="An alternate location for the returned data",
        example="/index.htm",
    )
}
```

</td>
</tr>
</table>

#### example

Example of the response body. The example object SHOULD be in the correct format
as specified by the media type. This affects the value of
the [`responses`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely,
the [`example`](https://spec.openapis.org/oas/v3.1.0#media-type-object) field
of Media Type object inside the value
of [`content`](https://spec.openapis.org/oas/v3.1.0#response-object) field of
Response object.

<table>
<tr>
<th>Possible types</th>
<th>Examples</th>
</tr>
<tr>
<td> <code>Any</code> </td>
<td>

```python
{
    "title": "Anna Karenina",
    "author": "Leo Tolstoy",
    "year": 1877,
}
```

</td>
</tr>
</table>

#### examples

Examples of the response body. Each example object SHOULD match the media type
and specified schema if present. This affects the value of
the [`responses`](https://spec.openapis.org/oas/v3.1.0#operation-object)
field of the Operation object, or more precisely,
the [`examples`](https://spec.openapis.org/oas/v3.1.0#media-type-object) field
of Media Type object inside the value
of [`content`](https://spec.openapis.org/oas/v3.1.0#response-object) field of
Response object.

The values of this dictionary could be either examples themselves,
or `openapify.core.openapi.models.Example` objects. In the latter case,
extended information about examples, such as a summary and description, can be
added to the [Example](https://spec.openapis.org/oas/v3.1.0#example-object)
object.

<table>
<tr>
<th>Possible types</th>
<th>Examples</th>
</tr>
<tr>
<td> <code>Mapping[str, Any]</code> </td>
<td>

```python
{
    "Anna Karenina": {
        "title": "Anna Karenina",
        "author": "Leo Tolstoy",
        "year": 1877,
    }
}
```

</td>
</tr>
<tr>
<td> <code>Mapping[str, Example]</code> </td>
<td>

```python
{
    "Anna Karenina": Example(
        value={
            "title": "Anna Karenina",
            "author": "Leo Tolstoy",
            "year": 1877,
        },
        summary="The book 'Anna Karenina'",
        description="An object illustrating the book 'Anna Karenina'",
    )
}
```

</td>
</tr>
</table>

### Security requirements

Decorator `security_requirements`
declares [security mechanisms](https://spec.openapis.org/oas/v3.1.0#securityRequirementObject)
that can be used for the operation.

```python
from openapify import security_requirements
```

This decorator takes one or more `SecurityRequirement` mappings, where the key
is the requirement name and the value is `SecurityScheme` object. There are
classes for
each [security scheme](https://spec.openapis.org/oas/v3.1.0#security-scheme-object)
which can be imported as follows:

```python
from openapify.core.openapi.models import (
    APIKeySecurityScheme,
    HTTPSecurityScheme,
    OAuth2SecurityScheme,
    OpenIDConnectSecurityScheme,
)
```

For example, to add authorization by token, you can write something like this:

```python
from openapify import security_requirements
from openapify.core.openapi.models import (
    APIKeySecurityScheme,
    SecuritySchemeAPIKeyLocation,
)

XAuthTokenSecurityRequirement = {
    "x-auth-token": APIKeySecurityScheme(
        name="X-Auh-Token",
        location=SecuritySchemeAPIKeyLocation.HEADER,
    )
}

@security_requirements(XAuthTokenSecurityRequirement)
def secure_operation():
    ...
```

And the generated specification document will look like this:

```yaml
paths:
  /secure_path:
    get:
      responses: {}
      security:
      - x-auth-token: []
info:
  title: API
  version: 1.0.0
openapi: 3.1.0
components:
  securitySchemes:
    x-auth-token:
      type: apiKey
      name: X-Auh-Token
      location: header
```

Integration with web-frameworks
--------------------------------------------------------------------------------

Entity schema builders
--------------------------------------------------------------------------------
