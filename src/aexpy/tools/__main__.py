from .cli import build


def main():
    return build()[0]()


if __name__ == "__main__":
    main()
