import os

COUNT_DIRS = [
    'cogs',
    'utils',
    '.'
]

COUNT_EXTENSIONS = (
    '.py',
)


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
