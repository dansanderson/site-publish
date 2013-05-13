import sys


# The available commands.  Each of these has a module in this package with the
# given name, containing a class with this name using an initial capital
# letter.
COMMANDS = ['publish']

# The length of the longest command name, for columnar display.
_COMMAND_NAME_MAX_WIDTH = max(len(c) for c in COMMANDS)


def get_command_class(cmd_name):
    """Imports and gets the command class for a given command name.

    Args:
        cmd_name: The name of the command, a str.

    Returns:
        The command class.
    """
    mod = __import__('tool.' + cmd_name)
    return getattr(getattr(mod, cmd_name), cmd_name.title())


def main(args):
    """The main command-line tool routine.

    Args:
        args: The command-line arguments, not including the tool name.

    Returns:
        The exit status for the command.
    """
    if not args or (args[0] != 'help' and args[0] not in COMMANDS):
        sys.stderr.write(
            'Usage:  sp <command> [args]\n\n'
            'For help:  sp help\n')
        return 1

    if args[0] == 'help':
        if len(args) == 1:
            # List the available commands with short descriptions.
            sys.stdout.write(
                'Usage:  sp <command> [args]\n\n'
                'Available commands:\n')
            for cmd_name in COMMANDS:
                cmd_class = get_command_class(cmd_name)
                sys.stdout.write(
                    ('  %' + str(_COMMAND_NAME_MAX_WIDTH) + 's  %s\n')
                    % (cmd_name, cmd_class.get_short_desc()))
            return 0

        # Print the help text for the given command.
        cmd_name = args[1]
        cmd_class = get_command_class(cmd_name)
        sys.stdout.write(cmd_class.get_long_desc())
        sys.stdout.write('\n')
        return 0

    cmd_name = args[0]
    cmd = get_command_class(cmd_name)()
    return cmd.do_cmd(args[1:])
