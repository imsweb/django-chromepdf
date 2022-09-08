"""
Command-line entry point for running ChromePDF.
To execute, run:
> python -m chromepdf generate-pdf [args] [kwargs]
"""


def main():
    """
    To make unit testing chromepdf.__main__ easier, put everything into a function
    Except the single line executed by __name__ == '__main__', which is hard if not impossible to get at.
    """
    import sys

    from .run import chromepdf_run
    chromepdf_run(sys.argv[1:])


if __name__ == '__main__':
    main()
