import os


def make_folder_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)


def rename_object_to_snake_case(object):
    object.name = object.name.replace(".", "-")
    object.name = object.name.replace(" ", "-")


def get_plugin_folder():
    return os.path.dirname(os.path.dirname(__file__))
