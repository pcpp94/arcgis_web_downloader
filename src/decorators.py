import functools

def retry(retries=4):
    def decorator_retry(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):      
            last_exception = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    last_exception = e
            raise last_exception
        return wrapper
    return decorator_retry

