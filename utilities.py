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

import re

def grep(pattern, lines):
    result = []
    for line in lines:
        if re.search(pattern, line):
            result.append(line)
    return result

def grep_last(pattern, lines):
    result = None
    for line in lines:
        if re.search(pattern, line):
            result = line
    return result

def pattern_spans(pattern, string):
    r = re.compile(pattern)
    spans = []
    m = r.search(string, 0)
    while m:
        spans.append(m.span())
        m = r.search(string, m.end())
    return spans

def comment_spans(s):
    i = 0
    spans = []
    length = len(s)
    while i < length:
        if s[i] == '%':
            start = i
            if s[i:i+6] == '%BEGIN':
                # block comment
                while i <= length and s[i-4:i] != 'END%':
                    i += 1
                end = min(i,length)
            else:
                # line comment
                while i < length and s[i] != '\n':
                    i += 1
                end = i  # ok if string ends without \n
            spans.append((start,end))
        else:
            i += 1
    return spans
                    
def member(x, b):
    if b == []:
        return False
    elif x == b[0]:
        return True
    else:
        return member(x, b[1:])

def intersect(a, b):
    if a == []:
        return []
    elif member(a[0], b):
        return [a[0]] + intersect(a[1:], b)
    else:
        return intersect(a[1:], b)

def remove_reg_exprs(exprs, str):
    pat = '|'.join(exprs)
    r = re.compile(pat)
    str = r.sub('', str)
    return str

    
        
