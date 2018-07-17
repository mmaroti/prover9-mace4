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

import os, re, wx

# local imports

from platforms import *

class State:
    """
    For various processes and threads.
    """
    ready     = 0
    running   = 1
    suspended = 2
    done      = 3
    error     = 4

def to_top(w):
    while w.GetParent():
        w = w.GetParent()
    return w

def absolute_position(w):
    (x,y) = w.GetPosition()
    if not w.GetParent():
        return (x,y)
    else:
        (a,b) = absolute_position(w.GetParent())
        return (x+a, y+b)

def size_that_fits(recommended_size):
    (r_width, r_height) = recommended_size
    screen_width  = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
    screen_height  = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
    return (min(r_width, screen_width), min(r_height, screen_height))

def pos_for_center(size):
    (frame_width, frame_height) = size
    screen_width  = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
    screen_height  = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
    x = screen_width/2 - frame_width/2
    y = screen_height/2 - frame_height/2
    return (max(x,0),max(y,0))

def center_of_screen():
    screen_width  = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
    screen_height  = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
    return (screen_width/2, screen_height/2)

def error_dialog(message):
    dlg = wx.MessageDialog(None, message, '', wx.OK | wx.ICON_ERROR)
    dlg.ShowModal()
    dlg.Destroy()

def info_dialog(message):
    dlg = wx.MessageDialog(None, message, '', wx.OK | wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()

def open_dir_style(current_path):
    # Mac and Win32 remember directory, even after quitting program;
    # else (GTK), use our
    style = wx.OPEN
    if Mac() or Win32():
        return ('', style)
    else:
        # return (os.getcwd(), wx.OPEN | wx.CHANGE_DIR)
        if current_path:
            return (os.path.dirname(current_path), style)
        else:
            return (os.getcwd(), style)

def saveas_dir_style(current_path):
    style = wx.SAVE | wx.OVERWRITE_PROMPT
    if Win32():  # Win32 uses dir remembered from 'open'
        return ('', style)
    elif Mac():  # Mac doesn't use dir remembered from 'open'
        if current_path:
            return (os.path.dirname(current_path), style)
        else:
            return ('', wx.SAVE)
    else:        # GTK doesn't remember
        # return (os.getcwd(), style | wx.CHANGE_DIR)
        if current_path:
            return (os.path.dirname(current_path), style)
        else:
            return (os.getcwd(), style)

def max_width(strings, window):
    max_wid = 0
    for s in strings:
        width = window.GetTextExtent(s)[0]
        max_wid = max(max_wid, width)
    return max_wid

class Text_frame(wx.Frame):
    def __init__(self, parent, font, title, text,
                 extension=None, saveas=True,
                 off_center=0, saved_flag=None,
                 extra_operations=[]):
        
        size = size_that_fits((900,650))     # reduce if screen too small
        (x,y) = pos_for_center(size)         # position to center frame
        pos = (x+off_center, y+off_center)

        wx.Frame.__init__(self, parent, title=title, size=size, pos=pos)

        self.extension = extension
        self.saved_flag = saved_flag
        self.text = text

        if saveas:
            saveas_btn = wx.Button(self, -1, 'Save as...')
            self.Bind(wx.EVT_BUTTON, self.on_saveas, saveas_btn)

        extra_btns = []
        for (label,func) in extra_operations:
            btn = wx.Button(self, -1, label)
            self.Bind(wx.EVT_BUTTON, func, btn)
            extra_btns.append(btn)

        close_btn = wx.Button(self, -1, 'Close')
        self.Bind(wx.EVT_BUTTON, self.on_close, close_btn)

        self.txt = wx.TextCtrl(self,
                               style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL|
                               wx.TE_RICH2)  # TE_RICH2 allows > 32K in Win32
        self.txt.SetFont(font)
        
        self.txt.AppendText(text)
        self.txt.ShowPosition(0)
 
        sub_sizer = wx.BoxSizer(wx.HORIZONTAL)
        if saveas:
            sub_sizer.Add(saveas_btn, 0, wx.ALL, 3)
        for btn in extra_btns:
            sub_sizer.Add(btn, 0, wx.ALL, 3)
        sub_sizer.Add((0,0), 1)  # strechable space
        sub_sizer.Add(close_btn, 0, wx.ALL, 3)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sub_sizer, 0, wx.ALL|wx.GROW, 3)
        sizer.Add(self.txt, 1, wx.ALL|wx.GROW, 3)
        self.SetSizer(sizer)

    def append(self, text):
        self.txt.AppendText(text)
        self.txt.ShowPosition(self.txt.GetLastPosition())

    def on_saveas(self, evt):
        (dir,style) = saveas_dir_style(to_top(self).current_path)

        if to_top(self).current_path and self.extension:
            dfile = os.path.basename(to_top(self).current_path)
            dfile = re.sub('\.[^.]*$', '', dfile)  # get rid of any extension
            dfile = '%s.%s' % (dfile,self.extension)    # append new extension
        else:
            dfile = ''

        dlg = wx.FileDialog(self, message='Save file as ...',
                            defaultDir=dir, defaultFile=dfile, style=style)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()      # full path
            try:
                f = open(path, 'w')
                f.write(self.txt.GetValue())
                # Do not update to_top(self).current_path
                if self.saved_flag:
                    self.saved_flag[0] = True
            except IOError, e:
                error_dialog('Error opening file %s for writing.' % path)

        dlg.Destroy()

    def on_close(self, evt):
        self.Close()

    def hilite_error(self):
        start = self.txt.GetValue().find('%%START ERROR%%')
        if start > 0:
            end = self.txt.GetValue().find('%%END ERROR%%', start)
            if end > 0:
                self.txt.SetStyle(start+15, end,
                                  wx.TextAttr('RED',
                                              wx.Colour(200,200,255)))
        else:
            start = self.txt.GetValue().find('%%ERROR:')
            if start > 0:
                end = self.txt.GetValue().find('\n', start)
                if end > 0:
                    self.txt.SetStyle(start+8, end,
                                      wx.TextAttr('RED',
                                                  wx.Colour(200,200,255)))
            

# END class Text_frame(wx.Frame)

class Mini_info(wx.MiniFrame):
    def __init__(self, parent, title, items):
        
        # pos = center_of_screen()
        pos = absolute_position(parent)

        if Win32():
            style = wx.STAY_ON_TOP|wx.DEFAULT_FRAME_STYLE
        elif Mac():
            style = wx.STAY_ON_TOP|wx.CAPTION|wx.CLOSE_BOX
        else:
            style = wx.STAY_ON_TOP   # GTK ignores style for MiniFrame

        wx.MiniFrame.__init__(self, parent, title=title, pos=pos, style=style)

        # Cannot get a close button on titlebar in GTK.
        if Win32() or Mac():
            close_btn = None
        else:
            close_btn = wx.Button(self, -1, 'Close', style=wx.BU_EXACTFIT)
            self.Bind(wx.EVT_BUTTON, self.on_close, close_btn)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        gsizer = wx.GridSizer(len(items), 2)

        self.val_labels = []
        for (name,val) in items:
            name_lab = wx.StaticText(self, -1, name + ':')
            val_lab  = wx.StaticText(self, -1, str(val), size=(75,-1),
                                     style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
            self.val_labels.append(val_lab)
            gsizer.Add(name_lab, 0, wx.ALIGN_LEFT, 3)
            gsizer.Add(val_lab, 0, wx.ALIGN_RIGHT, 3)

        sizer = wx.BoxSizer(wx.VERTICAL)
        if close_btn:
            sizer.Add(close_btn, 0, wx.ALL|wx.ALIGN_RIGHT, 3)
        sizer.Add(gsizer, 0, wx.ALL|wx.ALIGN_CENTER, 3)
        self.SetSizer(sizer)
        self.Fit()
        self.Show()

    def on_close(self, evt):
        self.GetParent().info_reset()
        self.Destroy()

    def update(self, items):
        i = 0
        for (_,val) in items:
            lab = self.val_labels[i]
            lab.SetLabel(str(val))
            i += 1
        self.Fit()
        
# END class Mini_info(wx.MiniFrame)

class Invoke_event(wx.PyEvent):
    """
    This class is used so that a side thread can invoke
    a function in the main GUI thread.
    """
    my_EVT_INVOKE = wx.NewEventType()

    def __init__(self, func, args, kwargs):
        wx.PyEvent.__init__(self)
        self.SetEventType(Invoke_event.my_EVT_INVOKE)
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs

    def invoke(self):
        self.__func(*self.__args, **self.__kwargs)

# END class Invoke_event(PyEvent)

class Busy_bar(wx.Gauge):

    def __init__(self, parent, width=200, height=16,
                 pixels_to_move=2, fill=.9, delay=200):

        wx.Gauge.__init__(self, parent, range=100, size=(width,height))

        self.delay = delay
        self.range = range
        self.state = State.ready
        self.position = 40
        self.direction = 1

    def update_bar(self, evt):
        # This is run periodically, triggered by the timer in self.start().

        self.position += self.direction
        if self.position >= 60:
            self.direction = -1
        elif self.position <= 40:
            self.direction = 1

        self.SetValue(self.position)

    def start(self):
        self.timer = wx.Timer(self, -1)
        wx.EVT_TIMER(self, self.timer.GetId(), self.update_bar)
        self.timer.Start(self.delay)
        self.state = State.running

    def pause(self):
        self.timer.Stop()
        self.state = State.suspended

    def resume(self):
        self.start()
        
    def stop(self):
        self.timer.Stop()
        self.SetValue(0)
        self.position = 40
        self.direction = 1
        self.state = State.ready

# END class Busy_bar(Guage)

