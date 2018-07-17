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

import os, sys, types
import re
import wx

# local imports

import utilities
from wx_utilities import *

# Types of Option record:

Flag        = 0  # Boolean value
Parm        = 1  # integer value
Stringparm  = 2  # string value
Group       = 3  # special case for layout only

# Indexes into option records (Flag, Parm, Stringparm, unless noted otherwise):

Id       = 0
Label_id = 1
Share    = 2
Depend   = 3
Type     = 4  # for all records
Name     = 5  # for all records
Value    = 6
Default  = 7
Range    = 8  # ignored for Flag
Tip      = 9

Column   = 6  # only for Group

# Option records:
#
# [id, label_id, share, depend, type, name, value, default, range, tooltip]
# [None, None, None, Group, group_name, column]

def id_to_option(id, options):
    "Given an option id, return the record."
    for opt in options:
        if opt[Type] in [Flag, Parm, Stringparm] and opt[Id] == id:
            return opt
    return None

def name_to_option(name, options):
    "Given an option name, return the record."
    for opt in options:
        if opt[Type] in [Flag, Parm, Stringparm] and opt[Name] == name:
            return opt
    return None

def nondefault_options(options, work):
    """Collect the options with nondefault values.  A list of triples
    is returned: (type, name, value).  We pass in a partially constructed
    list so that we can prevent duplicates."""
    for opt in options:
        if (opt[Type] in [Flag, Parm, Stringparm] and
            opt[Value] != opt[Default]):
            triple = (opt[Type], opt[Name], opt[Value])
            if not utilities.member(triple, work):
                work.append(triple)
    return work

def option_triples_contains_name(triples, name):
    for (_,n,_) in triples:
        if name == n:
            return True
    return False

def option_triples_to_string(triples):
    "Return a string that can be given to a LADR program (e.g., Prover9)."
    s = ''
    for (type,name,value) in triples:
        if type == Flag:
            if value:
                s += '  set(%s).\n' % name
            else:
                s += '  clear(%s).\n' % name
        elif type == Parm:
            s += '  assign(%s, %d).\n' % (name,value)
        elif type == Stringparm:
            s += '  assign(%s, %s).\n' % (name,value)
    return s

def print_sharing(opt):
    "For debugging."
    print '  option: %d %s %s' % (opt[Id], opt[Name], str(opt[Value]))
    for o in opt[Share]:
        print '        %d %s' % (o[Id], o[Name])

def update_label(opt):
    "Given an option, set the color of its label."
    label = wx.FindWindowById(opt[Label_id])
    if opt[Value] == opt[Default]:
        if len(opt[Depend]) > 0:
            label.SetForegroundColour('BLUE')
        else:
            label.SetForegroundColour('BLACK')
        label.Refresh()
    else:
        label.SetForegroundColour('RED')
        label.Refresh()

def update_option(opt, value):
    """Update the value of an option: (1) option record, (2) option label,
    (3) the widget.
    """
    opt[Value] = value
    update_label(opt)
    x = wx.FindWindowById(opt[Id])
    if opt[Type] in [Flag, Parm]:
        x.SetValue(value)
    elif opt[Type] == Stringparm:
        x.SetStringSelection(value)

def update_shared(opt):
    "Given an option record, update all of the other occurrences."
    for shared_opt in opt[Share]:
        if shared_opt != opt:
            update_option(shared_opt, opt[Value])

def update_dependent(opt):
    "Given an option record, update all of the dependent options."
    for (v1,dep_opt,v2) in opt[Depend]:
        if (v1 == opt[Value] or
            v1 == 'any' or
            (v1 == '>=0' and opt[Value] >= 0) or
            (v1 == '>0' and opt[Value] > 0)):
            if type(v2) == types.TupleType:
                (op, x) = v2
                if op == 'multiply':
                    update_option(dep_opt, opt[Value] * x)
                elif opt == 'add':
                    update_option(dep_opt, opt[Value] + x)
            else:
                update_option(dep_opt, v2)

            update_shared(dep_opt)
            update_dependent(dep_opt)

def link_options(opt1, opt2):
    """Given two option records, link them so that if one is uptdated,
    the other is updated in the same way.  The options must have the
    same type.  They can have different names, but that might be a
    bad idea."""
    if opt1 in opt2[Share] or opt2 in opt1[Share]:
        error_dialog('link_options, already linked?')
    elif opt1[Type] != opt2[Type]:
        error_dialog('link_options, different types')
    else:
        shared = opt1[Share] + opt2[Share]
        for opt in shared:
            opt[Share] = shared

def link_options_by_names(options1, options2, names):
    for name in names:
        opt1 = options1.name_to_opt(name)
        opt2 = options2.name_to_opt(name)
        if opt1 and opt2:
            link_options(opt1, opt2)
        else:
            error_dialog('link_options_by_names: not found')

class Options_panel(wx.Panel):
    def __init__(self, parent, title, logo_bitmap, options):

        self.options = options
        wx.Panel.__init__(self, parent)

        if logo_bitmap:
            heading = wx.StaticBitmap(self, -1, logo_bitmap)
        else:
            heading = wx.StaticText(self, -1, title) # title.replace(' ', '_'))
            font = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
            font.SetPointSize(font.GetPointSize()+2)
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            heading.SetFont(font)

        reset_btn = wx.Button(self, -1, 'Reset These to Defaults')
        self.Bind(wx.EVT_BUTTON, self.on_reset, reset_btn)

        groups = []

        for opt in self.options:
            if opt[Type] in [Flag, Parm, Stringparm]:

                if groups == []:
                    # in case the options are not divided into groups
                    box = wx.StaticBox(self, -1, '')
                    g_sizer = wx.GridBagSizer(5, 5)
                    groups.append((box, g_sizer, 'left'))
                    row = 0

                id = wx.NewId()
                label_id = wx.NewId()
                opt[Id] = id
                opt[Label_id] = label_id
                opt[Value] = opt[Default]
                opt[Share] = [opt]  # note: this creates a cyclic structure
                opt[Depend] = []

                label = wx.StaticText(self, label_id, opt[Name] + ':')

                if opt[Type] == Flag:
                    x = wx.CheckBox(self, id, '')
                    self.Bind(wx.EVT_CHECKBOX, self.on_change, x)
                    x.SetValue(opt[Default])
                    tip = opt[Tip]
                elif opt[Type] == Parm:
                    (min, max) = opt[Range]
                    x = wx.SpinCtrl(self,id,min=min,max=max,size=(75,-1))
                    self.Bind(wx.EVT_SPINCTRL, self.on_change, x)
                    x.SetValue(opt[Default])
                    tip = ('%s Range is [%d ... %d].' % (opt[Tip], min, max))
                else: # stringparm
                    x = wx.Choice(self, id, choices=opt[Range])
                    self.Bind(wx.EVT_CHOICE, self.on_change, x)
                    x.SetStringSelection(opt[Default])
                    tip = opt[Tip]
                    
                label.SetToolTipString(tip)
                if GTK():
                    # Tooltips on labels don't work in GTK.
                    # Large tooltips on widgets obscure choices in Mac.
                    x.SetToolTipString(tip)

                g_sizer.Add(label, (row,0), (1,1),
                            wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
                g_sizer.Add(x,     (row,1), (1,1),
                            wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
                row += 1

            elif opt[Type] == Group:
                box = wx.StaticBox(self, -1, opt[Name])
                g_sizer = wx.GridBagSizer(5, 5)
                groups.append((box, g_sizer, opt[Column]))
                row = 0
            else:
                # dividers? space?
                pass

        sizer       = wx.BoxSizer(wx.VERTICAL)
        opt_sizer   = wx.BoxSizer(wx.HORIZONTAL)
        left_sizer  = wx.BoxSizer(wx.VERTICAL)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        right_column_populated = False

        for (box, g_sizer, column) in groups:
            box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
            box_sizer.Add(g_sizer, 0, wx.ALL|wx.ALIGN_CENTER, 5)
            if column == 'left':
                left_sizer.Add(box_sizer, 0, wx.ALL|wx.GROW, 5)
            else:
                right_sizer.Add(box_sizer, 0, wx.ALL|wx.GROW, 5)
                right_column_populated = True

        opt_sizer.Add(left_sizer, 0, wx.ALL, 0)
        if right_column_populated:
            opt_sizer.Add(right_sizer, 0, wx.ALL, 0)
        sizer.Add(heading, 0, wx.ALIGN_CENTER, 5)
        sizer.Add(opt_sizer, 0, wx.ALIGN_CENTER, 5)
        sizer.Add(reset_btn, 0, wx.ALIGN_CENTER, 5)

        self.SetSizer(sizer)

    def on_change(self, evt):
        opt = id_to_option(evt.GetId(), self.options)
        x = evt.GetEventObject()
        if opt[Type] in [Flag, Parm]:
            opt[Value] = x.GetValue()
        elif opt[Type] == Stringparm:
            opt[Value] = x.GetStringSelection()
        update_label(opt)
        update_shared(opt)
        update_dependent(opt)

    def on_reset(self, evt):
        for opt in self.options:
            if (opt[Type] in [Flag, Parm, Stringparm] and
                opt[Value] != opt[Default]):

                update_option(opt, opt[Default])
                update_shared(opt)
        
# END class Options_panel(Panel)

class M4_options:

    # Nonstandard Mace4 Options:
    #   prolog_style_variables: shared with language tab and Prover9.
    #   max_seconds: shared with Mace4 run panel (not with Prover9 run panel).
    #              : different default, so always used.
    #   domain_size: partly meta.
    #   ignore_option_dependencies: "mandatory" option (always used).
    #
    # Omitted options:
    #   print_models_tabular, verbose, trace, iterate_up_to
    #   report_stderr, ignore_option_dependencies

    options = [

        [None, None, None, None, Group, 'Basic Options', 'left'],
        [None, None, None, None, Parm, 'domain_size', None, 0, [0,sys.maxint], 'Look for structures of this size only.'],
        [None, None, None, None, Parm, 'start_size', None, 2, [2,sys.maxint], 'Initial (smallest) domain size.'],
        [None, None, None, None, Parm, 'end_size', None, -1, [-1,sys.maxint], 'Final (largest) domain size (-1 means infinity).'],
        # [None, None, None, None, Parm, 'iterate_up_to', None, 10, [-1,sys.maxint], 'Final domain size.'],
        [None, None, None, None, Parm, 'increment', None, 1, [1,sys.maxint], 'Increment for next domain size (when end_size > start_size).'],
        [None, None, None, None, Stringparm, 'iterate', None, 'all', ['all', 'evens', 'odds', 'primes', 'nonprimes'], 'Domain sizes must satisfy this property.'],
        [None, None, None, None, Parm, 'max_models', None, 1, [-1,sys.maxint], 'Stop search at this number of models (-1 means no limit).'],
        [None, None, None, None, Parm, 'max_seconds', None, 60, [-1,sys.maxint], 'Overall time limit.'],
        [None, None, None, None, Parm, 'max_seconds_per', None, -1, [-1,sys.maxint], 'Time limit for each domain size.'],
        [None, None, None, None, Flag, 'prolog_style_variables', None, 0, None, 'Variables start with upper case instead of starting with u,v,w,x,y,z.'],

#        [None, None, None, None, Group, 'Output Options', 'left'],
#        [None, None, None, None, Flag, 'print_models', None, 1, None, 'Print models in standard form (for input to other LADR programs).'],
#        [None, None, None, None, Flag, 'print_models_tabular', None, 0, None, 'Print models in a tabular form.'],
#        [None, None, None, None, Flag, 'verbose', None, 0, None, 'Show more in the output file.'],
#        [None, None, None, None, Flag, 'trace', None, 0, None, 'USE THIS ONLY ON VERY SMALL SEARCHES!!'],

        [None, None, None, None, Group, 'Other Options', 'left'],
        [None, None, None, None, Flag, 'integer_ring', None, 0, None, 'Impose a ring structure (see sample input Ring-19.in).'],
        # [None, None, None, None, Flag, 'iterate_primes', None, 0, None, 'Search structures of prime size only.'],
        # [None, None, None, None, Flag, 'iterate_nonprimes', None, 0, None, 'Search structures of nonprime size only.'],
        [None, None, None, None, Flag, 'skolems_last', None, 0, None, 'Decide Skolem symbols last.'],
        [None, None, None, None, Parm, 'max_megs', None, 200, [-1,sys.maxint], 'Memory limit for Mace4 process (approximate).'],
        [None, None, None, None, Flag, 'print_models', None, 1, None, 'Output models that are found.'],

        [None, None, None, None, Group, 'Experimental Options', 'right'],
        [None, None, None, None, Flag, 'lnh', None, 1, None, 'Least Number Optimization.'],
        [None, None, None, None, Flag, 'negprop', None, 1, None, 'Apply negative propagation.'],
        [None, None, None, None, Flag, 'neg_assign', None, 1, None, 'Negative propagation is triggered by assignments.'],
        [None, None, None, None, Flag, 'neg_assign_near', None, 1, None, 'Negative propagation is triggered by near-assignments.'],
        [None, None, None, None, Flag, 'neg_elim', None, 1, None, 'Negative propagation is triggered by eliminations.'],
        [None, None, None, None, Flag, 'neg_elim_near', None, 1, None, 'Negative propagation is triggered by near-eliminations.'],
        [None, None, None, None, Parm, 'selection_order', None, 2, [0,2], '0: all, 1: concentric, 2: concentric-band.'],
        [None, None, None, None, Parm, 'selection_measure', None, 4, [0,4], '0: first, 1: most occurrences, 2: most propagations, 3: most contradictions, 4: fewest values.'],
        ]

    dependencies = [
        # (('print_models_tabular', True), ('print_models', False)),
        # (('print_models', True), ('print_models_tabular', False)),
        # (('iterate_primes', True), ('iterate_nonprimes', False)),
        # (('iterate_primes', True), ('iterate', 'primes')),
        # (('iterate_nonprimes', True), ('iterate_primes', False)),
        # (('iterate_nonprimes', True), ('iterate', 'nonprimes')),
        (('domain_size', 'any'), ('start_size', ('multiply', 1))),
        (('domain_size', 'any'), ('end_size', ('multiply', 1))),
        # (('iterate_up_to', 'any'), ('end_size', ('multiply', 1))),
        ]

    def __init__(self, parent, logo_bitmap):
        self.panel = wx.Panel(parent)
        self.options_panel = Options_panel(self.panel, 'Mace4 Options',
                                 logo_bitmap, self.options)
        # mark dependencies
        for ((n1,v1),(n2,v2)) in self.dependencies:
            o1 = self.name_to_opt(n1)
            o2 = self.name_to_opt(n2)
            if not o1:
                error_dialog('Mace4 option %s not found' % n1)
            elif not o2:
                error_dialog('Mace4 option %s not found' % n2)
            else:
                o1[Depend].append((v1, o2, v2))
                update_label(o1)

        # layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((0,0), 1)
        sizer.Add(self.options_panel, 0, wx.ALIGN_CENTER, 0)
        sizer.Add((0,0), 3)
        self.panel.SetSizer(sizer)

    def nondefaults(self):
        triples = nondefault_options(self.options, [])
        # always include max_seconds, because GUI default != program default.
        for name in ['max_seconds']:
            if not option_triples_contains_name(triples, name):
                opt = self.name_to_opt(name)
                if opt:
                    triples.append((opt[Type],opt[Name],opt[Value]))
        return triples

    def name_to_opt(self, name):
        return name_to_option(name, self.options)

    def share_external_option(self, external_opt):
        local_opt = self.name_to_opt(external_opt[Name])
        if not local_opt:
            error_dialog('share_external_option(M4), not found')
        else:
            link_options(local_opt, external_opt)
            # print 'External(M4):'; print_sharing(local_opt)
            # print '             '; print_sharing(external_opt)

    def reset(self):
        self.options_panel.on_reset(None)

# end class M4_options

class P9_options:

    # Nonstandard Mace4 Options:
    #   prolog_style_variables: shared with language tab and Prover9.
    #   max_seconds: shared with Prover9 run panel (not with Mace4 run panel).
    #              : different default, so always used.
    #   ignore_option_dependencies: "mandatory" option (always used).
    #
    # Omitted options:
    #   min_sos_limit, lrs_ticks, lrs_interval,
    #   default_parts, default_output, basic_paramodulation,
    #   echo_input, quiet, bell, report_stderr,
    #   ignore_option_dependencies

    option_sets = [

        ('Basic Options', 
        [
        [None, None, None, None, Parm, 'max_weight', None, 100, [-sys.maxint,sys.maxint], 'Discard inferred clauses with weight greater than this.'],
        [None, None, None, None, Parm, 'pick_given_ratio', None, -1, [-1,sys.maxint], 'Selection by (Weight : Age) ratio  (except for hints).'],
        [None, None, None, None, Stringparm, 'order', None, 'lpo', ['lpo', 'rpo', 'kbo'], 'Overall term ordering: Lexicographic Path Ordering (LPO), Recursive Path Ordering (RPO), Knuth-Bendix Ordering (KBO).  If the search fails with LPO, try KBO.'],
        [None, None, None, None, Stringparm, 'eq_defs', None, 'unfold', ['unfold', 'fold', 'pass'], 'Adjustment of term ordering, based on equational definitions in the input.\nUnfold: eliminate defined operations at the start of the search;\nFold: introduce the defined operation whenever possible;\nPass: let equational definitions be oriented by the term ordering.'],
        [None, None, None, None, Flag, 'expand_relational_defs', None, 0, None, 'Use relational definitions in the input to immediately expand occurrences of the defined relations in the input.'],
        [None, None, None, None, Flag, 'restrict_denials', None, 0, None, 'This flag restricts the application of inference rules when negative clauses are involved, with the goal of producing more direct (forward) proofs.  WARNING: this flag can block proofs.'],
        [None, None, None, None, Parm, 'max_seconds', None, 60, [-1,sys.maxint], 'Stop the search at this number of seconds (CPU, not wall clock).'],
        [None, None, None, None, Flag, 'prolog_style_variables', None, 0, None, 'Variables start with upper case instead of starting with u,v,w,x,y,z.'],
        ]),

        ('Meta Options', 
        [
        [None, None, None, None, Flag, 'auto', None, 1, None, 'Automatic Mode.  This flag simply sets or clears the following 4 flags.'],
        [None, None, None, None, Flag, 'auto_setup', None, 1, None, 'Processing before the search starts.'],
        [None, None, None, None, Flag, 'auto_limits', None, 1, None, 'Search limits.'],
        [None, None, None, None, Flag, 'auto_denials', None, 1, None, 'Automatic handling of denials (negative clauses in Horn sets).'],
        [None, None, None, None, Flag, 'auto_inference', None, 1, None, 'Automatic selection of inference rules, based on the input.'],
        [None, None, None, None, Flag, 'auto_process', None, 1, None, 'Processing of inferred clauses.'],
        [None, None, None, None, Flag, 'auto2', None, 0, None, 'Experimental automatic mode.'],
        [None, None, None, None, Flag, 'raw', None, 0, None, 'Raw (anti-automatic) mode.'],
        ]),

        ('Term Ordering', 
        [
        [None, None, None, None, Stringparm, 'order', None, 'lpo', ['lpo', 'rpo', 'kbo'], 'Overall term ordering: Lexicographic Path Ordering (LPO), Recursive Path Ordering (RPO), Knuth-Bendix Ordering (KBO).  If the search fails with LPO, try KBO.'],
        [None, None, None, None, Stringparm, 'eq_defs', None, 'unfold', ['unfold', 'fold', 'pass'], 'Adjustment of term ordering, based on equational definitions in the input.\nUnfold: eliminate defined operations at the start of the search;\nFold: introduce the defined operation whenever possible;\nPass: let equational definitions be oriented by the term ordering.'],
        [None, None, None, None, Flag, 'inverse_order', None, 1, None, 'Adjustment of term ordering, based on occurrences of inverse axioms in the input.'],
        ]),

        ('Limits', 
        [

        [None, None, None, None, Group, 'Search Limits', 'left'],
        [None, None, None, None, Parm, 'max_given', None, -1, [-1,sys.maxint], 'Stop the search at this number of given clauses.'],
        [None, None, None, None, Parm, 'max_kept', None, -1, [-1,sys.maxint], 'Stop the search at this number of kept clauses.'],
        [None, None, None, None, Parm, 'max_proofs', None, 1, [-1,sys.maxint], 'Stop the search at this number of proofs.'],
        [None, None, None, None, Parm, 'max_megs', None, 200, [-1,sys.maxint], 'Stop the search when the process has used about this amount of memory.'],
        [None, None, None, None, Parm, 'max_seconds', None, 60, [-1,sys.maxint], 'Stop the search at this number of seconds (CPU, not wall clock).'],
        [None, None, None, None, Parm, 'max_minutes', None, -1, [-1,sys.maxint], ''],
        [None, None, None, None, Parm, 'max_hours', None, -1, [-1,sys.maxint], ''],
        [None, None, None, None, Parm, 'max_days', None, -1, [-1,sys.maxint], ''],

        [None, None, None, None, Group, 'Limits on Kept Clauses', 'right'],
        [None, None, None, None, Parm, 'max_weight', None, 100, [-sys.maxint,sys.maxint], 'Discard inferred clauses with weight greater than this.'],
        [None, None, None, None, Parm, 'max_depth', None, -1, [-1,sys.maxint], 'Discard inferred clauses with depth greater than this.'],
        [None, None, None, None, Parm, 'max_literals', None, -1, [-1,sys.maxint], 'Discard inferred clauses with more literals than this.'],
        [None, None, None, None, Parm, 'max_vars', None, -1, [-1,sys.maxint], 'Discard inferred clauses with more variables than this.'],

        [None, None, None, None, Group, 'Sos Control', 'right'],
        [None, None, None, None, Parm, 'sos_limit', None, 20000, [-1,sys.maxint], 'Limit on the size of the SOS list (the list of clauses that have been kept, but not yet selected as given clauses).  As the SOS fills up, a heuristic is used to discards new clauses that are unlikely to be used due to this limit.'],
#       [None, None, None, None, Parm, 'min_sos_limit', None, 0, [0,sys.maxint], 'Unused'],
#       [None, None, None, None, Parm, 'lrs_interval', None, 50, [1,sys.maxint], 'Limited resource heuristic: '],
#       [None, None, None, None, Parm, 'lrs_ticks', None, -1, [-1,sys.maxint], 'Limited resource heuristic: '],
        ]),

        ('Search Prep', 
        [
        [None, None, None, None, Flag, 'expand_relational_defs', None, 0, None, 'Use relational definitions in the input to immediately expand occurrences of the defined relations in the input.'],
        [None, None, None, None, Flag, 'dont_flip_input', None, 0, None, 'Do not flip input equalities, even if they violate the term ordering.  Using this flag can cause nontermination of rewriting.  It is usually better to adjust the term ordering instead.'],
        [None, None, None, None, Flag, 'process_initial_sos', None, 1, None, 'Treat input clauses as if they were inferred; exceptions are the application of max_weight, max_level, max_vars, and max_literals.'],
        [None, None, None, None, Flag, 'sort_initial_sos', None, 0, None, 'Sort the initial assumptions.  The order is largely  arbitrary.'],
        [None, None, None, None, Flag, 'predicate_elim', None, 1, None, 'Try to eliminate predicate (relation) symbols before the search starts.'],
        [None, None, None, None, Parm, 'fold_denial_max', None, 0, [-1,sys.maxint], ''],
        ]),

        ('Goals/Denials', 
        [
        [None, None, None, None, Flag, 'restrict_denials', None, 0, None, 'This flag applies only to Horn sets.  It restricts the application of inference rules when negative clauses are involved, with the goal of producing more direct (forward) proofs.'],
        [None, None, None, None, Flag, 'reuse_denials', None, 0, None, 'This flag allows multiple proofs of goals.  (Applies to Horn sets only.'],
        ]),

        ('Select Given', 
        [

        [None, None, None, None, Group, 'Selection Ratio', 'left'],
        [None, None, None, None, Parm, 'hints_part', None, sys.maxint, [0,sys.maxint], 'Component for clauses that match hint.'],
        [None, None, None, None, Parm, 'age_part', None, 1, [0,sys.maxint], 'Component for the oldest clauses.'],
        [None, None, None, None, Parm, 'weight_part', None, 0, [0,sys.maxint], 'Component for the lightest clauses.'],
        [None, None, None, None, Parm, 'false_part', None, 4, [0,sys.maxint], 'Component for the lightest false (w.r.t. an interpretation) clauses.'],
        [None, None, None, None, Parm, 'true_part', None, 4, [0,sys.maxint], 'Component for the lightest true (w.r.t. an interpretation) clauses.'],
        [None, None, None, None, Parm, 'random_part', None, 0, [0,sys.maxint], 'Component for random clauses.'],

        [None, None, None, None, Group, 'Meta Options', 'right'],
        [None, None, None, None, Parm, 'pick_given_ratio', None, -1, [-1,sys.maxint], 'Selection by (Weight : Age) ratio  (except for hints).'],
        [None, None, None, None, Flag, 'breadth_first', None, 0, None, 'Selection by age only (except for hints).'],
        [None, None, None, None, Flag, 'lightest_first', None, 0, None, 'Selection by weight only (except for hints).'],
        [None, None, None, None, Flag, 'random_given', None, 0, None, 'Random selection (except for hints).'],
#       [None, None, None, None, Flag, 'default_parts', None, 1, None, ''],

        [None, None, None, None, Group, 'Semantic Guidance', 'left'],
        [None, None, None, None, Stringparm, 'multiple_interps', None, 'false_in_all', ['false_in_all', 'false_in_some'], 'Semantics with multiple interpretaions: determines how clauses are marked as "false".'],
        [None, None, None, None, Parm, 'eval_limit', None, 1024, [-1,sys.maxint], 'Limit on the number of ground instances for evaluation in an explicit interpretation (for semantic guidance).'],

        [None, None, None, None, Group, 'Others', 'right'],
        [None, None, None, None, Flag, 'input_sos_first', None, 1, None, 'Before starting with selection ratio, select input clauses.'],
        [None, None, None, None, Flag, 'breadth_first_hints', None, 0, None, 'For hints component, select by age rather than by weight.'],
        ]),

        ('Inference Rules', 
        [

        [None, None, None, None, Group, 'Ordinary Rules', 'left'],
        [None, None, None, None, Flag, 'binary_resolution', None, 0, None, 'Binary resolution (not necessarily positive).'],
        [None, None, None, None, Flag, 'neg_binary_resolution', None, 0, None, 'Negative binary resolution.'],
        [None, None, None, None, Flag, 'hyper_resolution', None, 0, None, 'Synonym for pos_hyperresolution.'],
        [None, None, None, None, Flag, 'pos_hyper_resolution', None, 0, None, 'Positive hyperresolution.'],
        [None, None, None, None, Flag, 'neg_hyper_resolution', None, 0, None, 'Negative hyperresolution.'],
        [None, None, None, None, Flag, 'ur_resolution', None, 0, None, 'Unit resulting resolution.'],
        [None, None, None, None, Flag, 'pos_ur_resolution', None, 0, None, 'Positive-unit resulting resolution.'],
        [None, None, None, None, Flag, 'neg_ur_resolution', None, 0, None, 'Negative-unit resulting resolution.'],
        [None, None, None, None, Flag, 'paramodulation', None, 0, None, 'The inference rule for equality.'],

        [None, None, None, None, Group, 'Other Rules', 'left'],
        [None, None, None, None, Parm, 'new_constants', None, 0, [-1,sys.maxint], 'If > 0, introduce new constants when equations such as x*x\'=y*y\' are derived.  The value of this parameter is a limit on the number of times the rule will be applied.'],
        [None, None, None, None, Flag, 'factor', None, 0, None, ''],

        [None, None, None, None, Group, 'General Restrictions', 'right'],
        [None, None, None, None, Stringparm, 'literal_selection', None, 'max_negative', ['max_negative', 'all_negative', 'none'], 'Method for determining which literals in a multi-literal clause are eligible for resolution or paramodulation.'],

        [None, None, None, None, Group, 'Resolution Restrictions', 'right'],
        [None, None, None, None, Flag, 'ordered_res', None, 1, None, 'Resolved literals in one or more parents must be maximal in the clause.  (Does not apply to UR resolution.)'],
        [None, None, None, None, Flag, 'check_res_instances', None, 0, None, 'The maximality checks are done after the application of the unifier for the inference.'],
        [None, None, None, None, Flag, 'initial_nuclei', None, 0, None, 'For hyperresolution and UR resolution the nucleus for the inference must be an initial clause (this restriction can block all proofs).'],
        [None, None, None, None, Parm, 'ur_nucleus_limit', None, -1, [-1,sys.maxint], 'The nucleus for each UR-resolution inference can have at most this many  literals.'],

        [None, None, None, None, Group, 'Paramodulation Restrictions', 'right'],
        [None, None, None, None, Flag, 'ordered_para', None, 1, None, 'For paramodulation inferences, one or both parents must be maximal in the clause.'],
        [None, None, None, None, Flag, 'check_para_instances', None, 0, None, 'The maximality checks are done after the application of the unifier for the inference.'],
        [None, None, None, None, Flag, 'para_from_vars', None, 1, None, 'Paramodulation is allowed from variables (not allowing can block all proofs)..'],
        [None, None, None, None, Flag, 'para_units_only', None, 0, None, 'Paramodulation is applied to unit clauses only (this restriction can block all proofs).'],
#       [None, None, None, None, Flag, 'basic_paramodulation', None, 0, None, ''],
        [None, None, None, None, Parm, 'para_lit_limit', None, -1, [-1,sys.maxint], 'Paramodulation is not applied to clauses with more than this number of literals (using this restriction can block all proofs).'],
        ]),

        ('Rewriting', 
        [

        [None, None, None, None, Group, 'Term Rewriting Limits', 'left'],
        [None, None, None, None, Parm, 'demod_step_limit', None, 1000, [-1,sys.maxint], 'When rewriting derived clauses, apply at most this many rewrite steps.  Under most settings, rewriting is guaranteed to terminate, but it can be intractable.'],
        [None, None, None, None, Parm, 'demod_size_limit', None, 1000, [-1,sys.maxint], 'When rewriting derived clauses, stop if the term being rewritten has more than this many symbols.'],

        [None, None, None, None, Group, 'Lex-Dependent Rewriting', 'right'],
        [None, None, None, None, Flag, 'lex_dep_demod', None, 1, None, 'Apply non-orientable equations as rewrite rules if the instance used for the rewrite is orientable.'],
        [None, None, None, None, Flag, 'lex_dep_demod_sane', None, 1, None, 'This is a restriction on lex_dep_demod.  A non-orientable equation can be used for rewriting only if the two sides have the same number of symbols.'],
        [None, None, None, None, Parm, 'lex_dep_demod_lim', None, 11, [-1,sys.maxint], 'This is a restriction on lex_dep_demod.  A non-orientable equation can be used for rewriting only if it has fewer than this number of symbols.'],
        [None, None, None, None, Flag, 'lex_order_vars', None, 0, None, 'Incorporate (uninstantiated) variables into the term ordering, treating them as constants.  For example, x*y < y*x.  This cuts down the search, but it can block all proofs.'],

        [None, None, None, None, Group, 'Others', 'left'],
        [None, None, None, None, Flag, 'back_demod', None, 1, None, 'Use newly derived equations to rewrite old clauses.'],
        [None, None, None, None, Flag, 'unit_deletion', None, 0, None, 'Remove literals from newly derived clauses with old unit clauses, and use newly derived unit clauses to remove literals from old clauses.'],
        [None, None, None, None, Flag, 'cac_redundancy', None, 1, None, 'Eliminate some redundancy when there are commutative or associative-commutative operations.'],
        ]),

        ('Weighting', 
        [

        [None, None, None, None, Group, 'Symbol Weights', 'left'],
        [None, None, None, None, Parm, 'variable_weight', None, 1, [-sys.maxint,sys.maxint], 'Weight of variables .'],
        [None, None, None, None, Parm, 'constant_weight', None, 1, [-sys.maxint,sys.maxint], 'Default weight of constants.'],
        [None, None, None, None, Parm, 'not_weight', None, 0, [-sys.maxint,sys.maxint], 'Weight of the negation symbol.'],
        [None, None, None, None, Parm, 'or_weight', None, 0, [-sys.maxint,sys.maxint], 'Weight of the disjunction symbol.'],
        [None, None, None, None, Parm, 'sk_constant_weight', None, 1, [-sys.maxint,sys.maxint], 'Weight of Skolem constants.  This option can be useful, because Skolem constants cannot appear in weighting rules.'],
        [None, None, None, None, Parm, 'prop_atom_weight', None, 1, [-sys.maxint,sys.maxint], 'Weight of propositional atoms.'],

        [None, None, None, None, Group, 'Penalties', 'right'],
        [None, None, None, None, Parm, 'skolem_penalty', None, 1, [0,sys.maxint], 'If a term contains a (non-constant) Skolem function, its weight is multiplied by this value.'],
        [None, None, None, None, Parm, 'nest_penalty', None, 0, [0,sys.maxint], 'For each nest of two identical function symbols, e.g., f(f(x,y),z), this value is added tot he weight of the term.'],
        [None, None, None, None, Parm, 'depth_penalty', None, 0, [-sys.maxint,sys.maxint], 'After the weight of clause C is calculated, its weight is increased by depth(C) * this_value.'],
        [None, None, None, None, Parm, 'var_penalty', None, 0, [-sys.maxint,sys.maxint], 'After the weight of clause C is calculated, its weight is increased by number_of_vars(C) * this_value.'],

        [None, None, None, None, Group, 'Others', 'right'],
        [None, None, None, None, Parm, 'default_weight', None, sys.maxint, [-sys.maxint,sys.maxint], ''],
        ]),

        ('Process Inferred', 
        [
        [None, None, None, None, Flag, 'safe_unit_conflict', None, 0, None, 'In some cases, a proof may be missed because a newly-derived clause is deleted by a limit such as max_weight.  This flag eliminates some of those cases.'],
        [None, None, None, None, Flag, 'back_subsume', None, 1, None, 'When a newly-derived clause C is kept, discard all old clauses that are subsumed by C.'],
        [None, None, None, None, Parm, 'backsub_check', None, 500, [-1,sys.maxint], 'At this number of given clauses, disable back subsumption if less than 5% of kept clauses have been back subsumed.'],
        ]),

        ('Input/Output', 
        [
#       [None, None, None, None, Flag, 'echo_input', None, 1, None, ''],
#       [None, None, None, None, Flag, 'bell', None, 1, None, ''],
#       [None, None, None, None, Flag, 'quiet', None, 0, None, ''],
        [None, None, None, None, Flag, 'print_initial_clauses', None, 1, None, 'Show clauses after preprocessing, before the start of the search.'],
        [None, None, None, None, Flag, 'print_given', None, 1, None, 'Print clauses when they are selected as given clauses.  These clauses say a lot about the progress of the search.'],
        [None, None, None, None, Flag, 'print_gen', None, 0, None, 'Print all newly-derived clauses.  This flag can cause an enormous amount of output for nontrivial searches.'],
        [None, None, None, None, Flag, 'print_kept', None, 0, None, 'Print newly-derived clauses if they pass the retention tests.'],
        [None, None, None, None, Flag, 'print_labeled', None, 0, None, 'Print newly-kept clauses that have labels.'],
        [None, None, None, None, Flag, 'print_proofs', None, 1, None, 'Print all proofs that are found.'],
#       [None, None, None, None, Flag, 'default_output', None, 1, None, ''],
        [None, None, None, None, Flag, 'print_clause_properties', None, 0, None, 'When a clause is printed, show some if its syntactic properties (mostly for debugging).'],
        [None, None, None, None, Stringparm, 'stats', None, 'lots', ['none', 'some', 'lots', 'all'], 'How many statistics should be printed at the end of the search and in "reports".'],
        [None, None, None, None, Parm, 'report', None, -1, [-1,sys.maxint], 'Output a statistics report every n seconds.'],
#       [None, None, None, None, Parm, 'report_stderr', None, -1, [-1,sys.maxint], ''],
        [None, None, None, None, Flag, 'prolog_style_variables', None, 0, None, 'Variables start with upper case instead of starting with u,v,w,x,y,z.'],
        ]),

        ('Hints', 
        [
        [None, None, None, None, Flag, 'limit_hint_matchers', None, 0, None, 'Apply the parameters max_weight, max_vars, max_depth, and max_literals to clauses that match hints (as well as to those that do not match hints).'],
        [None, None, None, None, Flag, 'collect_hint_labels', None, 0, None, 'When equivalent hints are input, only the first is kept.  This flag causes any labels on the discarded hints to be appended to the retained hint.'],
        [None, None, None, None, Flag, 'degrade_hints', None, 1, None, 'The more times a hint is matched, the less its effect becomes.'],
        [None, None, None, None, Flag, 'back_demod_hints', None, 1, None, 'This flag causes hints, as well as ordinary clauses, to be rewritten by newly-derived equations.'],
        ]),

        ('Other Options', 
        [
        [None, None, None, None, Parm, 'random_seed', None, 0, [-1,sys.maxint], 'Seed for random number generation.'],
        ]),
        ]

    dependencies = [
        (('max_minutes', '>=0'), ('max_seconds', ('multiply', 60))),
        (('max_hours', '>=0'), ('max_seconds', ('multiply', 3600))),
        (('max_days', '>=0'), ('max_seconds', ('multiply', 86400))),
        (('para_units_only', True), ('para_lit_limit', 1)),
        (('hyper_resolution', True), ('pos_hyper_resolution', True)),
        (('hyper_resolution', False), ('pos_hyper_resolution', False)),
        (('ur_resolution', True), ('pos_ur_resolution', True)),
        (('ur_resolution', True), ('neg_ur_resolution', True)),
        (('ur_resolution', False), ('pos_ur_resolution', False)),
        (('ur_resolution', False), ('neg_ur_resolution', False)),
        (('lex_dep_demod', False), ('lex_dep_demod_lim', 0)),
        (('lex_dep_demod', True), ('lex_dep_demod_lim', 11)),
        (('lightest_first', True), ('weight_part', 1)),
        (('lightest_first', True), ('age_part', 0)),
        (('lightest_first', True), ('false_part', 0)),
        (('lightest_first', True), ('true_part', 0)),
        (('lightest_first', True), ('random_part', 0)),
        (('random_given', True), ('weight_part', 0)),
        (('random_given', True), ('age_part', 0)),
        (('random_given', True), ('false_part', 0)),
        (('random_given', True), ('true_part', 0)),
        (('random_given', True), ('random_part', 1)),
        (('pick_given_ratio', '>=0'), ('age_part', 1)),
        (('pick_given_ratio', '>=0'), ('weight_part', ('multiply', 1))),
        (('pick_given_ratio', '>=0'), ('false_part', 0)),
        (('pick_given_ratio', '>=0'), ('true_part', 0)),
        (('pick_given_ratio', '>=0'), ('random_part', 0)),
        (('breadth_first', True), ('age_part', 1)),
        (('breadth_first', True), ('weight_part', 0)),
        (('breadth_first', True), ('false_part', 0)),
        (('breadth_first', True), ('true_part', 0)),
        (('breadth_first', True), ('random_part', 0)),
#        (('default_parts', True), ('hints_part', sys.maxint)),
#        (('default_parts', True), ('age_part', 1)),
#        (('default_parts', True), ('weight_part', 0)),
#        (('default_parts', True), ('false_part', 4)),
#        (('default_parts', True), ('true_part', 4)),
#        (('default_parts', True), ('random_part', 0)),
#        (('default_parts', False), ('hints_part', 0)),
#        (('default_parts', False), ('age_part', 0)),
#        (('default_parts', False), ('weight_part', 0)),
#        (('default_parts', False), ('false_part', 0)),
#        (('default_parts', False), ('true_part', 0)),
#        (('default_parts', False), ('random_part', 0)),
#        (('default_output', True), ('quiet', False)),
#        (('default_output', True), ('echo_input', True)),
#        (('default_output', True), ('print_initial_clauses', True)),
#        (('default_output', True), ('print_given', True)),
#        (('default_output', True), ('print_proofs', True)),
#        (('default_output', True), ('stats', 'lots')),
#        (('default_output', True), ('print_kept', False)),
#        (('default_output', True), ('print_gen', False)),
        (('auto_setup', True), ('predicate_elim', True)),
        (('auto_setup', True), ('eq_defs', 'unfold')),
        (('auto_setup', False), ('predicate_elim', False)),
        (('auto_setup', False), ('eq_defs', 'pass')),
        (('auto_limits', True), ('max_weight', 100)),
        (('auto_limits', True), ('sos_limit', 20000)),
        (('auto_limits', False), ('max_weight', sys.maxint)),
        (('auto_limits', False), ('sos_limit', -1)),
        (('auto', True), ('auto_inference', True)),
        (('auto', True), ('auto_setup', True)),
        (('auto', True), ('auto_limits', True)),
        (('auto', True), ('auto_denials', True)),
        (('auto', True), ('auto_process', True)),
        (('auto', False), ('auto_inference', False)),
        (('auto', False), ('auto_setup', False)),
        (('auto', False), ('auto_limits', False)),
        (('auto', False), ('auto_denials', False)),
        (('auto', False), ('auto_process', False)),
        (('auto2', True), ('auto', True)),
        (('auto2', True), ('new_constants', 1)),
        (('auto2', True), ('fold_denial_max', 3)),
        (('auto2', True), ('max_weight', 200)),
        (('auto2', True), ('nest_penalty', 1)),
        (('auto2', True), ('skolem_penalty', 3)),
        (('auto2', True), ('sk_constant_weight', 0)),
        (('auto2', True), ('prop_atom_weight', 5)),
        (('auto2', True), ('sort_initial_sos', True)),
        (('auto2', True), ('sos_limit', -1)),
#        (('auto2', True), ('lrs_ticks', 3000)),
        (('auto2', True), ('max_megs', 400)),
        (('auto2', True), ('stats', 'some')),
#        (('auto2', True), ('echo_input', False)),
#        (('auto2', True), ('quiet', True)),
        (('auto2', True), ('print_initial_clauses', False)),
        (('auto2', True), ('print_given', False)),

        (('raw', True), ('auto', False)),
        (('raw', True), ('ordered_res', False)),
        (('raw', True), ('ordered_para', False)),
        (('raw', True), ('literal_selection', 'none')),
        (('raw', True), ('backsub_check', sys.maxint)),
        (('raw', True), ('lightest_first', True)),
        (('raw', True), ('cac_redundancy', False)),

        ]

    dependencies += [
        # These are extra dependencies so that the GUI makes sense.
        # They are irrelevant to Prover9 because they change meta options only,
        # which Prover9 will ignore.
        
        (('breadth_first', True), ('lightest_first', False)),
        (('breadth_first', True), ('random_given', False)),
        (('breadth_first', True), ('pick_given_ratio', -1)),
        (('lightest_first', True), ('breadth_first', False)),
        (('lightest_first', True), ('random_given', False)),
        (('lightest_first', True), ('pick_given_ratio', -1)),
        (('random_given', True), ('lightest_first', False)),
        (('random_given', True), ('breadth_first', False)),
        (('random_given', True), ('pick_given_ratio', -1)),
        (('pick_given_ratio', '>=0'), ('breadth_first', False)),
        (('pick_given_ratio', '>=0'), ('lightest_first', False)),
        (('pick_given_ratio', '>=0'), ('random_given', False)),

        (('max_minutes', '>=0'), ('max_hours', -1)),
        (('max_minutes', '>=0'), ('max_days', -1)),
        (('max_hours', '>=0'), ('max_minutes', -1)),
        (('max_hours', '>=0'), ('max_days', -1)),
        (('max_days', '>=0'), ('max_minutes', -1)),
        (('max_days', '>=0'), ('max_hours', -1))
        ]

    def __init__(self, parent):
        """ Use the option_set table to build a dictionary, indexed by
        set name, of (hidden) options panels.
        """
        panels = {}
        for (name,options) in self.option_sets:
            panels[name] = Options_panel(parent, name, None, options)
            panels[name].Show(False)  # start out hidden

        # find and mark the shared options
        for (_,options1) in self.option_sets:
            for opt1 in options1:
                if opt1[Type] in [Flag, Parm, Stringparm]:
                    for (_,options2) in self.option_sets:
                        for opt2 in options2:
                            if (opt1[Type] == opt2[Type] and
                                opt1[Name] == opt2[Name] and
                                not opt1 in opt2[Share]):

                                link_options(opt1, opt2)
                                # print 'Share:'; print_sharing(opt1)
                                # print '      '; print_sharing(opt2)

        # mark dependencies
        for ((n1,v1),(n2,v2)) in self.dependencies:
            o1 = self.name_to_opt(n1)
            o2 = self.name_to_opt(n2)
            if not o1:
                error_dialog('Prover9 option %s not found' % n1)
            elif not o2:
                error_dialog('Prover9 option %s not found' % n2)
            else:
                for o in o1[Share]:
                    o[Depend].append((v1, o2, v2))
                    update_label(o)

        self.panels = panels

    def optionset_names(self):
        result = []
        for (name,_) in self.option_sets:
            result.append(name)
        return result

    def nondefaults(self):
        triples = []
        # order:  1,2,3,...,0  (because "basic" should be last)
        for (_,options) in self.option_sets[1:]:
            triples = nondefault_options(options, triples)
        triples = nondefault_options(self.option_sets[0][1], triples)
        # always include max_seconds, because GUI default is not program default
        if not option_triples_contains_name(triples, 'max_seconds'):
            opt = self.name_to_opt('max_seconds')
            if opt:
                triples.append((opt[Type],opt[Name],opt[Value]))
        return triples

    def name_to_opt(self, name):
        for (_,options) in self.option_sets:
            opt = name_to_option(name, options)
            if opt:
                return opt
        return None

    def share_external_option(self, external_opt):
        local_opt = self.name_to_opt(external_opt[Name])
        if not local_opt:
            error_dialog('share_external_option(P4), not found')
        else:
            link_options(local_opt, external_opt)
            # print 'External(P9):'; print_sharing(local_opt)
            # print '             '; print_sharing(external_opt)

    def reset(self):
        for key in self.panels.keys():
            self.panels[key].on_reset(None)

# end class P9_options

def set_options(opt_str, opt_class, handle_dep = True):

    not_handled = ''

    pat_flag = '(set|clear)\s*\(\s*([a-z0-9_]+)\s*\)'  # without period
    r_flag = re.compile(pat_flag)

    pat_parm = 'assign\s*\(\s*([a-z0-9_]+)\s*,\s*([a-z0-9_-]+)\s*\)'  # without period
    r_parm = re.compile(pat_parm)

    opts = opt_str.split('.')[:-1]  # no option after last period
    for command in opts:
        m = r_flag.match(command)
        if m:
            (op,name) = m.groups()
            opt = opt_class.name_to_opt(name)
            if opt and opt[Type] == Flag:
                update_option(opt, op == 'set')
                update_shared(opt)
                if handle_dep:
                    update_dependent(opt)
            else:
                not_handled += command + '.\n'
        else:
            m = r_parm.match(command)
            if m:
                (name,string_val) = m.groups()
                try:
                    value = int(string_val)
                    opt_type = Parm
                except:
                    value = string_val
                    opt_type = Stringparm
                opt = opt_class.name_to_opt(name)
                if opt and opt[Type] == opt_type:
                    update_option(opt, value)
                    update_shared(opt)
                    if handle_dep:
                        update_dependent(opt)
                else:
                    not_handled += command + '.\n'
            else:
                not_handled += command + '.\n'
    return not_handled
    
def opt_intersect(s1, s2):
    t1 = s1.split('.\n')
    t2 = s2.split('.\n')
    y = utilities.intersect(t1, t2)
    return '.\n'.join(y)
    
def set_options_either(opt_str, class1, class2, handle_dep = True):
    x1 = set_options(opt_str, class1, handle_dep)
    x2 = set_options(opt_str, class2, handle_dep)
    # (x1 intersect x2) was handled by neither
    return opt_intersect(x1,x2)
