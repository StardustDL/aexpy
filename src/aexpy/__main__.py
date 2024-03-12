from .cli import main
from .tools.cli import tool

main.add_command(tool)

if __name__ == "__main__":
    main()
