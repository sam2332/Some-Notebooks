import shutil

try:
    shutil.copytree(r"..\\Templates", r".\\dist\\App\\Templates")
except Exception as e:
    print(e)
try:
    shutil.copytree(r"..\\Documentation", r".\\dist\\App\\Documentation")
except Exception as e:
    print(e)

from pathlib import Path




import os
import zipfile

version = open("version.txt", "r").read()


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(
                os.path.join(root, file),
                os.path.relpath(os.path.join(root, file), os.path.join(path, "..")),
            )


Zip_Name = f"App_{version}.zip"
try:
    os.unlink(Zip_Name)
except Exception as e:
    print(e)

zipf = zipfile.ZipFile(Zip_Name, "w", zipfile.ZIP_DEFLATED, compresslevel=9)
zipdir("./dist/App", zipf)
zipf.close()
