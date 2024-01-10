import inspect
from collections import namedtuple
from functools import wraps
from typing import TypeVar, Type, Callable, overload

from fastapi import APIRouter
from fastapi.params import Depends

T = TypeVar("T")

RouteMeta = namedtuple("RouteMeta", ("method", "path", "args", "kwargs"))


def is_depends(instance: object) -> bool:
    """
    Check if an object is a Depends instance
    """
    return isinstance(instance, Depends)


_CONTROLLER_ROUTER_KEY = "_controller_router_"

_ROUTER_META_KEY = "_router_meta_"


def is_controller(instance: object) -> bool:
    """
    Check if an object is a controller
    """
    return hasattr(instance, _CONTROLLER_ROUTER_KEY)


class Controller:
    """
    Decorate a class as a controller
    """

    def __init__(self, *args, **kwargs):
        self._router = APIRouter(*args, **kwargs)

    def __call__(self, kls: Type[T]) -> Type[T]:
        """
        Decorate a class as a controller
        """
        assert inspect.isclass(kls), "Controller must be a class"

        controller_key = f"_{kls.__name__}__self"

        # Get all the fields that are Depends instances
        field_depends = inspect.getmembers(kls, is_depends)

        # Make sure the controller key is not already used
        assert controller_key not in [field_name for field_name, _ in field_depends]

        annotations = kls.__annotations__

        params = []

        # Add all the Depends instances as parameters
        for field_name, field_value in field_depends:
            assert (
                    controller_key != field_name
            ), f"Depends field name '{field_name}' is reserved for controller instance"
            parameter = inspect.Parameter(
                name=field_name,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=field_value,
                annotation=annotations.get(field_name),
            )
            params.append(parameter)

        params.append(
            inspect.Parameter(
                controller_key,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=Depends(kls),
            )
        )

        depend_signature = inspect.Signature(params)

        # Add all the methods as routes
        for method_name, method in inspect.getmembers(kls, inspect.isfunction):
            meta: RouteMeta | None = getattr(method, _ROUTER_META_KEY, None)
            if not meta:
                continue

            method_signature = inspect.signature(method)
            parameters = list(method_signature.parameters.values())[1:] + list(
                depend_signature.parameters.values()
            )

            is_coroutine_function = inspect.iscoroutinefunction(method)

            if is_coroutine_function:
                @wraps(method)
                async def router_handler(*args, **kwargs):
                    """
                    Closure to handle the route
                    """
                    # Get the controller instance
                    _controller = kwargs.pop(controller_key)

                    # Set all the Depends instances as attributes on the controller
                    for field_name, _ in field_depends:
                        setattr(_controller, field_name, kwargs.pop(field_name))
                    # Call the method
                    return await method(self=_controller, *args, **kwargs)
            else:
                @wraps(method)
                def router_handler(*args, **kwargs):
                    """
                    Closure to handle the route
                    """
                    # Get the controller instance
                    _controller = kwargs.pop(controller_key)

                    # Set all the Depends instances as attributes on the controller
                    for field_name, _ in field_depends:
                        setattr(_controller, field_name, kwargs.pop(field_name))
                    # Call the method
                    return method(self=_controller, *args, **kwargs)

            router_handler.__signature__ = method_signature.replace(parameters=parameters)  # type: ignore[attr-defined]

            self._router.add_api_route(
                meta.path,
                router_handler,
                methods=[meta.method],
                *meta.args,
                **meta.kwargs,
            )

        setattr(kls, _CONTROLLER_ROUTER_KEY, self._router)

        return kls


controller = Controller


def as_api_router(_controller: object) -> APIRouter:
    """
    Get the APIRouter instance from a controller
    """
    assert is_controller(_controller), "Object must be decorated with @Controller"
    return getattr(_controller, _CONTROLLER_ROUTER_KEY)


class Method:
    """
    Decorate a function as a route with a specific HTTP method
    """
    allowed_methods = [
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
        "OPTIONS",
        "HEAD",
        "TRACE",
    ]

    def __init__(self, method: str):
        assert (
                method in self.allowed_methods
        ), f"Method must be one of {self.allowed_methods}"
        self.method = method

    @overload
    def __call__(self, path_or_func: str, *args, **kwargs):
        ...

    @overload
    def __call__(self, path_or_func: Callable, *args, **kwargs):
        ...

    def __call__(self, path_or_func: str | Callable, *args, **kwargs):
        if callable(path_or_func):
            # If the first argument is a function, act like the original decorator
            return self._create_route("", path_or_func, *args, **kwargs)

        # Otherwise, return a new decorator with the path argument filled in
        def decorator(func):
            return self._create_route(path_or_func, func, *args, **kwargs)

        return decorator

    def _create_route(self, path: str, func: Callable, *args, **kwargs):
        """
        Create a route from a path and function
        """
        is_coroutine_function = inspect.iscoroutinefunction(func)

        if is_coroutine_function:
            @wraps(func)
            async def inner(*inner_args, **inner_kwargs):
                return await func(*inner_args, **inner_kwargs)
        else:
            @wraps(func)
            def inner(*inner_args, **inner_kwargs):
                return func(*inner_args, **inner_kwargs)

        meta = RouteMeta(method=self.method, path=path, args=args, kwargs=kwargs)
        setattr(inner, _ROUTER_META_KEY, meta)

        return inner


get = Method("GET")

post = Method("POST")

put = Method("PUT")

delete = Method("DELETE")

patch = Method("PATCH")

options = Method("OPTIONS")

head = Method("HEAD")

trace = Method("TRACE")
