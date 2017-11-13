from os import getcwd
from os.path import join

default_settings = {
    'chat_bot_name': 'Moby',
    'bot_token': '',
    'email_username': '',
    'email_password': '',
    'email_address': '',
    'email_smtp': '',
    'email_port': '',
    'cowan_text_gateway': '',
    'client_email': '',
    'client_password': '',
}


def create_new_settings(path=getcwd()):
    """
    Initializes the settings file to some initial value.
    :param path: path to create the setting file
    :return: None
    """
    with open(join(path, "settings.txt"), "w") as f:
        for k in default_settings.keys():
            f.write(k + '=' + default_settings[k] + '\n')

    return None


def read_settings(f):
    """
    Load settings from a file and parse them.
    :param f: path to settings file
    :return: dict of settings
    """

    out = {}

    with open(f, "r") as f:
        for line in f.readlines():
            line = line.rstrip()
            key, value = line.split('=')
            out[key] = value

    return out


if __name__ == '__main__':
    # create_new_settings()
    d = read_settings('settings.txt')

    for key in d.keys():
        print(key, d[key])
