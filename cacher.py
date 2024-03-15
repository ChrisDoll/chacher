import pickle
import os
import hashlib
from functools import wraps
from datetime import datetime, timedelta
import re
def cache_this(
        name: str = None, 
        time_limit: timedelta = timedelta(weeks=2)
        ):
    """
    This is a small function indended to work as a decorator to cache the results of other functions.
    
    This will cache the result of a function so that if it is called again with the same arguments, the result will be returned from the cache instead of being recalculated.

    It has two modes of operation:
    1. If no name is supplied, it uses the general cache
    2. If a name is supplied, it only checks for cache files with that name prefix
        This means that if you want to use a longer term cache for a specific function, you can supply a name to the decorator and a time limit and it will never be touched until the decorator is rerun.

    It also has a time limit for the cache, which defaults to 2 weeks.
    Keep in mind that should the decorator be used without a timelimit, it will delete all files older than 2 weeks, unless a name is supplied.
    
    Args:
        name (str): Optional name of the cache file. Specifies the cache should only check these files and leave other files alone.
        time_limit (timedelta): Optional time limit for the cache. Defaults to 2 weeks.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.abspath(os.path.join(script_dir, '../../.cache'))

    print(f'script_dir: {script_dir}')
    print(f"Using cache directory {cache_dir}")

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            os.makedirs(cache_dir, exist_ok=True)
            
            # Use current time to create a part of the filename that includes the timestamp
            now = datetime.now()
            current_time_str = now.strftime("%Y%m%d%H%M%S")

            # Serialize args and kwargs to create a unique hash key
            try:
                key = hashlib.sha256(pickle.dumps((args, kwargs))).hexdigest()
            except Exception as e:
                print(f"Failed to serialize args and kwargs with error: {e}")
                key = "key_error"
            
            # Use the name argument as a prefix for the cache file if it is provided
            file_prefix = f"{name}_{key}" if name else key
            
            # Look for existing cache files with this prefix
            for filename in os.listdir(cache_dir):
                if name and not filename.startswith(name): # This ensures that filenames are only checked against the relevant name prefix
                    continue
                if filename.startswith(file_prefix):
                    try:
                        _, timestamp_str = filename.split('_', 1)
                        timestamp = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S.pkl")
                    except ValueError:
                        os.remove(os.path.join(cache_dir, filename))
                        continue
                    except TypeError:
                        os.remove(os.path.join(cache_dir, filename))
                        continue

                    # Check if the cache file is less than a week old
                    print(f"    Found cache file {filename} with timestamp {timestamp}")
                    if now - timestamp <= time_limit:
                        file_path = os.path.join(cache_dir, filename)
                        print(f"    Found cached result, returning results from {file_path}")
                        with open(file_path, 'rb') as f:
                            return pickle.load(f)
                    else:
                        # Remove old cache file
                        os.remove(os.path.join(cache_dir, filename))
                        print(f"    Removed outdated cache file {filename}")

            # If no valid cache file is found, or all are outdated, calculate result
            print(f"    No valid cache found with calculating result for {func.__name__}")
            result = func(*args, **kwargs)
            new_file_path = os.path.join(cache_dir, f"{file_prefix}_{current_time_str}.pkl")
            with open(new_file_path, 'wb') as f:
                pickle.dump(result, f)
            
            return result
        return wrapper
    return decorator

def check(args, kwargs=None, name: str = None, time_limit: timedelta = timedelta(days=3)):
    """
    Checks for a cached file based on the provided arguments and loads it if found and not outdated.

    Parameters:
        args (tuple or any): Arguments with which the original function was called.
        kwargs (dict): Keyword arguments with which the original function was called.
        name (str): Optional name of the cache file. Specifies the cache should only check these files.
        time_limit (timedelta): Optional time limit for the cache. Defaults to 3 days.

    Returns:
        The cached result if a valid cache file is found, otherwise None.
    """
    # Ensure args is a tuple
    if not isinstance(args, tuple):
        args = (args,)

    # Ensure kwargs is a dictionary
    if kwargs is None:
        kwargs = {}
    
    # Getting the path to the cache directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.abspath(os.path.join(script_dir, '../../.cache'))
    os.makedirs(cache_dir, exist_ok=True)
    #print(f"Using cache directory {cache_dir}")
    # Serialize args and kwargs to create a unique hash key for file name
    try:
        key = hashlib.sha256(pickle.dumps((args, kwargs))).hexdigest()
        #print(f"key: {key}")
    except Exception as e:
        #print(f"Failed to serialize args and kwargs with error: {e}")
        return False, None
    file_prefix = f"{name}_{key}" if name else key
    now = datetime.now()

    # Look for existing cache files with this prefix
    for filename in os.listdir(cache_dir):
        if name and not filename.startswith(name): # This ensures that filenames are only checked against the relevant name prefix
            #print(f"    Skipping {filename}")
            continue
        if filename.startswith(file_prefix):
            try:
                #print(f"    Found cache file {filename}, getting timestamp...")
                match = re.search(r"(\d{14})\.pkl$", filename)
                timestamp_str = match.group(1)
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S") # Extract timestamp from filename
            except (ValueError, TypeError):
                #print(f"    Removing invalid cache file {filename}")
                os.remove(os.path.join(cache_dir, filename))
                continue

            if now - timestamp <= time_limit: # Check if the cache file is less than time_limit old
                file_path = os.path.join(cache_dir, filename)
                print(f"    Found cached result, returning results from cache")
                with open(file_path, 'rb') as f:
                    return True, pickle.load(f)
            else:
                os.remove(os.path.join(cache_dir, filename)) # Remove outdated cache file if necessary
    return False, None


def store(result = None, args = None, kwargs=None, name: str = None, time_limit: timedelta = timedelta(weeks=2)):
    """
    Checks for a cached file based on the provided arguments and loads it if found and not outdated.

    Parameters:
        args (tuple or any): Arguments with which the original function was called.
        kwargs (dict): Keyword arguments with which the original function was called.
        name (str): Optional name of the cache file. Specifies the cache should only check these files.
        time_limit (timedelta): Optional time limit for the cache. Defaults to 2 weeks.

    Returns:
        The cached result if a valid cache file is found, otherwise None.
    """
    # Ensure args is a tuple
    if not isinstance(args, tuple):
        args = (args,)

    # Ensure kwargs is a dictionary
    if kwargs is None:
        kwargs = {}
    
    # Getting the path to the cache directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.abspath(os.path.join(script_dir, '../../.cache'))
    os.makedirs(cache_dir, exist_ok=True)
    #print(f"Using cache directory {cache_dir}")

    # Serialize args and kwargs to create a unique hash key for file name
    try:
        key = hashlib.sha256(pickle.dumps((args, kwargs))).hexdigest()
        #print(f"key: {key}")
    except Exception as e:
        print(f"Failed to serialize args and kwargs with error: {e}")
        return None
    
    file_prefix = f"{name}_{key}" if name else key
    now = datetime.now().strftime("%Y%m%d%H%M%S")

    # Store the results
    new_file_path = os.path.join(cache_dir, f"{file_prefix}_{now}.pkl")
    with open(new_file_path, 'wb') as f:
        pickle.dump(result, f)
    


if __name__ == "__main__":
    

    def function_with_cache_check(a, b):
        
        # Doing something
        def my_function(a, b):
            print("Calculating result for", a, b)
            return a + b
    
        cache_loaded, data = check((a,b), name="my_function")  # Single argument

        print(f'Did cache get loaded: {cache_loaded}')
        if cache_loaded:
            print("Cache loaded")
            return data
        else:
            print("Cache not loaded")
            result = my_function(a, b)
            store(result = result, args = (a, b), name="my_function")
            return result
        
    print(function_with_cache_check(1, 2))
    print(function_with_cache_check(1, 2))
    print(function_with_cache_check(3, 2))
    print(function_with_cache_check(3, 2))