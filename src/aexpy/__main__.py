from .cli import main as mainCommand


def main():
    try:
        from .tools.cli import build

        for cmd in build():
            mainCommand.add_command(cmd)
    except Exception:
        pass
    return mainCommand()


if __name__ == "__main__":
    main()
