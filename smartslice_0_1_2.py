
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import json, zipfile, tempfile, shutil, datetime, math
import trimesh

APP="SmartSlice 0.1.2"
class App:
    def __init__(self,root):
        self.root=root; root.title(APP+" — Offline Proof of Concept"); root.geometry("760x660")
        self.mesh=None; self.path=None; self.suggestions=[]
        self.purpose=tk.StringVar(value="Decorative")
        self.priority=tk.StringVar(value="Balanced")
        self.filament=tk.StringVar(value="Generic PLA")
        self.fuzzy=tk.BooleanVar(value=False)
        self.ironing=tk.BooleanVar(value=False)
        self.arachne=tk.BooleanVar(value=False)
        self.log=[]
        outer=ttk.Frame(root,padding=16); outer.pack(fill="both",expand=True)
        ttk.Label(outer,text="SmartSlice 0.1",font=("Segoe UI",19,"bold")).pack(anchor="w")
        ttk.Label(outer,text="Offline geometry analysis + experimental 3MF project settings • Bambu P2S target").pack(anchor="w",pady=(0,12))
        ttk.Button(outer,text="Import STL or 3MF…",command=self.load).pack(fill="x")
        self.filename=ttk.Label(outer,text="No file loaded"); self.filename.pack(anchor="w",pady=6)
        self.geometry=ttk.Label(outer,text=""); self.geometry.pack(anchor="w")
        form=ttk.Frame(outer); form.pack(fill="x",pady=10)
        for i,(label,var,values) in enumerate([
            ("Use case",self.purpose,["Decorative","Functional"]),
            ("Priority",self.priority,["Fast","Balanced","Quality"]),
            ("Filament (local baseline)",self.filament,["Generic PLA","Generic PETG","Generic TPU","Foaming TPU (unverified)"])]):
            ttk.Label(form,text=label).grid(row=0,column=i,sticky="w",padx=(0,8))
            cb=ttk.Combobox(form,textvariable=var,values=values,state="readonly",width=23)
            cb.grid(row=1,column=i,sticky="ew",padx=(0,8))
            cb.bind("<<ComboboxSelected>>",lambda e:self.analyze())
            form.columnconfigure(i,weight=1)
        exp=ttk.LabelFrame(outer,text="＋ Optional enhancements",padding=8); exp.pack(fill="x",pady=5)
        for i,(name,var) in enumerate([("Fuzzy skin",self.fuzzy),("Ironing",self.ironing),("Arachne walls",self.arachne)]):
            ttk.Checkbutton(exp,text=name,variable=var,command=self.analyze).grid(row=0,column=i,sticky="w",padx=12)
        ttk.Button(outer,text="Analyze / refresh recommendations",command=self.analyze).pack(fill="x",pady=8)
        self.output=tk.Text(outer,height=13,wrap="word",font=("Consolas",10)); self.output.pack(fill="both",expand=True)
        bar=ttk.Frame(outer); bar.pack(fill="x",pady=10)
        ttk.Button(bar,text="Save experimental 3MF…",command=self.export).pack(side="left",fill="x",expand=True,padx=(0,5))
        ttk.Button(bar,text="Research / decision log…",command=self.show_log).pack(side="left",fill="x",expand=True)
        ttk.Label(outer,text="No internet access. No slicing. Review all imported settings in Bambu Studio before printing.",foreground="#865a00").pack(anchor="w")
    def note(self,kind,message):
        self.log.append({"time":datetime.datetime.now().isoformat(timespec="seconds"),"type":kind,"message":message,"source":"Local geometry heuristic / user selection (not internet verified)"})
    def load(self):
        path=filedialog.askopenfilename(filetypes=[("3D files","*.stl *.3mf"),("All files","*.*")])
        if not path:return
        try:
            obj=trimesh.load(path,force="scene")
            meshes=[g.copy() for g in obj.dump() if isinstance(g,trimesh.Trimesh)]
            if not meshes: raise ValueError("No mesh found")
            mesh=trimesh.util.concatenate(meshes)
            if len(mesh.faces)==0:raise ValueError("Empty mesh")
            self.mesh=mesh;self.path=Path(path)
            self.filename.config(text=self.path.name)
            self.geometry.config(text=f"Bounds: {mesh.extents[0]:.1f} × {mesh.extents[1]:.1f} × {mesh.extents[2]:.1f} mm  |  Triangles: {len(mesh.faces):,}")
            self.note("import",f"Loaded {self.path.name}; geometry only. Existing 3MF print settings are NOT preserved.")
            self.analyze()
        except Exception as e: messagebox.showerror("Import failed",str(e))
    def analyze(self):
        if self.mesh is None:
            self.output.delete("1.0","end");self.output.insert("end","Import a model to begin.");return
        ext=self.mesh.extents
        # Consider rotations that align each of the three bounding-box axes with Z.
        candidates=[]
        for axis in range(3):
            height=float(ext[axis]); dims=[float(ext[j]) for j in range(3) if j!=axis]
            footprint=dims[0]*dims[1]
            slender=height/max(min(dims),0.01)
            # simple heuristic; no unsupported claims of overhang analysis
            score=footprint/(1+0.15*max(0,slender-2))
            candidates.append((score,axis,height,footprint,slender))
        best=max(candidates)
        axis=best[1]
        # Rotate original geometry so selected axis becomes Z; preserve handedness.
        transforms={
            0:trimesh.transformations.rotation_matrix(-math.pi/2,[0,1,0]),
            1:trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]),
            2:trimesh.transformations.identity_matrix()
        }
        self.oriented=self.mesh.copy()
        self.oriented.apply_transform(transforms[axis])
        self.oriented.apply_translation(-self.oriented.bounds[0])
        priority=self.priority.get();purpose=self.purpose.get()
        layer={"Fast":0.28,"Balanced":0.20,"Quality":0.12}[priority]
        walls=3 if purpose=="Functional" else 2
        density="15%" if purpose=="Functional" else "8%"
        pattern="adaptivecubic"
        # Treat foaming TPU as unknown and do not prescribe unverified temperatures/flow.
        self.settings={
            "layer_height":str(layer),"wall_loops":str(walls),
            "sparse_infill_density":density,"sparse_infill_pattern":pattern,
            "wall_generator":"arachne" if self.arachne.get() else "classic",
            "fuzzy_skin":"external" if self.fuzzy.get() else "none",
            "ironing_type":"top" if self.ironing.get() else "no ironing",
        }
        lines=[
            f"MODEL: {self.path.name}",
            f"PRINTER TARGET: Bambu P2S (compatibility NOT validated)",
            f"MATERIAL: {self.filament.get()} (selection only; no verified temperature/flow profile)",
            f"ORIENTATION: candidate axis {['X','Y','Z'][axis]} vertical; estimated height {best[2]:.1f} mm",
            "  Bounding-box stability heuristic only; does NOT detect overhangs or strength direction.",
            "",
            "PROPOSED PROCESS SETTINGS:"
        ]
        lines += [f"  {k}: {v}" for k,v in self.settings.items()]
        lines += ["","CAUTION: No actual slicing or time estimates. Settings are experimental.",
                  "3MF export is a generic geometry package with a best-effort Bambu",
                  "project_settings.config. Bambu Studio may ignore these settings.",
                  "Verify the loaded printer, filament, and EVERY setting before printing.",
                  "Imported 3MF modifiers, painted supports, colors and other metadata are lost."]
        self.output.delete("1.0","end");self.output.insert("end","\n".join(lines))
        self.note("recommendation",f"{purpose}/{priority}; orientation axis {axis}; {self.settings}")
    def export(self):
        if self.mesh is None:return messagebox.showinfo("No model","Import a model first.")
        name=self.path.stem+"_SmartSlice_experimental.3mf"
        dest=filedialog.asksaveasfilename(defaultextension=".3mf",initialfile=name,filetypes=[("3MF project","*.3mf")])
        if not dest:return
        try:
            data=self.oriented.export(file_type="3mf")
            # Repackage to add experimental Bambu Studio project configuration.
            with zipfile.ZipFile(__import__("io").BytesIO(data),"r") as src:
                files={n:src.read(n) for n in src.namelist()}
            files["Metadata/project_settings.config"]=json.dumps(self.settings,indent=2).encode()
            files["Metadata/SmartSlice_recommendations.json"]=json.dumps({
                "application":APP,"printer_target":"Bambu P2S","filament_selection":self.filament.get(),
                "purpose":self.purpose.get(),"priority":self.priority.get(),
                "settings":self.settings,"warning":"Experimental. Bambu Studio settings may not import. Verify manually.",
                "source":"Local heuristics, no online research"
            },indent=2).encode()
            with zipfile.ZipFile(dest,"w",zipfile.ZIP_DEFLATED) as out:
                for name,content in files.items():out.writestr(name,content)
            self.note("export",f"Exported experimental 3MF to {dest}")
            messagebox.showinfo("Saved","Experimental 3MF saved.\n\nOpen it in Bambu Studio and verify all settings. No compatibility validation has been performed.")
        except Exception as e:messagebox.showerror("Export failed",str(e))
    def show_log(self):
        win=tk.Toplevel(self.root);win.title("SmartSlice — Research & Decision Log");win.geometry("720x460")
        t=tk.Text(win,wrap="word");t.pack(fill="both",expand=True)
        t.insert("end",json.dumps(self.log,indent=2));t.config(state="disabled")
        def save():
            p=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")])
            if p:Path(p).write_text(json.dumps(self.log,indent=2),encoding="utf-8")
        ttk.Button(win,text="Export log JSON…",command=save).pack(fill="x")
if __name__=="__main__":
    root=tk.Tk()
    App(root)
    root.mainloop()
