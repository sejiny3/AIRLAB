"""Fill the KSME template through Hancom Office's COM interface."""
import os
import re
import shutil

import pythoncom
import win32com.client as win32

STYLE = {'body': 12, 'chapter': 13, 'section': 14, 'item': 15, 'fig': 16, 'table': 17, 'ack': 18, 'ref_title': 19,
         'ref': 20, 'eq': 23, 'normal': 0, 'notation_title': 11, 'center': 6}


class Doc:
    def __init__(self, src):
        pythoncom.CoInitialize()
        self.h = win32.Dispatch('HWPFrame.HwpObject')
        self.h.SetMessageBoxMode(0x00010000)  # answer every message box with OK
        # a Hwp.exe that is still closing locks the file it had, and the next open is then read-only
        self.work = os.path.abspath(f'work_{os.getpid()}.hwp')
        shutil.copy(src, self.work)
        if not self.h.Open(self.work, 'HWP', 'forceopen:true;lock:false'):
            raise RuntimeError('could not open ' + src)
        if self.h.EditMode != 1:
            raise RuntimeError(f'{src} opened read-only')

    def replace_all(self, find, text):
        h = self.h
        act = h.HAction
        pset = h.HParameterSet.HFindReplace
        act.GetDefault('AllReplace', pset.HSet)
        pset.FindString, pset.ReplaceString = find, text
        pset.IgnoreMessage = 1
        pset.Direction = h.FindDir('AllDoc')
        pset.FindRegExp = 0
        return act.Execute('AllReplace', pset.HSet)

    def style(self, name):
        h = self.h
        act = h.CreateAction('Style')
        s = act.CreateSet()
        act.GetDefault(s)
        if s.Item('Apply') != STYLE[name]:  # applying the style a paragraph already has hangs Hancom
            s.SetItem('Apply', STYLE[name])
            act.Execute(s)
        h.Run('CharShapeNormal')  # the caret keeps bold from whatever was typed before

    def set_text(self, lst, para, text, start=0, end=None, black=False):
        """Replace part of one paragraph, keeping its style and the shape at the start of the range."""
        h = self.h
        h.SetPos(lst, para, 0)
        h.HAction.Run('MoveParaEnd')
        if end is None:
            end = h.GetPos()[2]
        h.SetPos(lst, para, start)
        if end > start:
            h.SelectText(para, start, para, end)
            h.HAction.Run('Delete')
        self.rich(text)
        stop = h.GetPos()[2]
        h.Run('Cancel')
        if black and stop > start:  # the part being replaced may end in the template's blue notes
            h.SelectText(para, start, para, stop)
            self.black()
            h.Run('Cancel')

    def black(self):
        h = self.h
        h.HAction.GetDefault('CharShape', h.HParameterSet.HCharShape.HSet)
        h.HParameterSet.HCharShape.TextColor = h.RGBColor(0, 0, 0)
        h.HAction.Execute('CharShape', h.HParameterSet.HCharShape.HSet)

    def align(self, kind):
        """0 justify, 1 left, 2 right, 3 centre."""
        h = self.h
        act = h.CreateAction('ParagraphShape')
        p = act.CreateSet()
        act.GetDefault(p)
        p.SetItem('AlignType', kind)
        act.Execute(p)

    def clear_from(self, para):
        """Delete the main list after this paragraph and empty it. Deleting through the end of the
        document would leave the last paragraph's direct formatting, which styles do not reset."""
        h = self.h
        h.HAction.Run('MoveDocEnd')
        last, end = h.GetPos()[1:]
        h.SetPos(0, para + 1, 0)
        h.SelectText(para + 1, 0, last, end)
        h.HAction.Run('Delete')
        h.Run('Cancel')
        h.SetPos(0, para + 1, 0)
        h.HAction.Run('DeleteBack')
        h.Run('Cancel')
        self.set_text(0, para, '')

    def keep_with_next(self, with_next=True):
        """Headings and table captions stay with the next paragraph; the paragraph's lines also stay on one page
        (a caption split across pages is what KeepLines prevents)."""
        act = self.h.CreateAction('ParagraphShape')
        p = act.CreateSet()
        act.GetDefault(p)
        if with_next:
            p.SetItem('KeepWithNext', 1)
        try:
            p.SetItem('KeepLines', 1)
        except Exception as e:  # an unknown item name must not stop the build
            print('KeepLines not set:', e)
        act.Execute(p)

    def raw(self, text):
        h = self.h
        h.HAction.GetDefault('InsertText', h.HParameterSet.HInsertText.HSet)
        h.HParameterSet.HInsertText.Text = text
        h.HAction.Execute('InsertText', h.HParameterSet.HInsertText.HSet)

    def rich(self, text):
        """Text with ^{sup}, _{sub}, *{italic} and ~{bold} marks."""
        for part in re.split(r'(\^\{[^}]*\}|_\{[^}]*\}|\*\{[^}]*\}|~\{[^}]*\})', text):
            if not part:
                continue
            toggle = {'^{': 'CharShapeSuperscript', '_{': 'CharShapeSubscript', '*{': 'CharShapeItalic', '~{': 'CharShapeBold'}.get(part[:2])
            if toggle:
                self.h.Run(toggle)
                self.raw(part[2:-1])
                self.h.Run(toggle)
            else:
                self.raw(part)

    def para(self, style, text):
        self.style(style)
        self.rich(text)
        para = self.h.GetPos()[1]
        self.h.Run('BreakPara')
        if style in ('chapter', 'section', 'table', 'fig', 'ref_title', 'ack'):  # set last, so the next paragraph does not inherit it
            self.h.SetPos(0, para, 0)
            self.keep_with_next(style != 'fig')
            self.h.Run('Cancel')
            self.h.Run('MoveDocEnd')

    def equation(self, script, number):
        """Flush right, with the number at the column edge."""
        self.style('eq')
        h = self.h
        para = h.GetPos()[1]
        h.HAction.GetDefault('EquationCreate', h.HParameterSet.HEqEdit.HSet)
        h.HParameterSet.HEqEdit.string = script
        h.HParameterSet.HEqEdit.BaseUnit = h.PointToHwpUnit(10.0)
        h.HAction.Execute('EquationCreate', h.HParameterSet.HEqEdit.HSet)
        ctrl = h.LastCtrl
        prop = ctrl.Properties
        prop.SetItem('TreatAsChar', True)
        ctrl.Properties = prop
        h.Run('Cancel')
        h.Run('MoveDocEnd')
        self.raw(f'     ({number})')
        h.Run('BreakPara')
        h.SetPos(0, para, 0)  # aligned last, so the next paragraph does not inherit it
        self.align(2)
        h.Run('Cancel')
        h.Run('MoveDocEnd')

    def picture(self, path, width_mm, height_mm):
        self.style('center')
        h = self.h
        para = h.GetPos()[1]
        ctrl = h.InsertPicture(os.path.abspath(path), True, 1, False, False, 0, width_mm, height_mm)
        h.Run('Cancel')
        h.Run('MoveDocEnd')
        h.Run('BreakPara')
        h.SetPos(0, para, 0)
        self.keep_with_next()
        h.Run('Cancel')
        h.Run('MoveDocEnd')
        return ctrl

    def table(self, rows, widths):
        """rows: list of lists of cell text, the first row is the header; widths: column widths [mm]."""
        h = self.h
        self.style('center')
        act = h.CreateAction('TableCreate')
        t = act.CreateSet()
        act.GetDefault(t)
        t.SetItem('Rows', len(rows))
        t.SetItem('Cols', len(rows[0]))
        t.SetItem('WidthType', 2)
        t.SetItem('HeightType', 0)
        t.SetItem('WidthValue', h.MiliToHwpUnit(sum(widths)))
        cols = t.CreateItemArray('ColWidth', len(widths))
        for i, w in enumerate(widths):
            cols.SetItem(i, h.MiliToHwpUnit(w))
        act.Execute(t)
        ctrl = h.LastCtrl
        prop = ctrl.Properties
        prop.SetItem('TreatAsChar', True)
        ctrl.Properties = prop
        h.SetPosBySet(ctrl.GetAnchorPos(0))
        h.FindCtrl()
        h.Run('ShapeObjTableSelCell')
        h.Run('Cancel')
        for i, row in enumerate(rows):
            for j, cell in enumerate(row):
                self.style('center')
                self.rich(cell)
                if not (i == len(rows) - 1 and j == len(row) - 1):
                    h.Run('TableRightCell')
        h.Run('Cancel')
        h.Run('MoveDocEnd')
        pos = h.GetPos()
        print('after table: caret', pos, flush=True)
        if pos[2] > 0:  # still in the table's paragraph; at 0 Hancom already left an empty paragraph after the table
            h.Run('BreakPara')

    def save(self, path, fmt='HWP'):
        return self.h.SaveAs(os.path.abspath(path), fmt, '')

    def close(self):
        self.h.Clear(1)
        self.h.Quit()
        try:
            os.remove(self.work)
        except OSError:
            pass
