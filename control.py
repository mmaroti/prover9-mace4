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

import os, wx, re, copy
import time, thread, tempfile, subprocess, signal

# local imports

import utilities
from files import *
from platforms import *
from wx_utilities import *
from my_setup import *
from options import *

def run_and_wait(command, input = '', fin = None):

    if not fin:
        fin  = tempfile.TemporaryFile('w+b')  # stdin
        fin.write(input)
        fin.seek(0)

    fout = tempfile.TemporaryFile('w+b')  # stdout
    ferr = tempfile.TemporaryFile('w+b')  # stderr

    if Win32():
        # creationflag says not to pop a DOS box
        process = subprocess.Popen(command,stdin=fin,stdout=fout,stderr=ferr,
                                  creationflags=win32process.CREATE_NO_WINDOW)
    else:
        process = subprocess.Popen(command,stdin=fin,stdout=fout,stderr=ferr)

    exit_code = process.wait()
    fout.seek(0)
    output = fout.read()
    ferr.seek(0)
    error = ferr.read()
    fin.close()
    fout.close()
    ferr.close()
    return (exit_code, output, error)

def isofilter_command(program_name):
    fullpath = os.path.join(bin_dir(), program_name)
    if not binary_ok(fullpath):
        return None
    else:
        return [fullpath]

def ops_in_interp(s):
    i = s.find('interpretation(')
    ops = []
    if i >= 0:
        j = s.find(').', i+1)
        interp = s[i:j+2]
        r = re.compile('(?:function|relation)\(([^,(]*)')
        m = r.search(interp)
        while m:
            op = m.group(1)
            if op != '=':
                ops.append(op)
            m = r.search(interp, m.end())
    return ops
    
class Prover9:

    name = 'Prover9'
    solution_name = 'Proof'
    box_name = 'Proof Search'
    solution_ext = 'proof'
    some_message = 'Some, but not all, of the requested proofs were found.'

    logo_path = os.path.join(image_dir(), 'prover9-5a-128t.gif')

    # Compile regular expression for extracting stats from stderr.

    r_info = re.compile('Given=(\d+)\. Generated=(\d+)\. Kept=(\d+)\. '
                        'proofs=(\d+)\.User_CPU=(\d*\.\d*),')

    exits = {}
    exits[0]   = 'Proof'
    exits[1]   = 'Fatal Error'
    exits[2]   = 'Exhausted'
    exits[3]   = 'Memory Limit'
    exits[4]   = 'Time Limit'
    exits[5]   = 'Given Limit'
    exits[6]   = 'Kept Limit'
    exits[7]   = 'Action Exit'
    exits[101] = 'Interrupted'
    exits[102] = 'Crashed'
    exits[-9]  = 'Killed' # Linux, Mac
    exits[-1]  = 'Killed' # Win32

    def search_command(self):
        fullpath = os.path.join(bin_dir(), 'prover9')
        if not binary_ok(fullpath):
            return None
        else:
            return [fullpath]

    def success_command(self):
        fullpath = os.path.join(bin_dir(), 'prooftrans')
        if not binary_ok(fullpath):
            return None
        else:
            return [fullpath]

    def exists_solution(self, exit_code, output):
        return output.find('== PROOF ==') >= 0

    def count_solutions(self, solutions):
        return solutions.count('== PROOF ==')

    def exit_message(self, code):
        if code in self.exits.keys():
            return self.exits[code]
        else:
            return 'unknown exit code: %d' % code

    def logo_bitmap(self):
        if not os.access(self.logo_path, os.R_OK):
            error_dialog('The logo file %s cannot be found.' % self.logo_path)
            return None
        else:
            return wx.Image(self.logo_path,
                            wx.BITMAP_TYPE_GIF).ConvertToBitmap()

    def get_info_from_stderr(self, lines):
        stats = utilities.grep_last('Given', lines)
        time  = utilities.grep_last('User_CPU', lines)
        if stats and time:
            line = stats.strip() + time.strip()
            m = self.r_info.match(line)
            if m:
                return [('CPU Seconds', m.groups()[4]),
                        ('Given',       m.groups()[0]),
                        ('Generated',   m.groups()[1]),
                        ('Kept',        m.groups()[2]),
                        ('Proofs',      m.groups()[3])]
            else:
                error_dialog('get_stderr_info, failed to match')

        return [('CPU Seconds', '?'),
                ('Given',       '?'),
                ('Generated',   '?'),
                ('Kept',        '?'),
                ('Proofs',      '?')]

    def reformatter(self, parent, proofs, saved_solution):
        n = self.count_solutions(proofs)
        return Reformat_proof(parent, proofs, n, saved_solution)
        
# end class Prover9

class Mace4:

    name = 'Mace4'
    solution_name = 'Model'
    box_name = 'Model/Counterexample Search'
    solution_ext = 'model'
    some_message = ''

    logo_path = os.path.join(image_dir(), 'mace4-90t.gif')
    
    # Compile regular expression for extracting stats from stderr.
    # Domain_size=8. Models=0. User_CPU=8.00.
    r_info = re.compile('Domain_size=(\d+)\. Models=(\d+)\. User_CPU=(\d*\.\d*)\.')

    exits = {}
    exits[0]   = 'Model(s)'
    exits[1]   = 'Fatal Error'
    exits[2]   = 'Exhausted (no)'
    exits[3]   = 'Exhausted (yes)'
    exits[4]   = 'Time Limit (yes)'
    exits[5]   = 'Time Limit (no)'
    exits[6]   = 'Mem Limit (yes)'
    exits[7]   = 'Mem Limit (no)'
    exits[101] = 'Interrupted'
    exits[102] = 'Crashed'
    exits[-9]  = 'Killed' # Linux, Mac
    exits[-1]  = 'Killed' # Win32

    def search_command(self):
        fullpath = os.path.join(bin_dir(), 'mace4')
        if not binary_ok(fullpath):
            return None
        else:
            return [fullpath, '-c']

    def success_command(self):
        fullpath = os.path.join(bin_dir(), 'interpformat')
        if not binary_ok(fullpath):
            return None
        else:
            return [fullpath]

    def exists_solution(self, exit_code, output):
        return output.find('== MODEL ==') >= 0

    def count_solutions(self, solutions):
        return solutions.count('interpretation')

    def exit_message(self, code):
        if code in self.exits.keys():
            return self.exits[code]
        else:
            return 'unknown exit code: %d' % code

    def logo_bitmap(self):
        if not os.access(self.logo_path, os.R_OK):
            error_dialog('The logo file %s cannot be found.' % self.logo_path)
            return None
        else:
            return wx.Image(self.logo_path,
                            wx.BITMAP_TYPE_GIF).ConvertToBitmap()

    def get_info_from_stderr(self, lines):
        line = utilities.grep_last('Domain_size=', lines)
        if line:
            m = self.r_info.match(line)
            if m:
                return [('CPU Seconds', m.groups()[2]),
                        ('Domain Size', m.groups()[0]),
                        ('Models'     , m.groups()[1])]
            else:
                error_dialog('get_stderr_info, failed to match')
        return [('CPU Seconds', '?'),
                ('Domain Size', '?'),
                ('Models'     , '?')]

    def reformatter(self, parent, models, saved_solution):
        n = self.count_solutions(models)
        return Reformat_model(parent, models, n, saved_solution)

# end class Mace4

class Reformat_proof:
    def __init__(self, parent, proofs, num_proofs, saved_flag):

        self.parent = parent
        self.proofs = proofs
        self.num_proofs = num_proofs
        self.saved_flag = saved_flag

        self.choices = ['standard', 'parents_only', 'xml', 'ivy', 'hints']
        self.choice = self.choices[0]

        self.dlg = dlg = wx.Dialog(parent, -1, title="Reformat Proof(s)",
                                   pos=pos_for_center((0,0)))

        rb = wx.RadioBox(dlg, -1, 'Format', choices=self.choices,
                         majorDimension=1, style=wx.RA_SPECIFY_COLS)
        dlg.Bind(wx.EVT_RADIOBOX, self.on_rb, rb)

        options_box = wx.StaticBox(dlg, -1, 'Options')
        box_sizer = wx.StaticBoxSizer(options_box, wx.VERTICAL)
        self.expand_cb = wx.CheckBox(dlg, -1, 'Expand Proof')
        self.renumber_cb = wx.CheckBox(dlg, -1, 'Renumber Proof')
        self.striplabels_cb = wx.CheckBox(dlg, -1, 'Remove Labels')
        self.hl_cb = wx.CheckBox(dlg, -1, 'Hints Label')
        self.hl_ctrl = wx.TextCtrl(dlg, -1, '', size=(100, -1))

        box_sizer.Add(self.expand_cb)
        box_sizer.Add(self.renumber_cb)
        box_sizer.Add(self.striplabels_cb)
        subsizer = wx.BoxSizer(wx.HORIZONTAL)
        subsizer.Add(self.hl_cb, 0, wx.CENTER, 0)
        subsizer.Add(self.hl_ctrl, 0, wx.CENTER, 0)
        box_sizer.Add(subsizer)

        cancel_btn = wx.Button(dlg, -1, 'Cancel')
        dlg.Bind(wx.EVT_BUTTON, self.on_cancel, cancel_btn)
        ok_btn = wx.Button(dlg, -1, 'OK')
        dlg.Bind(wx.EVT_BUTTON, self.on_ok, ok_btn)

        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(rb, 0, wx.ALL|wx.CENTER, 10)
        sizer1.Add(box_sizer, 0, wx.ALL|wx.CENTER, 10)

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(cancel_btn, 0, wx.ALL, 10)
        sizer2.Add(ok_btn, 0, wx.ALL, 10)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sizer1, 0, wx.CENTER, 10)
        sizer.Add(sizer2, 0, wx.CENTER, 10)
        dlg.SetSizer(sizer)
        sizer.Fit(dlg)

        self.grayout_options()
        if Win32():
            rc = dlg.Show()  # if modal, I can't get the new fame to the top!
        else:
            rc = dlg.ShowModal()

    def grayout_options(self):
        if self.choice in ['standard', 'parents_only', 'xml']:
            self.expand_cb.Enable(True)
            self.renumber_cb.Enable(True)
            self.striplabels_cb.Enable(True)
            self.hl_cb.Enable(False)
            self.hl_ctrl.Enable(False)
        elif self.choice == 'ivy':
            self.expand_cb.Enable(False)
            self.renumber_cb.Enable(True)
            self.striplabels_cb.Enable(False)
            self.hl_cb.Enable(False)
            self.hl_ctrl.Enable(False)
        elif self.choice == 'hints':
            self.expand_cb.Enable(True)
            self.renumber_cb.Enable(False)
            self.striplabels_cb.Enable(True)
            self.hl_cb.Enable(True)
            self.hl_ctrl.Enable(True)
        else:
            error_dialog('grayout_options: unknown proof format')

    def command(self):
        command = [os.path.join(bin_dir(), 'prooftrans'), self.choice]
        if self.expand_cb.IsEnabled() and self.expand_cb.IsChecked():
            command.append('expand')
        if self.renumber_cb.IsEnabled() and self.renumber_cb.IsChecked():
            command.append('renumber')
        if self.striplabels_cb.IsEnabled() and self.striplabels_cb.IsChecked():
            command.append('striplabels')
        if self.hl_cb.IsEnabled() and self.hl_cb.IsChecked():
            command.append('-label')
            lab = self.hl_ctrl.GetValue().strip()
            if lab != '':
                command.append(lab)
        return command
        
    def on_rb(self, evt):
        self.choice = self.choices[evt.GetInt()]
        self.grayout_options()

    def on_ok(self, evt):
        command = self.command()
        (exit_code, output, err) = run_and_wait(command, input=self.proofs)
        self.dlg.Destroy()
        if exit_code != 0:
            error_dialog("Error reformatting proofs")
        else:
            args = ' '.join(command[1:])
            n = self.num_proofs
            if self.num_proofs == 1:
                title = 'Reformatted Proof (%s)' % (args)
            else:
                title = 'Reformatted Proofs (%s, %d proofs)' % (args, n)
            
            frame = Text_frame(self.parent, to_top(self.parent).box_font,
                               title,
                               output,
                               extension = 'proof',
                               saveas=True,
                               saved_flag = self.saved_flag,
                               off_center=20)
            frame.Show(True)
            frame.Raise()

    def on_cancel(self, evt):
        self.dlg.Destroy()

# class Reformat_proof

class Reformat_model:
    def __init__(self, parent, models, num_models, saved_flag):
        self.parent = parent
        self.models = models
        self.saved_flag = saved_flag
        self.num_models = num_models

        self.choices = ['standard', 'standard2', 'portable', 'tabular',
                        'raw', 'cooked', 'tex', 'xml']
        menu = wx.Menu()
        self.map = {}
        for item in self.choices:
            id = wx.NewId()
            self.map[id] = item
            menu.Append(id, item)
            self.parent.Bind(wx.EVT_MENU, self.on_select, id=id)
        self.parent.PopupMenu(menu)
        menu.Destroy()

    def on_select(self, evt):
        item = self.map[evt.GetId()]
        command = [os.path.join(bin_dir(), 'interpformat'), item]
        (exit_code, output, err) = run_and_wait(command, input=self.models)
        if exit_code != 0:
            error_dialog("Error reformatting models")
        else:
            args = ' '.join(command[1:])
            n = self.num_models
            if self.num_models == 1:
                title = 'Reformatted Model (%s)' % (args)
            else:
                title = 'Reformatted Models (%s, %d models)' % (args, n)
            
            frame = Text_frame(self.parent, to_top(self.parent).box_font,
                               title,
                               output,
                               extension = 'model',
                               saveas=True,
                               saved_flag = self.saved_flag,
                               off_center=40)
            frame.Show(True)

# class Reformat_model

class Run_program:
    def __init__(self, parent, program, input):
        self.parent = parent
        self.program = program
        self.input = input
        self.output = None
        self.solution = None
        self.exit_code = None
        self.state = State.ready  # ready, running, suspended, done, error

        # The following are lists so they can be altered as side effects.
        self.saved_input    = [False]
        self.saved_output   = [False]
        self.saved_solution = [False]

        thread.start_new_thread(self.run, ())

    def run(self):
        #
        # DO NOT DO ANY GUI STUFF IN HERE, BECAUSE THIS
        # RUNS IN A SEPARATE THREAD!!!
        #
        search_command  = self.program.search_command()
        success_command = self.program.success_command()

        if not search_command or not success_command:
            self.state = State.error
            self.fin  = self.fout = self.ferr = None
        else:
            # use files to avoid buffering problems  (maybe improve later)
            self.fin  = tempfile.TemporaryFile('w+b')  # stdin
            self.fout = tempfile.TemporaryFile('w+b')  # stdout
            self.ferr = tempfile.TemporaryFile('w+b')  # stderr

            self.fin.write(self.input)
            self.fin.seek(0)

            if Win32():
                # creationflag says not to pop a DOS box
                self.process = subprocess.Popen(
                    search_command, stdin=self.fin,
                    stdout=self.fout, stderr=self.ferr,
                    creationflags=win32process.CREATE_NO_WINDOW)
            else:
                self.process = subprocess.Popen(
                    search_command, stdin=self.fin,
                    stdout=self.fout, stderr=self.ferr)
                
            self.state = State.running
            self.exit_code = self.process.wait()  # Wait for process to finish!
            self.state = State.done
            self.fout.seek(0)  # rewind stdout
            self.output = self.fout.read()

            if (self.exit_code == 0 or
                self.program.exists_solution(self.exit_code, self.output)):

                # Extract the solution from stdout
                self.fout.seek(0)
                (rc,output,err) = run_and_wait(success_command, fin=self.fout)

                if rc == 0:  
                    self.solution = output  # at least one solution
                elif rc == 2:
                    self.solution = None  # no solution (clear(print_proofs)?)
                else:
                    self.solution = ('There was an error extracting the %s.' %
                                     self.program.solution_name)

            # Keep files open until self is deleted.

        self.parent.invoke_later(self.parent.job_finished)

    def pause(self):
        if self.state == State.running:
            os.kill(self.process.pid, signal.SIGSTOP)
            self.state = State.suspended

    def resume(self):
        if self.state == State.suspended:
            os.kill(self.process.pid, signal.SIGCONT)
            self.state = State.running

    def get_stderr_info(self):
        if self.state in [State.running, State.suspended, State.done]:
            self.ferr.seek(0)  # rewind
            lines = self.ferr.readlines()
            info = self.program.get_info_from_stderr(lines)
            return info

    def kill(self):
        if self.state == State.running or self.state == State.suspended:
            # Cleanup will occur when the 'run' thread terminates.
            if Win32():
                win32api.TerminateProcess(int(self.process._handle), -1)
            else:
                os.kill(self.process.pid, signal.SIGKILL)

    def done_with_job(self):
	if self.fin:  # if one exists, all exist
            self.fin.close()
            self.fout.close()
            self.ferr.close()
        del self

# end class Run_program()
    
class Program_panel(wx.Panel):

    def __init__(self, parent, program, options):

        self.program = program
        self.job = None
        self.info_panel = None
        self.timer = None        # for monitoring (Info button)

        wx.Panel.__init__(self, parent)
        self.Connect(-1, -1, Invoke_event.my_EVT_INVOKE, self.on_invoke)

        # Surrounding box

        box_program = wx.StaticBox(self, -1, program.box_name)
        box_sizer = wx.StaticBoxSizer(box_program, wx.VERTICAL)

        # Time limit (widget shared with options panel elsewhere)

        id = wx.NewId()
        label_id = wx.NewId()
        opt = copy.deepcopy(options.name_to_opt('max_seconds'))
        if opt:
            opt[Id] = id
            opt[Label_id] = label_id
            opt[Share] = [opt]
            (min, max) = opt[Range]
            options.share_external_option(opt)
            self.time_ctrl = wx.SpinCtrl(self, id, min=min, max=max,
                                         size=(75,-1))
                                         
            self.time_ctrl.SetValue(opt[Default])
        else:
            error_dialog('error sharing max_second option (%s)' % program.name)
            self.time_ctrl = wx.SpinCtrl(self, id, min=-1, max=sys.maxint,
                                         size=(75,-1))
            self.time_ctrl.SetValue(60)

        self.time_ctrl_opt = opt

        label = wx.StaticText(self, label_id, 'Time Limit: ')
        self.time_ctrl.SetToolTipString('A value of -1 means there is no limit.')
        self.Bind(wx.EVT_SPINCTRL, self.on_time_ctrl, self.time_ctrl)

        time_sizer = wx.BoxSizer(wx.HORIZONTAL)
        time_sizer.Add(label, 0, wx.ALL|wx.ALIGN_CENTER, 1)
        time_sizer.Add(self.time_ctrl, 0, wx.ALL, 1)
        time_sizer.Add(wx.StaticText(self, -1, 'seconds.'), 0,
                       wx.ALL|wx.ALIGN_CENTER, 1)

        # Start, Pause, Kill

        self.start_btn = wx.Button(self, -1, 'Start')
        self.start_btn.SetToolTipString(
            'Start %s with the current input.' % program.name)
        self.Bind(wx.EVT_BUTTON, self.on_start, self.start_btn)
        self.pause_btn = wx.Button(self, -1, 'Pause')
        self.pause_btn.SetToolTipString('Pause or Resume %s.' % program.name)
        self.pause_btn.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.on_pause_resume, self.pause_btn)
        if Win32():
            self.pause_btn.Show(False)
        self.kill_btn = wx.Button(self, -1, 'Kill')
        self.kill_btn.SetToolTipString('Kill %s process.' % program.name)
        self.kill_btn.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.on_kill, self.kill_btn)

        run_sizer = wx.BoxSizer(wx.HORIZONTAL)
        run_sizer.Add(self.start_btn, 0, wx.ALL, 1)
        run_sizer.Add(self.pause_btn, 0, wx.ALL, 1)
        run_sizer.Add(self.kill_btn, 0, wx.ALL, 1)

        # Busy bar

        self.bar = Busy_bar(self, width=200, height=16, delay=100)

        # State line

        width = max_width(program.exits.values(), self)
        self.state_text = wx.StaticText(self, -1, 'Ready',
                                        size=(width, -1))

        state_sizer = wx.BoxSizer(wx.HORIZONTAL)
        text = wx.StaticText(self, -1, 'State: ')
        state_sizer.Add(text,            0, wx.ALL|wx.ALIGN_CENTER, 1)
        state_sizer.Add(self.state_text, 1, wx.ALL|wx.ALIGN_CENTER, 1)

        # Info, Show/Save

        self.info_btn = wx.Button(self, -1, 'Info')
        self.info_btn.SetToolTipString(
            'Show some statistics on the %s search.' % program.name)
        self.Bind(wx.EVT_BUTTON, self.on_info, self.info_btn)
        self.info_btn.Enable(False)
        
        self.show_save_btn = wx.Button(self, -1, 'Show/Save')
	if not Mac():
	    self.show_save_btn.SetToolTipString(
              'The choices refer to the most recent %s search.' % program.name)
        self.Bind(wx.EVT_BUTTON, self.on_show_save, self.show_save_btn)
        self.show_save_btn.Enable(False)

        show_sizer = wx.BoxSizer(wx.HORIZONTAL)
        show_sizer.Add(self.info_btn,   0, wx.ALL, 1)
        show_sizer.Add(self.show_save_btn, 0, wx.ALL, 1)

        # Overall Layout

        logo_bitmap = program.logo_bitmap()
        if logo_bitmap:
            logo = wx.StaticBitmap(self, -1, logo_bitmap)
            box_sizer.Add(logo,     0, wx.ALL|wx.ALIGN_CENTER,3)
        box_sizer.Add(time_sizer,   0, wx.ALL, 3)
        box_sizer.Add(run_sizer,    0, wx.ALL|wx.ALIGN_CENTER,3)
        box_sizer.Add(self.bar,     0, wx.ALL|wx.ALIGN_CENTER,3)
        box_sizer.Add(state_sizer,  0, wx.ALL|wx.GROW, 3)
        box_sizer.Add(show_sizer,   0, wx.ALL|wx.ALIGN_CENTER, 3)
        self.SetSizer(box_sizer)

    # Methods

    def on_info(self, evt):
        if self.job:
            info = self.job.get_stderr_info()
            self.info_panel = Mini_info(self, 'Info on %s Search' %
                                        self.program.name, info)
            self.info_btn.Enable(False)
            if self.job.state != State.done:
                self.timer = wx.Timer(self, -1)
                wx.EVT_TIMER(self, self.timer.GetId(), self.update_info)
                self.timer.Start(2000)  # milliseconds

    def update_info(self, evt):
        if self.job:
            info = self.job.get_stderr_info()
            self.info_panel.update(info)
            if self.job.state == State.done:
                self.timer.Stop()
                self.timer = None
        else:
            self.timer.Stop()
            self.timer = None

    def info_reset(self):
        if self.timer:
            self.timer.Stop()
            self.timer = None
        self.info_btn.Enable(True)
        self.info_panel = None

    def on_time_ctrl(self, evt): 
        if self.time_ctrl_opt:
            self.time_ctrl_opt[Value] = self.time_ctrl.GetValue()
            update_label(self.time_ctrl_opt)
            update_shared(self.time_ctrl_opt)

    def on_start(self, evt):
        if self.job:
            if self.job.solution and not self.job.saved_solution[0]:
                message = (
                    'There is an unsaved %s.  Delete the %s and continue?' %
                    (self.program.solution_name,self.program.solution_name))
                dlg = wx.MessageDialog(self, message, '',
                                       wx.OK | wx.CANCEL| wx.ICON_QUESTION)
                rc = dlg.ShowModal()
                dlg.Destroy()
                if rc == wx.ID_CANCEL:
                    return

            self.job.done_with_job()
            self.job = None

            self.info_btn.Enable(False)
            if self.info_panel:
                self.info_panel.Close()

        self.start_btn.Enable(False)
        self.time_ctrl.Enable(False)
        self.pause_btn.Enable(True)
        self.kill_btn.Enable(True)
        self.info_btn.Enable(True)
        self.show_save_btn.Enable(False)
        self.bar.start()
        self.state_text.SetLabel('Running')
        input = to_top(self).setup.assemble_input()
        input = 'assign(report_stderr, 2).\n' + input
        self.job = Run_program(self, self.program, input)

    def on_pause_resume(self, evt):
        # assume job is running or suspended
        if self.job.state == State.running:
            self.job.pause()
            self.bar.pause()
            self.pause_btn.SetLabel('Resume')
            self.state_text.SetLabel('Paused')
        elif self.job.state == State.suspended:
            self.job.resume()
            self.bar.resume()
            self.pause_btn.SetLabel('Pause')
            self.state_text.SetLabel('Running')
        else:
            error_dialog('pause_resume: unknown job state')

    def on_kill(self, evt):
        # assume job is running or suspended
        self.job.kill()  # calls job_finished indirectly

    def job_state(self):
        if self.job:
            return self.job.state
        else:
            return None

    def job_finished(self):
        self.bar.stop()
        self.pause_btn.Enable(False)
        self.pause_btn.SetLabel('Pause')
        self.kill_btn.Enable(False)
        self.show_save_btn.Enable(True)
        self.start_btn.Enable(True)
        self.time_ctrl.Enable(True)

        if self.job.state == State.error:
            self.state_text.SetLabel('Program_Not_Found')
            error_dialog('%s binaries not found, looking in\n%s' %
                         (self.program.name, bin_dir()))
        else:
            message = self.program.exit_message(self.job.exit_code)
            self.state_text.SetLabel(message)

            if self.job.exit_code == 1:  # fatal error
                frame = Text_frame(
                    self, to_top(self).box_font,
                    self.program.name + ' Fatal Error',
                    self.job.output,
                    saveas=False)
                frame.hilite_error()
                frame.Show(True)
                error_dialog('A Fatal Error occurred.  The %s output '
                             'is shown.' % self.program.name)
                
            elif self.job.solution:
                self.ss_solution(None)

                if self.job.exit_code != 0:
                    info_dialog('%s Exit: %s. \n%s'
                                % (self.program.name, message,
                                   self.program.some_message))
            elif self.program.exits[self.job.exit_code] != 'Killed':
                info_dialog('%s Exit: %s' % (self.program.name, message))

    def on_show_save(self, evt):
        menu = wx.Menu()

        id = wx.NewId()
        menu.Append(id, self.program.name + ' Input (from most recent search)')
        self.Bind(wx.EVT_MENU, self.ss_input, id=id)

        id = wx.NewId()
        menu.Append(id, self.program.name + ' Output')
        self.Bind(wx.EVT_MENU, self.ss_output, id=id)
        if self.job.state == State.error:
            menu.Enable(id, False)

        id = wx.NewId()
        menu.Append(id, self.program.name + ' ' + self.program.solution_name)
        self.Bind(wx.EVT_MENU, self.ss_solution, id=id)
        if self.job.exit_code != 0 and not self.job.solution:
            menu.Enable(id, False)

        self.PopupMenu(menu)
        menu.Destroy()

    def ss_input(self, evt):
        frame = Text_frame(self, to_top(self).box_font,
                           self.program.name + ' Input',
                           self.job.input,
                           extension='in', saveas=True,
                           saved_flag=self.job.saved_input)
        frame.Show(True)
        
    def ss_output(self, evt):
        frame = Text_frame(self, to_top(self).box_font,
                           self.program.name + ' Output',
                           self.job.output,
                           extension='out', saveas=True,
                           saved_flag=self.job.saved_output)
        frame.Show(True)
        
    def ss_solution(self, evt):
        extra_ops=[('Reformat ...', self.on_reformat)]
        solutions = self.program.count_solutions(self.job.solution)
        if (self.program.name == 'Mace4' and solutions > 1):
            extra_ops.append(('Isofilter...', self.on_isofilter))
        if solutions == 1:
            title = '%s %s' % (self.program.name,self.program.solution_name)
        else:
            title = '%s %s (%d %ss)' % (self.program.name,
                                        self.program.solution_name,
                                        solutions,
                                        self.program.solution_name)
        frame = Text_frame(
            self, to_top(self).box_font,
            title,
            self.job.solution,
            extension=self.program.solution_ext,
            saveas=True,
            saved_flag=self.job.saved_solution,
            extra_operations=extra_ops)
        frame.Show(True)

    def on_reformat(self, evt):
        parent = evt.GetEventObject().GetParent()
        solution = parent.text
        self.program.reformatter(parent, solution, self.job.saved_solution)

    def on_isofilter(self, evt):
        parent = evt.GetEventObject().GetParent()
        solution = parent.text
        frame = Isofilter_frame(self, solution, self.job.saved_solution)

    # The following two methods allow GUI events in the main thread
    # to be initiated by other threads.  See class Invoke_event and
    # the Connect statement in the constructor of this class.

    def on_invoke(self, evt):
        evt.invoke()

    def invoke_later(self, func, *args, **kwargs):
        self.GetEventHandler().AddPendingEvent(Invoke_event(func,args,kwargs))

# END class Program_panel(Panel)

class Control_panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.FULL_REPAINT_ON_RESIZE)

        # Show Input Button

        self.show_input_btn = wx.Button(self, -1, 'Show Current Input')
        self.show_input_btn.SetToolTipString(
            'Show the data in the setup panel as a text file.\n'
            'This is what will be given to Prover9 and/or Mace4.\n'
            'This need not be saved before running Prover9 or Mace4.')
        self.Bind(wx.EVT_BUTTON, self.show_input, self.show_input_btn)

        # Program Panels

        self.prover9 = Program_panel(self, Prover9(),
                                     to_top(self).setup.p9_options.panels)
        self.mace4 = Program_panel(self, Mace4(),
                                   to_top(self).setup.m4_options)

        # Overall Layout

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.show_input_btn, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        sizer.Add((1,10), 1)
        sizer.Add(self.prover9, 0, wx.GROW, 5)
        sizer.Add((1,10), 1)
        sizer.Add(self.mace4, 0, wx.GROW, 5)
        sizer.Add((1,10), 1)
        self.SetSizer(sizer)
        sizer.Fit(self)

    def show_input(self, evt):
        top = to_top(self)
        input = top.setup.assemble_input()
        frame = Text_frame(self, top.box_font,
                           'Current Input', input,
                           extension='in', saveas=False)
        frame.Show(True)

# END class Control_panel(Panel)

class Isofilter_frame(wx.Frame):
    def __init__(self, parent, models, saved_solution):

        self.parent = parent
        self.models = models
        self.state = State.ready  # We'll use ready and running
        
        wx.Frame.__init__(self, parent, title='Isofilter',
                          pos=pos_for_center((0,0)))

        self.Connect(-1, -1, Invoke_event.my_EVT_INVOKE, self.on_invoke)

        ops_string = ' '.join(ops_in_interp(models))

        check_lab  = wx.StaticText(self, -1, 'Check:')
        self.check_id = wx.NewId()
        self.check_ctrl = wx.TextCtrl(self, self.check_id,
                                      value=ops_string, size=(200,-1))

        out_lab  = wx.StaticText(self, -1, 'Output:')
        self.out_id = wx.NewId()
        self.out_ctrl = wx.TextCtrl(self, self.out_id,
                                    value=ops_string, size=(200,-1))

        self.ignore_id = wx.NewId()
        self.ignore_cb = wx.CheckBox(self, self.ignore_id, 'Ignore Constants')

        self.wrap_id = wx.NewId()
        self.wrap_cb = wx.CheckBox(self, self.wrap_id, 'Enclose in List')

        alg_lab =  wx.StaticText(self, -1, 'Algorithm:')
        self.alg_id = wx.NewId()
        self.alg_ch = wx.Choice(self, self.alg_id,
                                choices=['Occurrence Profiles',
                                         'Canonical Forms'])
        self.alg_ch.SetSelection(0)

        self.start_btn = wx.Button(self, -1, 'Start')
        self.Bind(wx.EVT_BUTTON, self.on_start, self.start_btn)

        cancel_btn = wx.Button(self, -1, 'Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancel_btn)

        self.bar = Busy_bar(self, width=200, height=16, delay=100)

        gsizer = wx.GridBagSizer(5,5)
        gsizer.Add(alg_lab,         (0,0))
        gsizer.Add(self.alg_ch,     (0,1))
        gsizer.Add(check_lab,       (1,0))
        gsizer.Add(self.check_ctrl, (1,1))
        gsizer.Add(out_lab,         (2,0))
        gsizer.Add(self.out_ctrl,   (2,1))

        bsizer = wx.BoxSizer(wx.HORIZONTAL)
        bsizer.Add(self.start_btn)
        bsizer.Add(cancel_btn)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((1,5))
        sizer.Add(gsizer, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        sizer.Add(self.ignore_cb, 0, wx.ALL, 5)
        sizer.Add(self.wrap_cb, 0, wx.ALL, 5)
        sizer.Add(bsizer, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        sizer.Add(self.bar, 0, wx.ALL|wx.ALIGN_CENTER, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Show(True)

    # The following two methods allow GUI events in the main thread
    # to be initiated by other threads.  See class Invoke_event and
    # the Connect statement in the constructor of this class.

    def on_invoke(self, evt):
        evt.invoke()

    def invoke_later(self, func, *args, **kwargs):
        self.GetEventHandler().AddPendingEvent(Invoke_event(func,args,kwargs))

    def on_start(self, evt):
        if self.alg_ch.GetStringSelection() == 'Occurrence Profiles':
            command = isofilter_command('isofilter')  # returns list
        else:
            command = isofilter_command('isofilter2')  # returns list
        if command == None:
            error_dialog('Isofilter binary not found.')
            self.Close()
        else:
            if self.wrap_cb.IsChecked():
                command.append('wrap')
            if self.ignore_cb.IsChecked():
                command.append('ignore_consants')
            check = self.check_ctrl.GetValue()
            if check.strip() != '':
                command.append('check')
                command.append(check)
            out = self.out_ctrl.GetValue()
            if out.strip() != '':
                command.append('output')
                command.append(out)

            self.command = command
            self.start_btn.Disable()
            self.bar.start()
            thread.start_new_thread(self.run, ())

    def run(self):
        #
        # DO NOT DO ANY GUI STUFF IN HERE, BECAUSE THIS
        # RUNS IN A SEPARATE THREAD!!!
        #

        self.fin  = tempfile.TemporaryFile('w+b')  # stdin
        self.fout = tempfile.TemporaryFile('w+b')  # stdout
        self.ferr = tempfile.TemporaryFile('w+b')  # stderr

        self.fin.write(self.models)
        self.fin.seek(0)

        if Win32():
            # creationflag says not to pop a DOS box
            self.process = subprocess.Popen(
                self.command, stdin=self.fin,
                stdout=self.fout, stderr=self.ferr,
                creationflags=win32process.CREATE_NO_WINDOW)
        else:
            self.process = subprocess.Popen(
                self.command, stdin=self.fin,
                stdout=self.fout, stderr=self.ferr)

        self.state = State.running
        self.exit_code = self.process.wait()  # Wait for process to finish!
        self.fout.seek(0)  # rewind stdout
        self.filtered_models = self.fout.read()

        self.invoke_later(self.job_finished)

    def job_finished(self):
        self.bar.stop()
        if self.exit_code == 1:
            self.ferr.seek(0)  # rewind stderr
            err = self.ferr.read()
            error_dialog('Isofilter error:\n\n' + err)
        elif self.exit_code == 0:
            n = self.filtered_models.rfind(': input=')
            if n == -1:
                error_dialog('Isofilter error')
            else:
                x = re.split('=|,', self.filtered_models[n:])
                input = int(x[1])
                kept = int(x[3])
   
                extra_ops=[('Reformat ...', self.parent.on_reformat)]

                args = ' '.join(self.command[1:])

                frame = Text_frame(
                    self.parent, to_top(self).box_font,
                    'Isofilter Result (%s, %d models)' % (args, kept),
                    self.filtered_models,
                    extension='model',
                    saveas=True,
                    off_center=20,
                    saved_flag=self.parent.job.saved_solution,
                    extra_operations=extra_ops)
                frame.Show(True)

                info_dialog(('Isofilter received %d models, eliminated %d, '
                             'giving %d nonisomorphic model(s).') %
                            (input, input-kept, kept))

        self.fin.close()
        self.fout.close()
        self.ferr.close()
        self.Close()
        
    def on_cancel(self, evt):
        if self.state == State.running:
            # Cleanup will occur when the 'run' thread terminates.
            if Win32():
                win32api.TerminateProcess(int(self.process._handle), -1)
            else:
                os.kill(self.process.pid, signal.SIGKILL)
        else:
            self.Close()
    
# END class Isofilter_frame(wx.Frame)

def syntax_check(input):

    prover9_command  = Prover9().search_command()

    if not prover9_command:
        error_dialog("syntax check binary (prover9) not found")
    else:
        # use files to avoid buffering problems  (maybe improve later)

        input2 = 'assign(max_given,0).\n ' + input

        (exit_code,output,err) = run_and_wait(prover9_command, input=input2)
        
        exit_str = Prover9().exit_message(exit_code)

        if exit_str in ['Killed', 'Crashed', 'Interruppted']:
            return (exit_str, output, None)
        elif exit_code != 1:  # Fatal error
            return ('Okay', None, None)
        else:
            if re.search('%%ERROR', output):
                r = re.compile('(?<=%%ERROR: ).*')
                m = r.search(output)
                message = output[m.start():m.end()-1] + '.'
                r = re.compile('(?<=%%START ERROR%%).*(?=%%END ERROR%%)',
                               re.DOTALL)  # allow to cross lines
                m = r.search(output)
                if m:
                    error = output[m.start():m.end()].strip()
                else:
                    error = None
                return ('Input_Error', message, error)
            else:
                return ('Other_Error', output, None)

# END def syntax_check

