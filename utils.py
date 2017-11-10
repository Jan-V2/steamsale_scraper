import datetime

import os



def init_platform_vars():
    from sys import platform as _platform
    global dir_sep
    if _platform == "linux" or _platform == "linux2":
        # linux
        dir_sep = '/'
    # elif _platform == "darwin":
    #     # MAC OS X
    #     pass
    elif _platform == "win32":
        # Windows
        dir_sep = "\\"
    elif _platform == "win64":
        # Windows 64-bit
        dir_sep = "\\"
    else:
        raise OSError("OS not detected")

def listmerger(lists):
    # takes an array of lists and merges them into 1 multidimentional list csv style
    for k in lists:
        if not type(k) is list:
            print("not all arguments are lists")
            raise TypeError
    length = -2
    for l in lists:
        if not length == -2:
            if len(l) != length:
                print("not all items given in argument are lists")
                raise ValueError
        else:
            length = len(l)

        ret = []
        for i in range(0, length):
            temp = []
            for lis in lists:
                temp.append(lis[i])
            ret.append(temp)
        return ret

def get_subdir_list(dir):
    # gets the names for all the subdirs one layer deep
    # (so only the dirs in the rootdir)
    for root, dirs, files in os.walk(dir, topdown=True):
        return dirs


def log(logline):
    timestamp = get_timestamp()
    logline = timestamp + " " + logline
    print(logline)
    with open(ROOTDIR + dir_sep + "log.txt",mode='a') as logfile:
        logfile.write(logline + '\n')


def log_return():# puts an empty line in the logfile
    print()
    with open(ROOTDIR + dir_sep + "log.txt",mode='a') as logfile:
        logfile.write('\n')


def get_timestamp():
    return '[{:%Y-%m-%d_%H-%M-%S}]'.format(datetime.datetime.now())


def escape_string(string):
    escaped = string.translate(str.maketrans({"-":  r"\-",
                                              "]":  r"\]",
                                              "\\": r"\\",
                                              "^":  r"\^",
                                              "$":  r"\$",
                                              "*":  r"\*",
                                              ".":  r"\.",
                                              ",":  r"\,",
                                              "\n": r"\\n"}))
    return escaped

ROOTDIR = os.path.dirname(os.path.realpath(__file__))
dir_sep = ''
init_platform_vars()
ints_str = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]


if __name__ == '__main__':
    pass