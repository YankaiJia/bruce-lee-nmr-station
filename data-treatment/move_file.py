# i need to move the subfolder to the main folder, do it with python
# i will use the shutil library to move the files
import shutil
import os

path = 'D:\\Dropbox\\brucelee\\data\\DPE_bromination\\2025-02-19-run01_time_varied\\Results\\_000'
folders = os.listdir(path)
print(folders)
for folder in folders:
    # get subfolder path
    subfolder = os.path.join(path, folder)
    # get files in subfolder
    files = os.listdir(subfolder)
    for file in files:
        # get file path
        file_path = os.path.join(subfolder, file)
        # move file to main folder
        shutil.move(file_path, path)
