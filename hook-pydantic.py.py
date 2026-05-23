# appli/hook-pydantic.py
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('pydantic')
hiddenimports += [
    'pydantic.deprecated.class_validators',
    'pydantic.deprecated.config',
    'pydantic.deprecated.tools',
    'pydantic_core',
    'pydantic_core._pydantic_core',
]