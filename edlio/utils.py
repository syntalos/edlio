# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Matthias Klumpp <matthias@tenstral.net>
#
# Licensed under the GNU Lesser General Public License Version 3
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the license, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

import random
import string


def sanitize_name(name: str) -> str:
    '''
    Sanitize a string for use as an EDL unit name,
    by stripping or replacing invalid characters.

    Parameters
    ----------
    name
        A string to sanitize.

    Returns
    -------
    str
        The sanitized name.
    '''
    if not name:
        return None
    s = ''.join(filter(lambda x: x in string.printable, name))
    s = s.replace('/', '_').replace('\\', '_').replace(':', '')
    # TODO: Replace Windows' reserved names
    if not s:
        s = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return s
