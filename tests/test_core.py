
import json, tempfile, unittest, zipfile
from pathlib import Path
from smartslice_core import read_project, preview, save_project, ProjectError, CONFIG

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source=Path(self.temp.name)/"original.3mf"
        self.output=Path(self.temp.name)/"optimized.3mf"
        with zipfile.ZipFile(self.source,"w") as f:
            f.writestr("[Content_Types].xml",b"<Types/>")
            f.writestr("3D/3dmodel.model",b"<model>DO NOT TOUCH</model>")
            f.writestr("Metadata/plate_1.json",b'{"painted_supports":"preserve"}')
            f.writestr(CONFIG,json.dumps({
                "sparse_infill_density":"15%",
                "sparse_infill_pattern":"rectilinear",
                "wall_loops":"2",
                "layer_height":"0.20",
                "machine":"P2S",
                "unknown_setting":{"preserve":True}
            }))
    def test_round_trip_changes_settings_only(self):
        changes=save_project(self.source,self.output,"Decorative","Balanced")
        self.assertIn("sparse_infill_density",changes)
        self.assertEqual(read_project(self.output)["sparse_infill_density"],"8%")
        self.assertEqual(read_project(self.output)["sparse_infill_pattern"],"adaptivecubic")
        self.assertEqual(read_project(self.output)["unknown_setting"],{"preserve":True})
        with zipfile.ZipFile(self.source) as a,zipfile.ZipFile(self.output) as b:
            self.assertEqual(a.namelist(),b.namelist())
            for name in a.namelist():
                if name != CONFIG:self.assertEqual(a.read(name),b.read(name))
    def test_original_unchanged(self):
        before=self.source.read_bytes()
        save_project(self.source,self.output,"Functional","Quality")
        self.assertEqual(self.source.read_bytes(),before)
    def test_reject_stl(self):
        path=Path(self.temp.name)/"model.stl";path.write_text("solid cube")
        with self.assertRaises(ProjectError):read_project(path)
    def test_reject_non_bambu_3mf(self):
        with zipfile.ZipFile(self.source,"w") as f:f.writestr("3D/3dmodel.model","mesh")
        with self.assertRaises(ProjectError):read_project(self.source)
    def test_no_overwrite(self):
        with self.assertRaises(ProjectError):save_project(self.source,self.source,"Decorative","Balanced")
        self.output.write_bytes(b"existing")
        with self.assertRaises(FileExistsError):save_project(self.source,self.output,"Decorative","Balanced")
        self.assertEqual(self.output.read_bytes(),b"existing")
    def test_no_new_keys(self):
        with zipfile.ZipFile(self.source,"w") as f:
            f.writestr(CONFIG,json.dumps({"wall_loops":"2"}))
        save_project(self.source,self.output,"Functional","Balanced")
        self.assertEqual(read_project(self.output),{"wall_loops":"3"})
if __name__=="__main__":unittest.main()
