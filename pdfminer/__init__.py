import os

__version__ = os.environ.get('GIT_DESCRIBE_TAG', 'v0.0').replace('v', '') + '.' + os.environ.get('GIT_DESCRIBE_NUMBER', '0')

if __name__ == "__main__":
    print(__version__)
