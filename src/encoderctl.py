from argparse import ArgumentParser
from time import sleep

from encoder import EncoderMultiplexer
from rich import print


def main():
    parser = ArgumentParser(prog="encoderctl", description="Read the value for a given encoder")
    parser.add_argument("index", help="The encoder to select (0 <= index < 8)")

    args = parser.parse_args()
    multiplexer = EncoderMultiplexer()
    index = int(args.index)

    with multiplexer.select(index) as enc:
        while True:
            print(f"Encoder {index}: [bold]{enc.angle}[/bold]", end="\r")
            sleep(0.5)


if __name__ == "__main__":
    main()
