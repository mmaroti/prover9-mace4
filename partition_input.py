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

#!/usr/bin/python

import re, sys

import utilities

def in_span(i, spans):
    for (start,end) in spans:
        if i >= start and i < end:
            return True
    return False

def norm(s):
    x = s.strip()  # remove leading and trailing whitespace
    if x == '':
        return x
    else:
        return '\n' + x + '\n'

def split1(str, pat):
    r = re.compile(pat)
    comments = utilities.comment_spans(str)  # starts and ends of comments
    matched = other = ''  # matched and not_matched parts
    other_start = 0
    m = r.search(str, 0)
    while m:
        if not in_span(m.start(), comments):
            other   += str[other_start:m.start()]
            matched += str[m.start():m.end()]
            other_start = m.end()
        m = r.search(str, m.end())
    other += str[other_start:]
    return (matched, other)

def split2(str, start_pat, end_pat, remove_patterns=False):
    r1 = re.compile(start_pat)
    r2 = re.compile(end_pat)
    comments = utilities.comment_spans(str)  # starts and ends of comments
    matched = other = ''
    other_start = 0
    m1 = r1.search(str, 0)
    while m1:
        if not in_span(m1.start(), comments):
            m2 = r2.search(str, m1.end())
            while m2 and in_span(m2.start(), comments):
                m2 = r2.search(str, m2.end())
            match_end = m2.end() if m2 else len(str)
            other   += str[other_start:m1.start()]
            if remove_patterns:
                keep_start = m1.end()
                keep_end = m2.start() if m2 else len(str)
            else:
                keep_start = m1.start()
                keep_end = m2.end() if m2 else len(str)
            matched += str[keep_start:keep_end]
            next = other_start = match_end
        else:
            next = m1.end()
        m1 = r1.search(str, next)
    other += str[other_start:]
    return (matched, other)

def partition(input):

    work = input

    # if(Prover9). ... end_if.

    start_pat = 'if\s*\(\s*Prover9\s*\)\s*\.'
    end_pat   = 'end_if\s*\.'
    (p9, work) = split2(work, start_pat, end_pat, remove_patterns = True)

    # if(Prover9). ... end_if.

    start_pat = 'if\s*\(\s*Mace4\s*\)\s*\.'
    end_pat   = 'end_if\s*\.'
    (m4, work) = split2(work, start_pat, end_pat, remove_patterns = True)

    # assumptions|sos

    start_pat = 'formulas\s*\(\s*(assumptions|sos)\s*\)\s*\.'
    end_pat   = 'end_of_list\s*\.'
    (assumps, work) = split2(work, start_pat, end_pat, remove_patterns = True)

    # goals

    start_pat = 'formulas\s*\(\s*goals\s*\)\s*\.'
    end_pat   = 'end_of_list\s*\.'
    (goals, work) = split2(work, start_pat, end_pat, remove_patterns = True)

    # flags, parm, stringparms

    pat = '((set|clear)\s*\(\s*[a-z0-9_]+\s*\)\s*\.|assign\s*\(\s*[a-z0-9_]+\s*,\s*[a-z0-9_-]+\s*\)\s*\.)'
    (opt, work) = split1(work, pat)

    # op, redeclare

    pat = '(op\s*\([^,()]+,[^,()]+,[^,()]+\)\s*\.|redeclare\s*\([^,()]+,[^,()]+\)\s*\.)'
    (language, work) = split1(work, pat)

    # Clean up and return

    work = work.strip() + '\n'
    return (p9, m4, assumps, goals, opt, language, work)
                                       
# end def partition(input):

def extract_options(input):

    work = input

    # flags, parm, stringparms

    pat = '((set|clear)\s*\(\s*[a-z0-9_]+\s*\)\s*\.|assign\s*\(\s*[a-z0-9_-]+\s*,\s*[a-z0-9_]+\s*\)\s*\.)'
    (opt, work) = split1(work, pat)

    work = work.strip() + '\n'

    return (opt, work)
                                       
# end def extract_options(input):

if __name__ == '__main__':

    input = sys.stdin.read()

    (p9,m4,a,g,opt,other) = partition(input)

    print '% p9:\n' + p9
    print '% m4:\n' + m4
    print '% assumptions:\n' + a
    print '% goals:\n' + g
    print '% options:\n' + opt
    print '% other:\n' + other
