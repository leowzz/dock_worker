import os
from typing import TypeAlias, Literal

from loguru import logger

ReplaceStrModes: TypeAlias = Literal['-', '_']


def normalize_image_name(image_name: str, remove_namespace: bool = True, replace_char: ReplaceStrModes = '_') -> str:
    """
    Normalize the image name by either removing the part before '/' or replacing '/' with a specified character.

    :param image_name: The original image name.
    :param remove_namespace: 是否移除镜像名前缀, 例如leo03w/ubuntu:20.04中的 leo03w.
    :param replace_char: The character to replace '/' with if method is 'replace'.
    :return: The normalized image name.

    >>> normalize_image_name('leo03w/ubuntu:20.04')
    'ubuntu:20.04'
    >>> normalize_image_name('leo03w/ubuntu:20.04', remove_namespace=False)
    'leo03w-ubuntu:20.04'
    >>> normalize_image_name('leo03w/ubuntu:20.04', remove_namespace=False, replace_char='_')
    'leo03w_ubuntu:20.04'
    """
    if not image_name:
        return ''
    if '/' in image_name:
        if remove_namespace:
            return image_name.split('/')[-1]
        else:
            return image_name.replace('/', replace_char)
    return image_name


def execute_command(command: str) -> bool:
    try:
        logger.info(f"Executing command: {command}")
        os.system(command)
        return True
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return False
