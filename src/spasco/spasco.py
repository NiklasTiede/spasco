"""spasco - spaces to underscores
==============================
command line tool for replacing spaces within files and directories
"""
# Copyright (c) 2020, Niklas Tiede.
# All rights reserved. Distributed under the MIT License.

import argparse
import configparser
import glob
import logging
import os
import sys
from pprint import pprint
from textwrap import dedent
from typing import List

from term_color import Txt, fmt

# set up a settings file and then a logger:
config = configparser.ConfigParser()
config.read('settings.ini')

# some information about version, name, author, src
__title__ = os.path.splitext(__file__)[0]
__version__ = "0.1.0"
__author__ = 'Niklas Tiede'
__author_email__ = 'niklastiede2@gmail.com'
__src_url__ = 'https://github.com/NiklasTiede/spasco'

# default values for log record are created:
if not config.read('settings.ini'):
    config['VALUE-SETTINGS'] = {
        'search_value': "' '",
        'new_value': '_',
    }
    config['LOG-SETTINGS'] = {
        'Logging_turned_on': False,
        'logger_filename': f'{__title__}.log',
        'logger_location': os.environ['HOME'],
    }
    with open('settings.ini', 'w') as f:
        config.write(f)

# set a logger
logger_path = f"{config.get('LOG-SETTINGS', 'logger_location')}/{config.get('LOG-SETTINGS', 'logger_filename')}"
logging.basicConfig(
    filename=logger_path,
    level=logging.DEBUG,
    format='%(levelname)s | %(message)s | %(asctime)s'
)


# TODO: how to exclude windows/macos properly??
if sys.platform != 'linux':
    print(f"{__title__!r} is currently not optimized for Windows / OS X")
    sys.exit(1)




def main(argv):
    """ Main program.

    :argument
        argv: command-line arguments, such as sys.argv (including the program name
        in argv[0]).

    :return
        Zero on successful program termination, non-zero otherwise.
    """

    parser = __build_parser()[0]
    args = parser.parse_args(argv[1:])

    pprint(vars(args))

    if vars(args).get('command', None) == 'config':
        execute_config(parser, argv)
        return 0

    files_dirs = []

    # no recursive flag is used, current dirs files/dirs are collected:
    if args.file_or_dir and not args.recursive:
        files_dirs.extend(args.file_or_dir)

    # recursive flag is used: all files/dirs (nested ones also) within specified dir are collected:
    if args.recursive:
        files_dirs = recurse_dirs_and_files()

    # sort paths (longest paths first) so that renaming starts with the deepest nested file/directory:
    files_dirs = [x.split('/') for x in files_dirs]
    sorted_paths = sorted(files_dirs, key=len, reverse=True)
    files_dirs = ['/'.join(path_as_lst) for path_as_lst in sorted_paths]



    # --------------------------------
    # 2: filter each path
    SEARCH_VALUE = args.search_value if args.search_value else config.get('VALUE-SETTINGS', 'search_value')
    if SEARCH_VALUE == "' '":
        SEARCH_VALUE = ' '

    filtered_paths = []

    print(f'selected list before 1st filter: {files_dirs}')
    all_selected_files_dirs = files_dirs.copy()

    logging.info(f'number of all files/dirs: {len(all_selected_files_dirs)}')
    print(f'number of all files/dirs: {len(all_selected_files_dirs)}')

    # ------ 1: search-value filter ------
    [files_dirs.remove(x) for x in all_selected_files_dirs if not search_value_match(path=os.path.split(x)[1], SEARCH_VALUE=SEARCH_VALUE)]
    if not files_dirs:
        print(f'None of the selected {len(all_selected_files_dirs)} files/dirs contained the search-value {SEARCH_VALUE!r} ')
        return 1
    print(f'selected list after 1st filter (search-value): {files_dirs}')

    # ------ 2: pattern-only filter ------



    pattern = '*.py'
    glob_filter = [name for name in glob.glob(pattern)]
    pprint(glob_filter)
    base, file = os.path.split('reefneu/sdfcsndc/fefe.py')
    print(file)


    [files_dirs.remove(x) for x in files_dirs.copy() if args.pattern_only and
                     not is_match(s=os.path.split(x)[1], p=args.pattern_only)]




    [files_dirs.remove(x) for x in files_dirs.copy() if args.pattern_only and
                     not is_match(s=os.path.split(x)[1], p=args.pattern_only)]
    if not files_dirs:
        print(f'No file/dir present containing the pattern {args.pattern_only!r} ')
        return 1
    print(f'selected list after 2nd filter (pattern-only): {files_dirs}')

    # ------ 3: except-pattern filter -----
    [files_dirs.remove(x) for x in files_dirs.copy() if args.except_pattern and
                     not is_no_match(s=os.path.split(x)[1], p=args.except_pattern)]
    if not files_dirs:
        print(f'No file/dir present containing the search-value {SEARCH_VALUE!r} and not the except-pattern {args.except_pattern!r} ')
        return 1
    print(f'selected list after 3rd filter (except-pattern): {files_dirs}')

    # ------ 4: dirs-only filter -----
    [files_dirs.remove(x) for x in files_dirs.copy() if args.dirs_only and not os.path.isdir(x)]
    if not files_dirs:
        print(f'No directory present after filtering out files.')
        return 1
    print(f'selected list after 4th filter (dirs-only): {files_dirs}')

    # ------ 5: files-only filter -----
    [files_dirs.remove(x) for x in files_dirs.copy() if args.files_only and
                     not os.path.isfile(x)]
    if not files_dirs:
        print(f'No file present after filtering out directories.')
        return 1
    print(f'selected list after 5th filter (files-only): {files_dirs}')
    filtered_paths = files_dirs





    # 3: renaming function created
    NEW_VALUE = args.new_value if args.new_value else config.get('VALUE-SETTINGS', 'new_value')

    renamed_paths = path_renaming(path_lst=filtered_paths,
                                  search_value=SEARCH_VALUE,
                                  new_value=NEW_VALUE)

    print(f'{len(filtered_paths)} files/directories can be renamed:')

    print(f"before {' '*(max([len(x) for x in filtered_paths]) - len('before') + 6)} after")

    for before, after in list(zip(filtered_paths, renamed_paths)):
        print(f"{before!r}{' '*(max([len(x) for x in filtered_paths]) - len(before))} --> {after!r}")

    is_proceeding = input('OK to proceed with renaming? [y/n] ')

    if is_proceeding.lower() == 'y':
        print('renaming will be performed.')
        path_renaming(path_lst=filtered_paths, search_value=SEARCH_VALUE, new_value=NEW_VALUE, renaming=True)
        # 3 files and 2 dirs were converted. message /> save message as log (which files etc.)
        filecount, dircount = 0, 0
        for path in filtered_paths:
            if os.path.isdir(path):
                dircount += 1
            if os.path.isfile(path):
                filecount += 1
        print(f'{filecount} files and {dircount} directories were renamed.')
        return 0
    else:
        print(fmt("command aborted.", textcolor=Txt.greenblue))
        return 1


def execute_config(parser, argv):
    """ subparser triggering from main is refactored in here. """
    subparser = __build_parser()[1]
    args = parser.parse_args(argv[1:])

    # use as error handling, to let people know, that a
    boom = vars(args).copy()
    boom.pop('file_or_dir')
    boom = boom.values()
    print(boom)

    if args.show_settings:
        current_settings = dedent(f"""
        VALUE-SETTINGS:
          search_value: {config.get('VALUE-SETTINGS', 'search_value')}
          new_value: {config.get('VALUE-SETTINGS', 'new_value')}
        LOG-SETTINGS:
          logging_turned_on: {config.getboolean('LOG-SETTINGS', 'logging_turned_on')}
          logger_filename: {config.get('LOG-SETTINGS', 'logger_filename')}
          logger_location: {config.get('LOG-SETTINGS', 'logger_location')}
        """)
        print(current_settings)
        return 0

    if args.turn_log_on:
        print(f'change logging on/off: {args.turn_log_on.capitalize()}')
        config['LOG-SETTINGS']['logging_turned_on'] = args.turn_log_on.capitalize()
        with open('settings.ini', 'w') as fp:
            config.write(fp)
        log_state = config.getboolean('LOG-SETTINGS', 'logging_turned_on')
        if log_state:
            print('log recording is activated.')
        else:
            print('log recording is deactivated.')
        return 0

    if args.log_name:
        config['LOG-SETTINGS']['logger_filename'] = args.log_name
        with open('settings.ini', 'w') as fp:
            config.write(fp)
        print(f"The new log filename is {config.get('LOG-SETTINGS', 'logger_filename')}")
        return 0

    if args.log_location:
        log_location = args.log_location
        if '~' in args.log_location:
            log_location = os.path.expanduser(args.log_location)
        if not os.path.isdir(log_location):
            print(f'The given path {args.log_location!r} is not a valid directory!')
            return 1
        config['LOG-SETTINGS']['logger_location'] = log_location
        with open('settings.ini', 'w') as fp:
            config.write(fp)
        print(f"The new log location is {config.get('LOG-SETTINGS', 'logger_location')}")
        return 0

    if args.set_search_value:
        config['VALUE-SETTINGS']['search_value'] = args.set_search_value
        with open('settings.ini', 'w') as fp:
            config.write(fp)
        print(f"The new search-value is {config.get('VALUE-SETTINGS', 'search_value')}")
        return 0

    if args.set_new_value:
        config['VALUE-SETTINGS']['new_value'] = args.set_new_value
        with open('settings.ini', 'w') as fp:
            config.write(fp)
        print(f"The new 'new-value' is {config.get('VALUE-SETTINGS', 'new_value')}")
        return 0

    subparser.print_help()
    return 1


def path_renaming(path_lst, search_value, new_value, renaming=False):
    """ text """
    renamed_paths = []
    for old_path_name in path_lst:
        path_base, file = os.path.split(old_path_name)
        new_name = file.replace(search_value, new_value)
        full_new = os.path.join(path_base, new_name)
        # full_new = path_base + '/' + new_name
        renamed_paths.append(full_new)
        if renaming:
            os.rename(old_path_name, full_new)
            #
    return renamed_paths


def search_value_match(path, SEARCH_VALUE):
    """ text """
    return SEARCH_VALUE in path


def recurse_dirs_and_files() -> List[str]:
    """
    :returns
        all dirs and files recursive, sorted
    """
    all_files_dirs = []
    base_path = os.getcwd()
    # collect all rel. paths in a list (rel to cwd):
    for dirpath, dirnames, filenames in os.walk(base_path):
        for filename in filenames:
            full_filepath = dirpath + '/' + filename
            rel_filepath = os.path.relpath(full_filepath, base_path)
            all_files_dirs.append(
                rel_filepath
            )  # .split('/')  sort lists according to their length
        for dirname in dirnames:
            full_dirpath = dirpath + '/' + dirname
            rel_dirpath = os.path.relpath(full_dirpath, base_path)
            # print('rel. dirpath:', rel_dirpath.split('/'))
            all_files_dirs.append(rel_dirpath)
    return all_files_dirs


# def is_match(s: str, p: str) -> bool:
#     """
#     wildcard characters (bash) can be used to rename only files/dirs sharing
#       *tern
#     p?ttern
#     """
#     sl = len(s)
#     pl = len(p)
#     dp = [[False for i in range(pl + 1)] for j in range(sl + 1)]
#     s = " " + s
#     p = " " + p
#     dp[0][0] = True
#     for i in range(1, pl + 1):
#         if p[i] == '*':
#             dp[0][i] = dp[0][i - 1]
#     for i in range(1, sl + 1):
#         for j in range(1, pl + 1):
#             if s[i] == p[j] or p[j] == '?':
#                 dp[i][j] = dp[i - 1][j - 1]
#             elif p[j] == '*':
#                 dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
#     return dp[sl][pl]


# def is_no_match(s: str, p: str) -> bool:
#     """ reverses the 'is_match'-function to exclude files with certain patterns from renaming. """
#     return not is_match(s, p)


# hack for removing the metavar below the subparsers title
from argparse import ArgumentParser, HelpFormatter, _SubParsersAction


class NoSubparsersMetavarFormatter(HelpFormatter):
    def _format_action(self, action):
        result = super()._format_action(action)
        if isinstance(action, _SubParsersAction):
            # fix indentation on first line
            return "%*s%s" % (self._current_indent, "", result.lstrip())
        return result

    def _format_action_invocation(self, action):
        if isinstance(action, _SubParsersAction):
            # remove metavar and help line
            return ""
        return super()._format_action_invocation(action)

    def _iter_indented_subactions(self, action):
        if isinstance(action, _SubParsersAction):
            try:
                get_subactions = action._get_subactions
            except AttributeError:
                pass
            else:
                # remove indentation
                yield from get_subactions()
        else:
            yield from super()._iter_indented_subactions(action)


# # class inherits a class which removes the subparsers metavar and a help-text formatter:
# class MyOwnFormatter(NoSubparsersMetavarFormatter, argparse.RawTextHelpFormatter):
#     pass


# class inherits a class which removes the subparsers metavar and a help-text formatter:
class MyOwnFormatter(NoSubparsersMetavarFormatter, argparse.RawDescriptionHelpFormatter):
    pass

# def add_parser_help(p):
#     """
#     So we can use consistent capitalization and periods in the help. You must
#     use the add_help=False argument to ArgumentParser or add_parser to use
#     this. Add this first to be consistent with the default argparse output.
#     """
#
#     p.add_argument(
#         '-h', '--help',
#         # action=_HelpAction,
#         action='help',
#         default=argparse.SUPPRESS,
#         help="Show this help message and exit.",
#     )


def __build_parser():
    """Constructs the main_parser for the command line arguments.

    :returns
      An ArgumentParser instance for the CLI.
    """
    # noinspection PyTypeChecker
    main_parser = argparse.ArgumentParser(
        prog=__title__,
        # usage='%(prog)s [options] path',
        add_help=False,
        description=f'A renaming tool for replacing whitespaces within file- or directory names '
                    f'by underscores.\nsrc: {__src_url__}',
        epilog='Make your files more computer-friendly :)',
        # formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, max_help_position=50),
        formatter_class=lambda prog: MyOwnFormatter(prog, max_help_position=80),
    )

    # positional arguments:
    main_parser.add_argument(
        'file_or_dir',
        metavar='files/directories',
        action='store',
        nargs='*',
        default=os.listdir(),
        help='Select files/dirs to be renamed. Default: current directory is listed.'
    )

    # optional arguments:
    main_parser.add_argument(
        '-s',
        # '--search-value',
        dest='search_value',
        nargs='?',
        action='store',
        # metavar='<search_value>',
        metavar='search_value',
        help='Searches for characters/patterns to be replaced other than whitespaces.',
    )

    main_parser.add_argument(
        '-n',
        # '--new-value',
        dest='new_value',
        nargs='?',
        action='store',
        metavar='new_value',
        # help='substitutes the search-value for custom characters/patterns other than underscores.'
        help='substitutes the search-value for custom characters/patterns other than underscores.'
    )

    main_parser.add_argument(
        '-p',
        # '--pattern-only',
        dest='pattern_only',
        nargs='?',
        action='store',
        metavar='pattern_only',
        help='Only files/dirs containing the pattern are renamed.'
    )

    main_parser.add_argument(
        '-e',
        # '--except-pattern',
        metavar='except_pattern',
        dest='except_pattern',
        nargs='?',
        action='store',
        help='Only files/dirs not containing the pattern are renamed.'
    )

    main_parser.add_argument(
        '-d',
        '--dirs-only',
        action='store_true',
        help='Only directories are renamed.'
    )

    main_parser.add_argument(
        '-f',
        '--files-only',
        action='store_true',
        help='Only files are renamed.'
    )

    main_parser.add_argument(
        '-r',
        '--recursive',
        action='store_true',
        help='Recurse into directories.'
    )

    main_parser.add_argument(
        '-v',
        '--version',
        action='version',
        help='Show version number and exit.',
        version=f'%(prog)s {__version__}'
    )

    main_parser.add_argument(
        '-h',
        '--help',
        # action=_HelpAction,
        action='help',
        # default=argparse.SUPPRESS,
        help="Show this help message and exit.",
    )

    # --------------------------------------
    # structure configuration as sub-main_parser:
    config_subparsers = main_parser.add_subparsers(
        title='log and rename configuration',
        # dest='config_parser_no_arg',
    )

    config_subparser = add_config_subparser(config_subparsers)

    return main_parser, config_subparser


def add_config_subparser(sub_parsers):

    config_subparser = sub_parsers.add_parser(
        name='config',
        # description='All renaming actions can be recorded within a log file.',
        description='search-value and new-value can be changed. Logging to record all '
                    'renaming actions as log file can be activated.',
        usage=f'{__title__} config [--show-setting] [-o true/false] [-n [filename]] [-l [pathname]] [-h, --help ]',
        add_help=False,
        formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, max_help_position=33),
        # formatter_class=argparse.RawDescriptionHelpFormatter,
        help=f"Sub-command to interact with {__title__}'s logging and rename settings.",
    )

    config_subparser.add_argument(
        '--show-settings',
        # dest='show_settings',
        action='store_true',
        help='Returns your current settings for logging and renaming.'
    )
    config_subparser.add_argument(
        '-h',
        '--help',
        action='help',
        help="Show this help message and exit.",
    )

    config_subparser_logging = config_subparser.add_argument_group('log settings')
    config_subparser_logging.add_argument(
        '-o',
        # '--turn-log-on',
        nargs='?',
        metavar='true/false',
        dest='turn_log_on',
        choices=['true', 'false'],
        help="Log record is turned on/off."
    )
    config_subparser_logging.add_argument(
        '-f',
        # '--log-name',
        nargs='?',
        metavar='filename',
        dest='log_name',
        help='Set up a new filename for the logger.',
    )
    config_subparser_logging.add_argument(
        '-l',
        # '--log-location',
        nargs='?',
        metavar='pathname',
        dest='log_location',
        help=f'Set up a new file location for the logger.',
    )

    config_subparser_renaming = config_subparser.add_argument_group('rename settings')
    config_subparser_renaming.add_argument(
        '-s',
        nargs='?',
        metavar='search_value',
        dest='set_search_value',
        help=f"Set up a new search value.",
    )
    config_subparser_renaming.add_argument(
        '-n',
        nargs='?',
        metavar='new_value',
        dest='set_new_value',
        help='Set up a new value which will replace the search-value.',
    )

    config_subparser.set_defaults(command='config')
    return config_subparser


def run_main():
    """ text """
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        sys.stderr.write(__title__ + ': ' + str(e) + '\n')
        sys.exit(1)


if __name__ == '__main__':
    run_main()
