"""
Command-line entry point for running ChromePDF.
To execute, run:
> python -m chromepdf generate-pdf [args] [kwargs]
"""

if __name__ == '__main__':
    import sys

    from .run import chromepdf_run
    chromepdf_run(sys.argv[1:])
