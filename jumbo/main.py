import click
from click_shell import shell

from jumbo.core import machines
from jumbo.core import session


def main():
    machines.add_machine(
        'toto',
        '10.10.10.11',
        1000,
        10000,
        [
            'master'
        ]
    )
    machines.add_machine(
        "toto",
        "10.10.10.11",
        1000,
        10000,
        [
            "master"
        ],
        2)
    machines.add_machine(
        "tata",
        "10.10.10.12",
        2000,
        10000,
        [
            "edge"
        ],
        2)


@shell(prompt='jumbo > ', intro='Welcome to the jumbo shell!')
def jumbo_shell():
    pass


@jumbo_shell.command()
def hello():
    print('Hello')


if __name__ == '__main__':
    main()
