#     Copyright (C) 2007 William McCune
#
#     This file is part of the LADR Deduction Library.
#
#     The LADR Deduction Library is free software; you can redistribute it
#     and/or modify it under the terms of the GNU General Public License
#     as published by the Free Software Foundation; either version 2 of the
#     License, or (at your option) any later version.
#
#     The LADR Deduction Library is distributed in the hope that it will be
#     useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with the LADR Deduction Library; if not, write to the Free Software
#     Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA.
#

# system imports

import wx, subprocess

# Platforms.  We'll assume GTK, and test for Win32 and Mac when necessary

def Win32():
    return wx.Platform=='__WXMSW__'

def Mac():
    return wx.Platform=='__WXMAC__'

def GTK():
    return wx.Platform=='__WXGTK__'

def Mac_ppc():
    if not Mac():
        return False
    else:
        try:
            arch = subprocess.Popen(['arch'],
                                    stdout=subprocess.PIPE).communicate()[0]
        except:
            arch = '??'
        return arch.strip() == 'ppc'

if Win32():
    import win32api, win32process

