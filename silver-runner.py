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

from os.path import join, dirname
from sicds.app import SiCDSApp
from sicds.config import SiCDSConfig
from yaml import load, YAMLError

configfilename = 'config.yaml'
configpath = join(dirname(__file__), configfilename)
try:
    with open(configpath) as f:
        config = load(f)
        config = SiCDSConfig(config)
        application = SiCDSApp(
            config.keys, config.superkey, config.store, config.loggers)
except IOError:
    print('Could not open file {0}'.format(configpath))
except YAMLError:
    print('Could not parse yaml')
