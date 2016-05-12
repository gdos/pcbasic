"""
PC-BASIC - GW-BASIC/BASICA/Cartridge BASIC compatible interpreter

(c) 2013, 2014, 2015, 2016 Rob Hagemans
This file is released under the GNU GPL version 3 or later.
"""

import sys
import locale
import platform
import subprocess
import logging
import traceback
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

# set locale - this is necessary for curses and *maybe* for clipboard handling
# there's only one locale setting so best to do it all upfront here
# NOTE that this affects str.upper() etc.
locale.setlocale(locale.LC_ALL, '')

from . import ansipipe
from . import basic
from . import config


def main():
    """Initialise and perform requested operations."""
    try:
        with config.TemporaryDirectory(prefix='pcbasic-') as temp_dir:
            # get settings and prepare logging
            settings = config.Settings(temp_dir)
            command = settings.get_command()
            if command == 'version':
                # in version mode, print version and exit
                show_version(settings)
            elif command == 'help':
                # in help mode, print usage and exit
                config.show_usage()
            elif command == 'convert':
                # in converter mode, convert and exit
                convert(settings)
            else:
                # otherwise, start an interpreter session
                start_basic(settings)
    except:
        # without this except clause we seem to be dropping exceptions
        # probably due to the sys.stdout.close() hack below
        logging.error('Unhandled exception\n%s', traceback.format_exc())
    finally:
        # avoid sys.excepthook errors when piping output
        # http://stackoverflow.com/questions/7955138/addressing-sys-excepthook-error-in-bash-script
        try:
            sys.stdout.close()
        except:
            pass
        try:
            sys.stderr.close()
        except:
            pass


def convert(settings):
    """Perform file format conversion."""
    from .basic.devices import nullstream
    # OS-specific stdin/stdout selection
    # no stdin/stdout access allowed on packaged apps in OSX
    if platform.system() == b'Darwin':
        has_stdio = False
    elif platform.system() == b'Windows':
        has_stdio = True
    else:
        try:
            sys.stdin.isatty()
            sys.stdout.isatty()
            has_stdio = True
        except AttributeError:
            has_stdio = False
    mode, name_in, name_out = settings.get_converter_parameters()
    session = basic.Session(**settings.get_session_parameters())
    internal_disk = session.devices.internal_disk
    try:
        if name_in:
            prog_infile = session.files.open_native_or_basic(name_in, filetype='ABP', mode='I')
        elif has_stdio:
            # use StringIO buffer for seekability
            in_buffer = StringIO(sys.stdin.read())
            prog_infile = internal_disk.create_file_object(in_buffer, filetype='ABP', mode='I')
        else:
            # nothing to do
            return
        if name_out:
            prog_outfile = session.files.open_native_or_basic(name_out, filetype=mode, mode='O')
        elif has_stdio:
            prog_outfile = internal_disk.create_file_object(sys.stdout, filetype=mode, mode='O')
        else:
            # nothing to do
            return
        with prog_infile:
            session.program.load(prog_infile, rebuild_dict=False)
        with prog_outfile:
            session.program.save(prog_outfile)
    except basic.RunError as e:
        logging.error(e.message)
    except EnvironmentError as e:
        logging.error(str(e))

def start_basic(settings):
    """Start an interactive interpreter session."""
    from . import interface
    interface_name = settings.get_interface()
    audio_params = settings.get_audio_parameters()
    video_params = settings.get_video_parameters()
    launch_params = settings.get_launch_parameters()
    session_params = settings.get_session_parameters()
    state_file = settings.get_state_file()
    try:
        with basic.launch_session(session_params, state_file, **launch_params) as launcher:
            interface.run(
                    launcher.input_queue, launcher.video_queue,
                    launcher.tone_queue, launcher.message_queue,
                    interface_name, video_params, audio_params)
    except interface.InitFailed:
        logging.error('Failed to initialise interface.')
    except basic.RunError as e:
        # only runtime errors that occur on interpreter launch are caught here
        # e.g. "File not Found" for --load parameter
        logging.error(e.message)

def show_version(settings):
    """Show version with optional debugging details."""
    sys.stdout.write(basic.__version__ + '\n')
    if settings.get('debug'):
        show_platform_info()

def show_platform_info():
    """Show information about operating system and installed modules."""
    logging.info('\nPLATFORM')
    logging.info('os: %s %s %s', platform.system(), platform.processor(), platform.version())
    logging.info('python: %s %s', sys.version.replace('\n',''), ' '.join(platform.architecture()))
    logging.info('\nMODULES')
    # try numpy before pygame to avoid strange ImportError on FreeBSD
    modules = ('numpy', 'win32api', 'sdl2', 'pygame', 'curses', 'pexpect', 'serial', 'parallel')
    for module in modules:
        try:
            m = __import__(module)
        except ImportError:
            logging.info('%s: --', module)
        else:
            for version_attr in ('__version__', 'version', 'VERSION'):
                try:
                    version = getattr(m, version_attr)
                    logging.info('%s: %s', module, version)
                    break
                except AttributeError:
                    pass
            else:
                logging.info('available\n')
    if platform.system() != 'Windows':
        logging.info('\nEXTERNAL TOOLS')
        tools = ('lpr', 'paps', 'beep', 'xclip', 'xsel', 'pbcopy', 'pbpaste')
        for tool in tools:
            try:
                location = subprocess.check_output('command -v %s' % tool, shell=True).replace('\n','')
                logging.info('%s: %s', tool, location)
            except Exception as e:
                logging.info('%s: --', tool)


if __name__ == "__main__":
    main()