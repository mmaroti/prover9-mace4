#!/usr/bin/python

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
from platforms import *
from wx_utilities import *
from my_setup import *
from control import *

Program_name = 'Prover9-Mace4'
Program_version = '0.5'
Program_date = 'December 2007'

Banner = '%s Version %s, %s' % (Program_name, Program_version, Program_date)

Help = """
1. Introduction

This is a brief introduction. Better help will be available
in the next release.

Prover9-Mace4 is a front end to the programs Prover9 (which
searches for proofs) and Mace4 (which searches for finite
models and counterexamples).  Prover9 and Mace4 have been
around for a few years, and they are ordinarily run on
a command line (without a GUI).  This introduction is
mainly about the GUI.  For detailed information on Prover9
and Mace4, see http://www.cs.unm.edu/~mccune/prover9.

The GUI is intended primarily for new users and casual
users.  Power users might not be very interested, but
they might find the displays of the options useful.

Recommendations for new users who know first-order or
equational logic:

  (1) Look at some of the examples in 'File -> Sample Inputs'.
      This will give an idea of the formula syntax.

  (2) Experiment by modifying the sample inputs, both formulas
      and options.  Note:

       (a) each formula ends with a period,
       (b) variables start with (lower case) u--z,
       (c) when in doubt, include parentheses.

  (3) Start from scratch, enter some assumptions and goals,
      and try to prove or disprove some things.

Although there are many options, much can be accomplished
with just Assumptions and Goals.

2. The Main Window

The main window is divided into the Setup panel on the
left, and the Run panel on the right.

2.1. The Setup Panel

The Setup panel is for specifying the input to Prover9 and/or
Mace4.  The 'Language Options' and 'Formulas' tabs are
used for both Prover9 and Mace4.  The 'Additional Input'
tab is for some esoteric kinds of input, and it can be ignored
by most users.

2.1.1. Formulas

A few basic points about formulas (see the HTML manual for details).

  + Do not include the Prover9/Mace4 constructs
    'formulas(assumptions)' or 'end_of_list'.
  + Each formula ends with a period.
  + Variables start with (lower case) u--z.
  + The basic logic connectives are:  - | & -> <-> all exists.
  + Universal quantifiers at the outermost level can be omitted.
  + When in doubt, include parentheses.  The programs usually
    output formulas with the minimum number of parentheses,
    so you can look in the output to see how you could have
    written the formulas.

Goals

Prover9 always proves by contradiction, and Mace4 looks
for counterexamples by searching for a model of the negation
of the conjecture.  Each program puts the negation of the
goals together with the assumptions and then searches.
If there are no goals, Prover9 simply looks for a contradiction
among the assumptions, and Mace4 looks for a model of the
assumptions.  It's also acceptable to have no assumptions,
with the entire statement of the conjecture as a goal.

Multiple Goals  

If there are multiple goals, Prover9 assumes you want a
separate proof of each goal, and it will try to prove
all of them.

Mace4 searches for counterexamples to the goals.  If
there are multiple goals, Mace4 looks for structures
that falsify all of the goals.

From the HTML manual: 'If there is more than one formula in
the goals list, each must be a positive universal
conjunctive formula; that is, a formula constructed from
atomic formulas, universal quantification, and conjunction
only.'

From a logical point of view, multiple goals are a
disjunction.  Consider two goals 'P. Q.'.  If Prover9
proves either of them, it outputs a proof.  Mace4
looks for a counterexample by searching for a model
of the negation of the disjunction; that is, a model
in which both are false.

If there is any doubt about the meaning of multiple goals,
the user can combine them into a single goal with the
conjunction or disjunction operations.

2.1.2. Options Panels

The options panels contain most of the options accepted
by the programs Prover9 and Mace4, with the same names.
The GUI's default values are the same as the programs'
default values.  When an option has a non-default value,
its name is shown in red.

There can be more than one widget (button or entry box)
associated with an option.  For example, each of the Prover9
'Basic Options' also appears somewhere in 'All Options'.
When one occurrence is changed, all other occurrences are
updated.

Many of the integer-valued options specify limits and have
a range [-1, ..., some-big-number].  In these cases, -1 means
'no limit'.

Prover9 and Mace4 have a notion of 'dependent option':
changing some of the options causes others to be changed
automatically.  For example, when Prover9 receives
'set(breadth_first).', it automatically changes the parameters
'age_part', 'weight_part', 'true_part', and 'false_part'.
The GUI is aware of the dependent options.  Options
with dependencies are shown in blue, and when such an option
is changed, the dependent options are changed automatically.
Because the GUI handles dependent options, it tells
Prover9 and Mace4 to ignore option dependencies.

2.1.2.  Additional Input Panels

These can be used for Prover9 input that cannot yet be
specified with the widgets, including:

  + weighting rules,
  + KBO weights,
  + function_order and relation_order,
  + actions,
  + interpretations for semantic guidance, and
  + lists of hints (you must include 'formulas(hints).' and
    'end_of_list.').

2.2. The Run Panel

The 'Show Current Input' button at the top of the Run panel
displays the data in the Setup panel as a text file.  This
is the input that will be given to Prover9 or Mace4 when one
of the 'Start' buttons is pressed.

If you want to try for both a proof and a counterexample,
the two programs can be run concurrently (and they should
take advantage of a multiple-core processor if you have one).

The 'Info' button shows a few statistics about the search.
It can be pressed during a search or after a search has
finished.

When the program stops, the 'Show-Save' button will be enabled.
he 'Show-Save' button gives you

  (1) the input that was given to the program (not the
      'Current Input', which might have changed since
      the program was started),
  (2) the program's full output, and
  (3) if successful, proof(s) or counterexample(s).

These data will be available until the another search is started.

2.3. The Menu Bar

2.3.1.  The File Menu

'Clear Entire Setup Menu' resets everything to the initial
state: language options, formulas, options, and additional
input.

The 'Open' and 'Save' selections work as in many other
applications.  These apply to Prover9/Mace4 input files.
(The text that is 'Save'd is the same as the text displayed
by the 'Show Current Input' button in the Run panel.)
The 'Append To Input' selection is similar to the 'Open'
selection, except that existing state (formulas, options)
is not cleared first.

'Open Input File ...' should work not only on previously
'Save'd files, but also on most other Prover9 or Mace4 input
files.  Comments in 'Open'ed files are not handled well:
most comments that are not inside of formula lists appear
in 'Additional Input'.

3. Proofs and Models/Counterexamples

When a proof or model/counterexample is found, it is shown
in a separate window.  Several additional operations can
be applied to the proofs or models/counterexamples.

3.1.  Proofs

Proofs found by Prover9 are usually hard to understand
and longer then necessary.  (We are conducting research on
several methods to humanize and simplify proofs.)

For now, there is a button "Reformat...", in the Proof window,
which allows the user to transform the proof in several simple
ways.  See the HTML manual, page "Prooftrans".

3.2. Models/Counterexamples

Models/Counterexamples found by Mace4 are given as function
and relation tables.  The underlying set for domain_size=n
is always {0,...,n-1}.

There is a button "Reformat...", in the Model/Counterexample window,
which allows the user to transform the model in several simple
ways.  See the HTML manual, page "Interpformat".

3.2.1.  Isofilter.

If the user asks for more than one model (option max_models),
Mace4 will keep searching until it finds that number of models
or until it reaches some other limit.  When Mace4 finds multiple
models, many are likely to be isomorphic to others.  A separate
program 'Isofilter' can be used to remove isomorphic models.

Isofilter has several options.  One can specify the operations
that are checked for isomorphism, and one can specify the
operations that are output.  (For example, if one of the operations
is a Skolem function from an existentially quantified variable,
one might wish to omit it for checking and for output.)

One can select the the algorithm Isofilter will use:
"Occurrence Profiles" (the default) or "Canonical Forms".
They should produce the same results, but the relative
performance depends on the application.

"""

Feedback = ('\nFeedback to mccune@cs.unm.edu.  We are '
            'especially interested in making this system '
            'accessible and friendly to new users.\n')

Things_to_do = """
To Do:

 + If both Prover9 and Mace4 are running, and one
   succeeds, the user should be reminded that the
   other job should probably be killed.
 + Before quit, remind user to save unsaved input.
 + Output directly to TextCtrl, so user can see givens?
 + Comments in 'Opened' files are not handled well.
 + Remember preferences for future sessions.
 + Help

Problems:

 + Mac: On a G3 iBook (10.3.9), text boxes with a lot of text
   (>32K?) don't show scrollbars.  (All of the text really is
   there, so it can be 'Save'd.)  No problem on Intel Mac (10.4.?).
 + Mac: On the Show/Save button, the tooltip hides the selections!
 + Win32: If the Prover9 or Mace4 process is run at
   normal priority, the GUI response is poor, so Prover9
   and Mace4 are run at lower priority (Win32 only).
 + Automatic syntax highlighting causes annoying flashes
   every few seconds on Win32.  Double-buffering might help.
 + The 'Well Formed?' button sometimes highlights the wrong
   substring.  (A string can be ill-formed in one context
   and well-formed in another, and the highlighter shows
   only the first occurrence).
 
"""

class Main_frame(wx.Frame):
    """
    This is the primary Frame.
    """
    def __init__(self, parent, title, size, pos):
        wx.Frame.__init__(self, parent, -1, title, size=size, pos=pos)
        self.saved_client_size = None
        self.saved_client_pos = None
        self.current_path = None
        self.probs = {}  # for sample problems

        # self.SetBackgroundColour(wx.NamedColor('GREY50'))

        self.box_font = wx.Font(12, wx.FONTFAMILY_MODERN,
                                wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        # Create the menubar
        menu_bar = wx.MenuBar()

        # File menu
        self.fmenu = wx.Menu()
        submenu = self.sample_menu(sample_dir())
        self.fmenu.AppendMenu(-1, 'Sample Inputs', submenu)
        self.fmenu.AppendSeparator()
        id = wx.NewId()
        self.fmenu.Append(id, 'Clear Entire Setup Panel')
        self.Bind(wx.EVT_MENU, self.clear_setup, id=id)
        self.fmenu.Append(wx.ID_OPEN, '&Open Input File...\tCtrl+O')
        id = wx.NewId()
        self.fmenu.Append(id, 'Append To Input...')
        self.Bind(wx.EVT_MENU, self.on_append, id=id)
        self.fmenu.AppendSeparator()
        self.fmenu.Append(wx.ID_SAVE, '&Save Input\tCtrl+S')
        self.fmenu.Enable(wx.ID_SAVE, False)
        self.fmenu.Append(wx.ID_SAVEAS, 'Save Input As...')
        self.fmenu.AppendSeparator()
        self.fmenu.Append(wx.ID_EXIT, '&Quit\tCtrl+Q')

        self.Bind(wx.EVT_MENU, self.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.on_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.on_saveas, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.on_close, id=wx.ID_EXIT)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        menu_bar.Append(self.fmenu, '&File')

        # Preferences menu
        self.pref_menu = wx.Menu()

        id = wx.NewId()
        self.pref_menu.Append(id, 'Font for Text Boxes...')
        self.Bind(wx.EVT_MENU, self.select_font, id=id)
        self.pref_menu.AppendSeparator()

        self.highlight_id = wx.NewId()
        self.pref_menu.Append(self.highlight_id,
                              'Automatic Highlighting for Text Boxes', '',
                              wx.ITEM_CHECK)
        if not Win32():
            self.pref_menu.Check(self.highlight_id, True)
        self.Bind(wx.EVT_MENU, self.highlight_toggle, id=self.highlight_id)

        self.tooltip_id = wx.NewId()
        self.pref_menu.Append(self.tooltip_id, 'Show Tool Tips', '',
                              wx.ITEM_CHECK)
        self.pref_menu.Check(self.tooltip_id, True)
        self.Bind(wx.EVT_MENU, self.tooltip_toggle, id=self.tooltip_id)

        menu_bar.Append(self.pref_menu, '&Preferences')

        # View menu
        self.view_menu = wx.Menu()
        self.view_id = wx.NewId()
        self.view_menu.Append(self.view_id, 'Hide Setup Panel')
        self.Bind(wx.EVT_MENU, self.setup_toggle, id=self.view_id)
        self.run_id = wx.NewId()
        self.view_menu.Append(self.run_id,'Hide Run Panel')
        self.Bind(wx.EVT_MENU, self.run_toggle, id=self.run_id)
        menu_bar.Append(self.view_menu, '&View')

        # Help menu
        menu = wx.Menu()
        menu.Append(wx.ID_HELP_CONTENTS, 'Help \tF1')
        menu.AppendSeparator()
        menu.Append(wx.ID_ABOUT, 'About')
        self.Bind(wx.EVT_MENU, self.get_help, id=wx.ID_HELP_CONTENTS)
        self.Bind(wx.EVT_MENU, self.get_about, id=wx.ID_ABOUT)
        menu_bar.Append(menu, '&Help')

        # set MenuBar and StatusBar
        self.SetMenuBar(menu_bar)
        # self.CreateStatusBar()

        self.setup = Setup_tabs(self)
        self.control = Control_panel(self)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.setup, 1, wx.ALL|wx.GROW, 1)
        sizer.Add(self.control, 0, wx.ALL|wx.GROW, 3)
        self.SetSizer(sizer)
        # sizer.Fit(self)  # overrides size in frame init above

    def sample_menu(self, dir_path):
        " Recursive: leaves are *.in files."
        if not os.access(dir_path, os.R_OK):
            error_dialog('The samples directory %s seems to be missing' %
                         dir_path)
        else:
            menu = wx.Menu()
            entries = os.listdir(dir_path)
            entries.sort()             # sorts in-place
            have_file = have_dir = False
            for x in entries:
                if os.path.isfile(os.path.join(dir_path, x)):
                    have_file = True
            for x in entries:
                path = os.path.join(dir_path, x)
                if os.path.isdir(path):
                    submenu = self.sample_menu(path)
                    menu.AppendMenu(-1, x, submenu)
                    have_dir = True
            if have_file and have_dir:
                menu.AppendSeparator()
            for x in entries:
                path = os.path.join(dir_path, x)
                if os.path.isfile(path) and re.search('\.in$', path):
                    id = wx.NewId()
                    self.probs[id] = path
                    menu.Append(id, x)
                    self.Bind(wx.EVT_MENU, self.load_sample, id=id)
            return menu

    def load_sample(self, evt):
        path = self.probs[evt.GetId()]
        try:
            f = open(path)
            input = f.read()
            self.setup.store_new_input(input, None)
        except IOError, e:
            error_dialog('Error opening file %s for reading.' % path)

        self.SetTitle('Prover9/Mace4')

    def on_close(self, evt):
        if self.control.prover9.job_state() in [State.running,State.suspended]:
            error_dialog('You must "Kill" the Prover9 job before quitting.')
        elif self.control.mace4.job_state() in [State.running,State.suspended]:
            error_dialog('You must "Kill" the Mace4 job before quitting.')
        else:
            self.Destroy()

    def clear_setup(self, evt):
        self.setup.reset()

    def on_open(self, evt):
        (dir,style) = open_dir_style(self.current_path)  # depends on platform
        dlg = wx.FileDialog(self, message='Select a file',
                            defaultDir=dir, style=style)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()      # full path
            try:
                f = open(path)
                input = f.read()
                self.setup.store_new_input(input, Program_version)
                self.current_path = path
                self.fmenu.Enable(wx.ID_SAVE, True)
                self.SetTitle(os.path.basename(path) + ' - Prover9/Mace4')
            except IOError, e:
                error_dialog('Error opening file %s for reading.' % path)
        dlg.Destroy()

    def on_append(self, evt):
        (dir,style) = open_dir_style(self.current_path)  # depends on platform
        dlg = wx.FileDialog(self, message='Select a file',
                            defaultDir=dir, style=style)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()      # full path
            try:
                f = open(path)
                input = f.read()
                self.setup.append_input(input)
                # self.current_path = path
                # self.fmenu.Enable(wx.ID_SAVE, True)
                # self.SetTitle(os.path.basename(path) + ' - Prover9/Mace4')
            except IOError, e:
                error_dialog('Error opening file %s for reading.' % path)
        dlg.Destroy()

    def write_input(self, path):
        try:
            input = self.setup.assemble_input()
            f = open(path, 'w')
            f.write('%% Saved by %s.\n\n' % Banner)
            f.write(input)
            return True
        except IOError, e:
            error_dialog('Error opening file %s for writing.' % path)
            return False

    def on_save(self, evt):
        if not self.current_path:
            error_dialog('filename for save not known')
        else:
            self.write_input(self.current_path)

    def on_saveas(self, evt):
        (dir,style) = saveas_dir_style(self.current_path) # depends on platform
        dlg = wx.FileDialog(self, message='Save file as ...',
                            defaultDir=dir, style=style)
        # ??? dlg.SetFilterIndex(2)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()      # full path
            ok = self.write_input(path)
            if ok:
                self.current_path = path
                self.fmenu.Enable(wx.ID_SAVE, True)
                self.SetTitle(os.path.basename(path) + ' - Prover9/Mace4')
            
        dlg.Destroy()

    def get_help(self, evt):
        text = '\n' + Banner + '\n' + Help
        frame = Text_frame(self, to_top(self).box_font,
                           'Help',
                           text, saveas=False)
        frame.Show(True)
        
    def get_about(self, evt):
        info_dialog('\n' + Banner + '\n' + Feedback + Things_to_do)

    def tooltip_toggle(self, evt):
        enable = self.pref_menu.IsChecked(self.tooltip_id)
        wx.ToolTip.Enable(enable)

    def highlight_toggle(self, evt):
        enable = self.pref_menu.IsChecked(self.highlight_id)
        if enable:
            self.setup.start_auto_highlight()
        else:
            self.setup.stop_auto_highlight()

    def auto_highlight(self):
        return self.pref_menu.IsChecked(self.highlight_id)

    def select_font(self, evt):
        data = wx.FontData()
        data.EnableEffects(True)
        data.SetInitialFont(self.box_font)
        dlg = wx.FontDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetFontData()
            font = data.GetChosenFont()
            self.box_font = font
            self.setup.update_font(font)
        dlg.Destroy()

    def setup_toggle(self, evt):
        show = (self.view_menu.GetLabel(self.view_id) == 'Show Setup Panel')
        if show:
            self.setup.Show(True)
            self.SetPosition(self.saved_client_pos)
            self.SetClientSize(self.saved_client_size)
            self.Layout()                # rearrange children
            self.view_menu.Enable(self.run_id, True)
            self.view_menu.SetLabel(self.view_id, 'Hide Setup Panel')
        else:
            # Size and position the frame (self) so that the run
            # panel stays stays the same.
            self.saved_client_pos  = (x1,y1) = self.GetPosition()
            self.saved_client_size = (w1,h1) = self.GetClientSize()
            self.setup.Show(False)
            self.Fit()  # shrink window to fit run panel
            (w2,_) = self.GetClientSize()
            self.SetPosition(((x1+w1)-w2, y1))
            self.SetClientSize((w2, h1))
            self.view_menu.Enable(self.run_id, False)
            self.view_menu.SetLabel(self.view_id, 'Show Setup Panel')
        self.Show(True)

    def run_toggle(self, evt):
        show = (self.view_menu.GetLabel(self.run_id) == 'Show Run Panel')
        if show:
            (w,h) = self.GetClientSize()
            self.control.Show(True)
            self.SetClientSize((w,h))
            self.Layout()                # rearrange children
            self.view_menu.Enable(self.view_id, True)
            self.view_menu.SetLabel(self.run_id, 'Hide Run Panel')
        else:
            # erase run panel, expand setup panel to fill space
            self.control.Show(False)
            self.setup.SetClientSize(self.GetClientSize())
            self.view_menu.Enable(self.view_id, False)
            self.view_menu.SetLabel(self.run_id, 'Show Run Panel')
        self.Show(True)

# END class Main_frame(Frame)

class Splash_screen(wx.SplashScreen):
    def __init__(self, path):

            bmp = wx.Image(path, wx.BITMAP_TYPE_GIF).ConvertToBitmap()
            wx.SplashScreen.__init__(
                self, bmp, wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_NO_TIMEOUT,
                5000, None, -1)

# END class Splash_screen(wx.SplashScreen):

class My_app(wx.App):
    def OnInit(self):

        size = size_that_fits((1000,700))  # reduce if screen too small
        pos = pos_for_center(size)         # position to center frame

        frame = Main_frame(None, 'Prover9/Mace4', size, pos)
        self.SetTopWindow(frame)

        if True:
            path = os.path.join(image_dir(),'prover9-splash.gif')
            if not os.access(path, os.R_OK):
                error_dialog('splash image %s not found' % path)
	    else:
                splash = Splash_screen(path)
                splash.Show(True)
                time.sleep(1)
                splash.Destroy()

        frame.Show(True)
    
	# info_dialog(path_info())
    
        return True

# end class My_app(wx.App):

# Initialization that does not need wx

os.chdir(os.path.expanduser('~'))  # set current directory to user's home

app = My_app(redirect=False)

app.MainLoop()

