import logging


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='\033[2m%(asctime)s\033[0m %(message)s',
        datefmt='%H:%M:%S'
    )

    logging.getLogger("fastmcp").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("mcp").setLevel(logging.WARNING)
