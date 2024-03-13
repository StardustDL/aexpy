from .cli import main

try:
    from .tools.cli import tool

    main.add_command(tool)
except Exception:
    pass

if __name__ == "__main__":
    main()
