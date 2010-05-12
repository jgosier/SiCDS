#!/usr/bin/env python
# Copyright (C) 2010 Ushahidi Inc. <jon@ushahidi.com>,
# Joshua Bronson <jabronson@gmail.com>, and contributors
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301
# USA

from sicds.app import getconfig, makeapp
import sys

def startshell(locals_={}, header='SiCDS Interactive Shell\n', footer=''):
    if not footer and locals_:
        footer = '\nThe following variables are available:\n  {0}'.format(
            ', '.join(locals_))
    try:
        # try to use IPython if possible
        from IPython.Shell import IPShellEmbed
        shell = IPShellEmbed(argv=sys.argv)
        banner = header + shell.IP.BANNER + footer
        shell.set_banner(banner)
        shell(local_ns=locals_, global_ns={})
    except ImportError:
        import code
        pyver = 'Python %s' % sys.version
        banner = header +  pyver + footer
        shell = code.InteractiveConsole(locals=locals_)
        try:
            import readline
        except ImportError:
            pass
        try:
            shell.interact(banner)
        finally:
            pass
    
def main():
    config = getconfig()
    app = makeapp(config)
    locals_ = dict(config=config, app=app)
    startshell(locals_=locals_)

if __name__ == '__main__':
    main()
