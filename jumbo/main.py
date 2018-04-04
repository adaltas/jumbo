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
    print(session.svars["machines"])
    machines.add_machine(
        "toto",
        "10.10.10.11",
        1000,
        10000,
        [
            "master"
        ],
        2)
    print(session.svars["machines"])


@shell(prompt='jumbo > ', intro='Welcome to the jumbo shell!')
def jumbo_shell():
    pass


@jumbo_shell.command()
def hello():
    print('Hello')


if __name__ == '__main__':
    main()
