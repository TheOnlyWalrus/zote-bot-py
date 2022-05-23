import os

COUNT_DIRS = [
    'cogs',
    'utils',
    '.'
]

COUNT_EXTENSIONS = (
    '.py',
)

ESCAPE_CHARS = [  # (find, replace)
    ('`', '\\`')
]


def escape_user(username: str) -> str:
    """
    Escapes a username so that it can be used in a discord message.
    """
    u = username
    for char, escape in ESCAPE_CHARS:
        u = u.replace(char, escape)

    return u


def aloc() -> int:
    """
    Returns the total lines of code in the project.
    """
    def _gen(reader):
        while True:
            b = reader(2 << 15)
            if not b:
                break
            yield b

    count = 0

    for dir_ in COUNT_DIRS:
        for file in os.listdir(dir_):
            if file.endswith(COUNT_EXTENSIONS):
                with open(os.path.join(dir_, file), 'rb') as f:
                    count += sum(buf.count(b'\n') for buf in _gen(f.read))

    return count
