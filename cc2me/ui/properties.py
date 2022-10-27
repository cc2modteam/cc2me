import tkinter


class Properties:
    def __init__(self, parent):
        self.parent = parent
        self.frame = tkinter.Frame(self.parent, relief=tkinter.SUNKEN)
        self.title = tkinter.Variable(self.frame, value="aaa")
        self.title_label = tkinter.Label(self.frame,
                                         textvariable=self.title,
                                         width=20,
                                         height=10,
                                         bg="#ff0000")
        self.title_label.pack(side=tkinter.TOP, expand=True, fill=tkinter.Y)
