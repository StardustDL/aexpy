import click


@click.command()
@click.option("-d", "--debug", is_flag=True, help="Debug mode.")
@click.option("-p", "--port", type=int, default=8008, help="Port to listen on.")
def serve(debug: "bool" = False, port: "int" = 8008):
    """Serve web server."""
    from .entrypoint import serve as inner, buildApp

    inner(buildApp(), debug, port)
