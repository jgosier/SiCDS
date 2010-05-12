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

from sicds.base import BaseLogger
from sys import stdout

class NullLogger(BaseLogger):
    '''
    Stub logger. Just throws entries away.
    '''
    def log(self, *args, **kw):
        pass

class TmpLogger(BaseLogger):
    '''
    Stores log records in memory. Records are lost when the object is destroyed.
    '''
    def __init__(self, *args, **kw):
        self._log_records = []

    def _add_log_record(self, record):
        self._log_records.append(record)

    def iterlog(self):
        return iter(self._log_records)

class FileLogger(BaseLogger):
    '''
    Opens a file at the path specified in ``url`` and logs entries to it.
    '''
    def __init__(self, url):
        self.file = open(url.path, 'a')

    def _add_log_record(self, entry):
        self.file.write('{0}\n'.format(entry))

class StdOutLogger(FileLogger):
    '''
    Logs to stdout.
    '''
    def __init__(self, *args):
        self.file = stdout
