from functools import wraps


def transform(*, param: str, attr: str):
    def decorator(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            try:
                kwargs[param] = getattr(kwargs[param], attr)()
            except (KeyError, AttributeError, TypeError):
                pass

            return await func(*args, **kwargs)

        return inner

    return decorator
