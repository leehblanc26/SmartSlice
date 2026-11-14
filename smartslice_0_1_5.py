
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import json, datetime
from smartslice_core import read_project, preview, save_project, ProjectError

class SmartSlice:
    def __init__(self,root):
        self.root=root; root.title("SmartSlice 0.1.5 — Settings-only experiment"); root.geometry("760x580")
        self.path=None; self.log=[]
        self.purpose=tk.StringVar(value="Decorative")
        self.priority=tk.StringVar(value="Balanced")
        box=ttk.Frame(root,padding=18);box.pack(fill="both",expand=True)
        ttk.Label(box,text="SmartSlice 0.1.5",font=("Segoe UI",20,"bold")).pack(anchor="w")
        ttk.Label(box,text="Offline Bambu Studio 3MF settings editor — geometry untouched").pack(anchor="w",pady=(0,14))
        ttk.Button(box,text="Open Bambu Studio 3MF…",command=self.open).pack(fill="x")
        self.file_label=ttk.Label(box,text="No project loaded");self.file_label.pack(anchor="w",pady=8)
        row=ttk.Frame(box);row.pack(fill="x",pady=8)
        for col,(label,var,choices) in enumerate((("Purpose",self.purpose,("Decorative","Functional")),("Goal",self.priority,("Fast","Balanced","Quality")))):
            ttk.Label(row,text=label).grid(row=0,column=col,sticky="w")
            combo=ttk.Combobox(row,textvariable=var,values=choices,state="readonly")
            combo.grid(row=1,column=col,sticky="ew",padx=(0,10))
            combo.bind("<<ComboboxSelected>>",lambda event:self.refresh())
            row.columnconfigure(col,weight=1)
        ttk.Label(box,text="Changes proposed (only settings already present in the 3MF):").pack(anchor="w")
        self.text=tk.Text(box,height=14,font=("Consolas",10),wrap="word");self.text.pack(fill="both",expand=True,pady=7)
        ttk.Button(box,text="Save modified 3MF as new file…",command=self.save).pack(fill="x",pady=5)
        ttk.Button(box,text="View session decision log…",command=self.show_log).pack(fill="x")
        ttk.Label(box,text="No STL import, no mesh processing, no internet, no slicing. Confirm changes in Bambu Studio.",foreground="#815800").pack(anchor="w",pady=8)
        self.refresh()
    def record(self,kind,details):
        self.log.append({"time":datetime.datetime.now().isoformat(timespec="seconds"),"event":kind,"details":details,"source":"Local experimental preset; no internet research"})
    def open(self):
        path=filedialog.askopenfilename(title="Select a Bambu Studio 3MF project", filetypes=[("3MF project files", "*.3mf"), ("All files", "*.*")])
        if not path:return
        try:
            data=read_project(path)
            self.path=Path(path);self.file_label.config(text=self.path.name)
            self.record("import",f"Project loaded; {len(data)} configuration keys")
            self.refresh()
        except Exception as exc:messagebox.showerror("Cannot open project",f"Selected file: {Path(path).name}\n\n{exc}")
    def refresh(self):
        self.text.delete("1.0","end")
        if not self.path:
            self.text.insert("end","Open a 3MF saved as a project by Bambu Studio.\n\nThis version does not load STL files or touch model geometry.")
            return
        try:
            changes=preview(self.path,self.purpose.get(),self.priority.get())
            if not changes:
                self.text.insert("end","No changes applicable. Project may already match the selected settings.")
            else:
                for key,(old,new) in changes.items():
                    self.text.insert("end",f"{key}\n  Current: {old}\n  Proposed: {new}\n\n")
            self.text.insert("end","\nThese are experimental rules, NOT filament-calibrated recommendations.\n")
            self.text.insert("end","Printer/filament profiles, supports, speeds and all model data remain unchanged.\n")
            self.text.insert("end","Bambu Studio may override project values through its profile inheritance.")
        except Exception as exc:self.text.insert("end",f"Error: {exc}")
    def save(self):
        if not self.path:return messagebox.showinfo("Open a project","Load a Bambu Studio 3MF first.")
        destination=filedialog.asksaveasfilename(defaultextension=".3mf",initialfile=self.path.stem+"_SmartSlice_0.1.5.3mf",filetypes=[("3MF","*.3mf")])
        if not destination:return
        try:
            changes=save_project(self.path,destination,self.purpose.get(),self.priority.get())
            self.record("export",{"output":destination,"changes":changes})
            messagebox.showinfo("Saved","3MF saved and unchanged archive entries verified.\n\nOpen it in Bambu Studio to verify the settings and geometry.")
        except FileExistsError:messagebox.showerror("File exists","Choose a new output filename. Existing files are never overwritten.")
        except Exception as exc:messagebox.showerror("Export failed",str(exc))
    def show_log(self):
        window=tk.Toplevel(self.root);window.title("SmartSlice session log");window.geometry("680x450")
        area=tk.Text(window,wrap="word");area.pack(fill="both",expand=True)
        area.insert("end",json.dumps(self.log,indent=2));area.config(state="disabled")
        def export():
            path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")])
            if path:Path(path).write_text(json.dumps(self.log,indent=2),encoding="utf-8")
        ttk.Button(window,text="Export JSON log…",command=export).pack(fill="x")
if __name__=="__main__":
    root=tk.Tk();SmartSlice(root);root.mainloop()
