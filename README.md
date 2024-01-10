# FastAPI Controller and Route Decorators

This package provides a set of decorators and utilities to simplify the creation of FastAPI controllers and routes. It allows you to define controllers as classes and routes as methods within those classes, with automatic dependency injection of shared dependencies.

## Features

- **Controller Class**: Define a group of related routes within a single class.
- **Route Decorators**: Easily define route handlers with specific HTTP methods (GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD, TRACE).
- **Automatic Dependency Injection**: Use `Depends` to inject dependencies into controller methods.
- **Simple Integration**: Integrate with existing FastAPI applications with minimal changes.

## Installation

To use these decorators, ensure that you have FastAPI installed in your environment. If not, you can install it using pip:

```bash
pip install fastapi-imp
```

Then, include the provided code in your project or package it accordingly.

## Usage

### Defining a Controller

To create a new controller, define a class and decorate it with `@controller`:

```python
from nest import controller

@controller()
class MyController:
    pass
```

### Defining Route Handlers

Use the provided HTTP method decorators to define route handlers within your controller:

```python
from nest import controller, get, post

@controller()
class MyController:
    
    @get("/items")
    def read_items(self):
        return {"message": "Reading items"}

    @post("/items")
    def create_item(self, item: dict):
        return {"message": "Creating item", "item": item}
```

### Dependency Injection

Use `Depends` to inject dependencies into your route handlers:

```python
from fastapi import Depends
from nest import controller, get

def get_current_user():
    # Logic to get the current user
    return {"user_id": 1}

@controller()
class MyController:
    
    # attribute inject
    current_user: dict = Depends(get_current_user)
    
    @get("/users/me")
    def read_current_user(self, current_user: dict = Depends(get_current_user)):
        assert self.current_user["user_id"] == current_user["user_id"]
        return {"message": "Reading current user", "user": current_user}
```

### Registering Controllers with FastAPI

To add your controller's routes to a FastAPI app, use the `as_api_router` utility:

```python
from fastapi import FastAPI
from nest import as_api_router
from my_controller import MyController

app = FastAPI()

my_controller_router = as_api_router(MyController())
app.include_router(my_controller_router)
```