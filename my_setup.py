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

import os, sys
import re
import wx

# local imports

import partition_input
import utilities
from files import *
from control import *
from platforms import *
from wx_utilities import *
from options import *

# When saving an input file, a few comments are added; when
# opening a saved input file, those comments are removed.

Comment_banner  = '% Saved by.*\n'
Comment_opt_dep = '% GUI handles dependencies'
Comment_lang    = '% Language Options'
Comment_p9_opt  = '% Options for Prover9'
Comment_m4_opt  = '% Options for Mace4'
Comment_p9_add  = '% Additional input for Prover9'
Comment_m4_add  = '% Additional input for Mace4'

All_added_comments = [Comment_banner, Comment_opt_dep, Comment_lang,
                      Comment_p9_opt, Comment_m4_opt,
                      Comment_p9_add, Comment_p9_add]

class Input_panel(wx.Panel):

    def __init__(self, parent, title, auto_highlight):
        self.title = title
        self.have_new_text = False
        wx.Panel.__init__(self, parent)

        title_display = title + ':'
        width = max_width([title_display], self) + 10  # +10 prevents wrap
        text = wx.StaticText(self, -1, title + ':', size=(width,-1))
        wff_btn = wx.Button(self, -1, 'Well Formed?')
        wff_btn.SetToolTipString(
            'Check syntax of %s.  If there are multiple '
            'errors, only the first will be shown.' % title)
        self.Bind(wx.EVT_BUTTON, self.well_formed_check, wff_btn)
        self.hilite_btn = wx.Button(self, -1, 'Highlight')
        self.hilite_btn.SetToolTipString(
            'Color comments and attributes in this box now. '
            'This button is a hack because on some platforms, '
            'the automatic highlighting causes an annoying '
            'flash every few seconds.')
        self.Bind(wx.EVT_BUTTON, self.on_hilite, self.hilite_btn)
        clear_btn = wx.Button(self, -1, 'Clear')
        clear_btn.SetToolTipString('Clear ' + title)
        self.Bind(wx.EVT_BUTTON, self.clear, clear_btn)

        sub_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sub_sizer.Add(text, 1, wx.ALIGN_BOTTOM, 0)
        sub_sizer.Add(self.hilite_btn, 0, wx.ALL, 3)
        sub_sizer.Add(wff_btn, 0, wx.ALL, 3)
        sub_sizer.Add(clear_btn, 0, wx.ALL, 3)

        self.ed = wx.TextCtrl(self,  # Win32 neews TE_RICH2 for color
                              style=wx.TE_MULTILINE|wx.HSCROLL|wx.TE_RICH2)
        if Win32():
            self.ed.Bind(wx.EVT_CHAR, self.on_char, self.ed)  # bad on Mac()
        else:
            self.ed.Bind(wx.EVT_TEXT, self.on_text, self.ed)  # bad on Win32()

        self.ed.SetFont(to_top(self).box_font)
        self.ed.SetDefaultStyle(wx.TextAttr('BLACK','WHITE',
                                            to_top(self).box_font))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sub_sizer, 0, wx.ALL|wx.GROW, 3)
        sizer.Add(self.ed, 1, wx.ALL|wx.GROW, 3)
        self.SetSizer(sizer)

        self.timer = None
        if auto_highlight:
            self.start_auto_highlight()
        else:
            self.hilite_btn.Show(True)
            self.Layout()

    def start_auto_highlight(self):
        if self.timer:
            error_dialog('start_auto_highlight: timer alreay exists')
        else:
            self.timer = wx.Timer(self, -1)
            wx.EVT_TIMER(self, self.timer.GetId(), self.check_highlight)
            self.timer.Start(2000)  # check every 2 seconds
            self.hilite_btn.Show(False)
        
    def stop_auto_highlight(self):
        if self.timer:
            self.timer.Stop()
            self.timer = None
            self.hilite_btn.Show(True)
            self.Layout()
        else:
            error_dialog('stop_auto_highlight: timer not found')

    def on_hilite(self, evt):
        self.highlight()
        if Mac():
            # There should be a better way to do this.
            self.Show(False)
            self.Show(True)

    def well_formed_check(self, evt):
        if self.title == 'Assumptions':
            head = '\nformulas(assumptions).\n'
            tail = '\nend_of_list.\n'
        elif self.title == 'Goals':
            head = '\nformulas(goals).\n'
            tail = '\nend_of_list.\n'
        else:
            head = tail = ''
        
        text = self.ed.GetValue()
        if self.title == 'Language Options':
            lang_opt = ''  # this may be temporary, until language panel is done
        else:
            lang_opt = to_top(self).setup.language.get_language_input()

        input = ('%s%s%s%s' % (lang_opt, head, text, tail))

        (exit, message, error) = syntax_check(input)

        if exit == 'Okay':
            info_dialog('This part of the input looks good!')
        elif exit == 'Input_Error':
            if error:
                start = text.find(error)
                if (start >= 0):
                    end = start + len(error)
                    self.ed.SetStyle(start, end,
                                     wx.TextAttr('RED',
                                                 wx.Colour(200,200,255)))
            error_dialog('%s\n%s' % (message,error if error else ''))
        else:
            frame = Text_frame(self, to_top(self).box_font,
                               'Error Output',
                               message, saveas=False)
            frame.Show(True)
            error_dialog('Unknown error; see the \'Error Output\' window.')

    def clear(self, evt):
        self.ed.Clear()

    def highlight(self):
        str = self.ed.GetValue()
        # reset to all black text
        self.ed.SetStyle(0, self.ed.GetLastPosition(),
                         wx.TextAttr('BLACK', 'WHITE', to_top(self).box_font))

        # attributes:
        spans = utilities.pattern_spans('#[^.\n]*[.\n]', str)
        for (start,end) in spans:
            self.ed.SetStyle(start, end, wx.TextAttr(wx.Colour(0,0,200)))

        font = self.ed.GetFont()
        font.SetStyle(wx.FONTSTYLE_ITALIC)

        # comments (line and block)
        spans = utilities.comment_spans(str)
        for (start,end) in spans:
            self.ed.SetStyle(start, end, wx.TextAttr(wx.Colour(0,160,0),
                                                     font=font))

        # following needed on mac to undo italics (???)
        self.ed.SetDefaultStyle(wx.TextAttr('BLACK','WHITE',
                                            to_top(self).box_font))
        
    def on_text(self, evt):
        # This gets called whenever the text is changed (EVT_TEXT)
        self.have_new_text = True

    def on_char(self, evt):
        # This gets called whenever a character is inserted (EVT_CHAR)
        self.have_new_text = True
        evt.Skip() # allows normal processing of char

    def check_highlight(self, evt):
        # This gets called periodically.
        if self.have_new_text:
            self.have_new_text = False
            self.timer.Stop()
            self.highlight()
            self.timer.Start(2000)

# END class Input_panel(Panel)

class P9_options_panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        panel1 = wx.Panel(self)
        panel1.SetBackgroundColour('white')
        self.panel2 = wx.Panel(self)

        self.type = ['Basic Options', 'All Options']

        logo_bitmap = Prover9().logo_bitmap()
        if logo_bitmap:
            heading = wx.StaticBitmap(panel1, -1, logo_bitmap)
        else:
            heading = wx.StaticText(panel1, -1, 'Prover9')

        self.rb1 = wx.RadioBox(panel1, -1, '', choices=self.type,
                               majorDimension=1, style=wx.RA_SPECIFY_COLS)
        self.rb1.SetToolTip(wx.ToolTip(
            'Show only basic options, or enable access to all options. '
            'Note that "Basic Options" is a subset of "All Options", and '
            'different groups in "All Options" may share options. '
            'Changing one of the widgets for a shared option will '
            'cause other widgets for that option to be updated in kind.'))

        self.panels = P9_options(self.panel2)  # dictionary indexed by sets
        self.sets = self.panels.optionset_names() # 'Basic Options' is first

        self.rb2 = wx.RadioBox(panel1, -1, 'Option Groups',
                               choices=self.sets[1:],  # all but first
                               majorDimension = 1, style=wx.RA_SPECIFY_COLS)
        self.rb2.SetToolTip(wx.ToolTip('These are all of the Prover9 '
                                       'options, separated into groups.'))
        self.rb2.Enable(False)

        self.Bind(wx.EVT_RADIOBOX, self.handle_rb1, self.rb1)
        self.Bind(wx.EVT_RADIOBOX, self.handle_rb2, self.rb2)

        self.reset = wx.Button(panel1, -1, 'Reset All to Defaults')
        self.Bind(wx.EVT_BUTTON, self.on_reset, self.reset)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((1,10), 0)
        # sizer.Add(heading, 0, wx.LEFT|wx.RIGHT|wx.GROW|wx.ALIGN_CENTER, 10)
        sizer.Add(heading, 0, wx.ALL|wx.ALIGN_CENTER, 0)
        sizer.Add((1,5), 0)
        sizer.Add(self.rb1, 0, wx.LEFT|wx.RIGHT|wx.GROW, 10)
        sizer.Add((1,10), 0)
        sizer.Add(self.rb2, 0, wx.LEFT|wx.RIGHT|wx.GROW, 10)
        sizer.Add((1,10), 0)
        sizer.Add(self.reset, 0, wx.LEFT|wx.RIGHT|wx.GROW, 10)
        panel1.SetSizer(sizer)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(panel1, 0, wx.ALL|wx.GROW, 3)
        sizer.Add(self.panel2, 1, wx.ALL|wx.GROW, 3)
        self.SetSizer(sizer)

        self.current_option_set = None
        self.switch_options(0)

    def switch_options(self, item):
        if self.current_option_set:
            self.current_option_set.Show(False)
        self.current_option_set = self.panels.panels[self.sets[item]]
        self.current_option_set.Show(True)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((0,0), 1)
        sizer.Add(self.current_option_set, 0, wx.ALIGN_CENTER, 10)
        sizer.Add((0,0), 3)
        self.panel2.SetSizer(sizer)
        self.panel2.Layout()

    def handle_rb1(self, evt):
        item = evt.GetInt()
        if self.type[item] == 'Basic Options':
            self.switch_options(0)
            self.rb2.Enable(False)
        else:
            item = self.rb2.GetSelection()
            self.switch_options(item+1)
            self.rb2.Enable(True)
        self.Layout()         # rearrange children

    def handle_rb2(self, evt):
        item = evt.GetInt()
        self.switch_options(item+1)

    def on_reset(self, evt):
        self.panels.reset()

# END class P9_options_panel(Panel)

class Language_panel(wx.Panel):
    def __init__(self, parent, options):
        wx.Panel.__init__(self, parent)

        # Directions

        temp_help = (
        'Some day, this panel will have widgets for specifying all of '
        'the language options.  Until then, if you know the '
        'Prover9/Mace4 commands for doing so, you can give them '
        'in the following text box.  The commands include '
        '"op", for specifying infix/prefix/postfix and precedence, '
        'and "redeclare", for changing the the symbols with built-in '
        'semantics.  For example,\n\n'
        '   op(450, infix, "@").\n'
        '   redeclare(implication, IMPLIES).')

        # directions = wx.StaticText(self, -1, temp_help)
        directions = wx.TextCtrl(self, -1, temp_help, style=wx.TE_MULTILINE)

        # Prolog-Style Variables (Shared with other options widgets)
        
        id = wx.NewId()
        label_id = wx.NewId()
        opt = copy.deepcopy(options.name_to_opt('prolog_style_variables'))
        if opt:
            opt[Id] = id
            opt[Label_id] = id  # we're not using a separate label here
            opt[Share] = [opt]  # note circular structure
            options.share_external_option(opt)
            self.prolog_cb = wx.CheckBox(self, id, 'Prolog-Style Variables')
            self.prolog_cb.SetValue(opt[Default])
            tip = opt[Tip]
        else:
            error_dialog('error sharing prolog_style_variables option')
            self.prolog_cb = wx.CheckBox(self, id, 'Prolog-Style Variables')
            self.prolog_cb.SetValue(False)
            tip = ''

        self.prolog_cb_opt = opt

        self.Bind(wx.EVT_CHECKBOX, self.on_prolog, self.prolog_cb)
        self.prolog_cb.SetToolTipString(tip)

        # Text Box

        self.input = Input_panel(self, 'Language Options',
                                 to_top(self).auto_highlight())

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.prolog_cb, 0, wx.ALL|wx.GROW, 10)
        sizer.Add(directions, 0, wx.ALL|wx.GROW, 10)
        sizer.Add(self.input, 1, wx.ALL|wx.GROW, 1)

        self.SetSizer(sizer)

    def on_prolog(self, evt):
        if self.prolog_cb_opt:
            self.prolog_cb_opt[Value] = self.prolog_cb.GetValue()
            update_label(self.prolog_cb_opt)
            update_shared(self.prolog_cb_opt)

    def get_language_input(self):
        return self.input.ed.GetValue()

# end class Language_panel(wx.Panel):

class Setup_tabs(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent,
                             style=wx.NO_BORDER|wx.FULL_REPAINT_ON_RESIZE|wx.NB_NOPAGETHEME)

        # self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_changed)

        # Formulas Tab

        self.formulas = wx.SplitterWindow(self, -1)
        self.assumps = Input_panel(self.formulas, 'Assumptions',
                                 to_top(self).auto_highlight())
        self.goals   = Input_panel(self.formulas, 'Goals',
                                 to_top(self).auto_highlight())

        self.formulas.SplitHorizontally(self.assumps, self.goals)
        self.formulas.SetSashGravity(0.75)
        self.formulas.SetMinimumPaneSize(150)
        if Mac() or Win32():
            self.formulas.SetSashPosition(450)

        # Prover9 Options Tab

        self.p9_options = P9_options_panel(self)

        # Mace4 Options Tab

        self.m4_options = M4_options(self, Mace4().logo_bitmap())

        # self.m4_options.output_transformed()
        # self.p9_options.panels.output_transformed()

        link_options_by_names(self.p9_options.panels, self.m4_options,
                              ['prolog_style_variables'])

        # Additional Input Tab

        self.add = wx.SplitterWindow(self, -1)
        self.add_p9 = Input_panel(self.add, 'Additional Input for Prover9',
                                 to_top(self).auto_highlight())
        self.add_m4 = Input_panel(self.add, 'Additional Input for Mace4',
                                 to_top(self).auto_highlight())
        self.add.SplitHorizontally(self.add_p9, self.add_m4)
                                   
        self.add.SetSashGravity(0.75)
        self.add.SetMinimumPaneSize(150)
        if Mac() or Win32():
            self.formulas.SetSashPosition(450)

        # Language Tab (construction assumes options tabs exist)

        self.language = Language_panel(self, self.m4_options)

        # Add tabs to Notebook

        self.AddPage(self.language, 'Language Options')
        self.AddPage(self.formulas, 'Formulas')
        self.AddPage(self.p9_options, 'Prover9 Options')
        self.AddPage(self.m4_options.panel, 'Mace4 Options')
        self.AddPage(self.add, 'Additional Input')

        self.SetSelection(1)  # Start with second page (Formulas) showing

        # Following is used when we have to update all boxes.
        
        self.text_boxes = [self.assumps, self.goals,
                           self.add_p9, self.add_m4,
                           self.language.input]

    def update_font(self, font):
        for box in self.text_boxes:
            box.ed.SetFont(font)
            box.highlight()

        if Mac():
            # There should be a better way to do this.
            self.Show(False)
            self.Show(True)

    def reset(self):
        for box in self.text_boxes:
            box.ed.Clear()

        self.p9_options.panels.reset()
        self.m4_options.reset()

    def assemble_input(self):
        language = self.language.get_language_input().strip() + '\n'
        assumps = self.assumps.ed.GetValue().strip() + '\n'
        goals = self.goals.ed.GetValue().strip() + '\n'

        p9_add = self.add_p9.ed.GetValue().strip() + '\n'
        m4_add = self.add_m4.ed.GetValue().strip() + '\n'

        p9_triples = self.p9_options.panels.nondefaults()
        m4_triples = self.m4_options.nondefaults()

        p9_opt = option_triples_to_string(p9_triples)
        m4_opt = option_triples_to_string(m4_triples)

        input = 'set(ignore_option_dependencies). %s\n\n' % Comment_opt_dep
        if language.strip() != '':
            input += '%s\n\n%s\n' % (Comment_lang,language)
        if p9_opt.strip() != '':
            input += 'if(Prover9). %s\n%send_if.\n\n' % (Comment_p9_opt,p9_opt)
        if m4_opt.strip() != '':
            input += 'if(Mace4).   %s\n%send_if.\n\n' % (Comment_m4_opt,m4_opt)
        if p9_add.strip() != '':
            input += 'if(Prover9). %s\n%send_if.\n\n' % (Comment_p9_add,p9_add)
        if m4_add.strip() != '':
            input += 'if(Mace4).   %s\n%send_if.\n\n' % (Comment_m4_add,m4_add)

        input += '\nformulas(assumptions).\n\n%s\nend_of_list.\n\n' % assumps
        input += '\nformulas(goals).\n\n%s\nend_of_list.\n\n' % goals
        input = re.sub('\n\s*\n', '\n\n', input)  # collapse blank lines
        return input

    def store_input(self, input):

        input = utilities.remove_reg_exprs(All_added_comments, input)

        (p9,m4,assumps,goals,opt,lang,other) = partition_input.partition(input)

        # Take the part from the if(Prover9), and split those (also Mace4)

        (p9_opt, p9_other) = partition_input.extract_options(p9)
        (m4_opt, m4_other) = partition_input.extract_options(m4)

        # If there is an option set(ignore_option_dependencies), remove it
        # and tell set_options() to ignore dependencies while putting the
        # options into the GUI.

        r = re.compile('set\s*\(\s*ignore_option_dependencies\s*\)\s*\.')
        if r.match(opt):
            opt = r.sub('', opt)
            handle_dep = False
        else:
            handle_dep = True

        p9_opt_x = set_options(p9_opt, self.p9_options.panels,
                               handle_dep = handle_dep)
        if p9_opt_x != '':
            info_dialog('The following options from the if(Prover9) section'
                        ' of the input were not recognized.  They have been'
                        ' added to the "Additional Input for Prover9" box.\n\n'
                        + p9_opt_x)

        m4_opt_x = set_options(m4_opt, self.m4_options, handle_dep=handle_dep)
        if m4_opt_x != '':
            info_dialog('The following options from the if(Mace4) section'
                        ' of the input were not recognized.  They have been'
                        ' added to the "Additional Input for Mace4" box.\n\n'
                        + m4_opt_x)

        opt_x = set_options_either(opt, self.p9_options.panels,
                                   self.m4_options, handle_dep = handle_dep)

        if opt_x != '':
            info_dialog('The following options from the '
                        ' input file were not recognized.  They have been'
                        ' added to the "Additional Input for Prover9" box.\n\n'
                        + opt_x)

        self.language.input.ed.AppendText(lang.replace('.', '.\n'))
        self.assumps.ed.AppendText(assumps)
        self.goals.ed.AppendText(goals)
        self.add_p9.ed.AppendText(p9_opt_x + p9_other + opt_x + other)
        self.add_m4.ed.AppendText(m4_opt_x + m4_other)

        for box in self.text_boxes:
            box.highlight()
            box.ed.ShowPosition(0)

        self.SetSelection(1)  # Start with second page (Formulas) showing

    def store_new_input(self, input, version):
        self.reset()  # clears everything in setup tabs

        if version:
            if input.find('Saved by Prover9-Mace4') < 0:
                info_dialog('The file being opened was not created by'
                            ' Prover9-Mace4.  Therefore, it might not run'
                            ' exactly the same here as with the command-line'
                            ' versions of Prover9 or Mace4, because'
                            ' Prover9-Mace4 can rearrange the input, and'
                            ' dependent options are handled differently.')
            elif input.find('Saved by Prover9-Mace4 Version %s' % version) < 0:
                info_dialog('The file being opened was created with a'
                            ' different version of Prover9-Mace4.  This is'
                            ' usually okay, but it might cause problems if'
                            ' the underlying programs Prover9 or Mace4'
                            ' have changed.')
        self.store_input(input)

    def append_input(self, input):
        self.store_input(input)

    def on_changed(self, evt):
        sel = evt.GetSelection()
        if sel == 0:
            # Tried to redraw so that all text will appear.  Failed.
            pass

    def start_auto_highlight(self):
        for box in self.text_boxes:
            box.start_auto_highlight()

    def stop_auto_highlight(self):
        for box in self.text_boxes:
            box.stop_auto_highlight()

# END class Setup_tabs(Notebook)
                                       
