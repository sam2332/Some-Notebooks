#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import shutil
import re
from zipfile import ZipFile,ZIP_DEFLATED


# In[17]:


file = 'unlockme.xlsx'
input('name file "unlockme.xlsx"')
shutil.copyfile(file,'tmp.zip')
tmpfile = 'tmp.zip'
dest= 'unprotected.xlsx'


# In[23]:


def main():
    debug = True
    with ZipFile(tmpfile, 'r') as zipread:
        Protection_files = []
        for fn in zipread.filelist:
            data = zipread.read(fn)
            if b'sheetProtection' in data:
                if debug:
                    print(fn)
                Protection_files.append(fn.filename)
        
        if len(Protection_files):
            print('Found Password Protected Sheets')
            for Protection_file in Protection_files:
                data = zipread.read(Protection_file)
                with ZipFile(dest, 'w', ZIP_DEFLATED) as zipwrite:
                    for fn in zipread.filelist:
                        if debug:
                            print(fn.filename)
                        if fn.filename not in Protection_files:
                            zipwrite.writestr(fn.filename, zipread.read(fn.filename))
                        else:
                            start = data.find(b'<sheetProtection')
                            inquotes= False
                            end = 0
                            for letter_id in range(start,len(data)):
                                letter = chr(data[letter_id])
                                if debug:
                                    print(letter_id,letter)
                                if inquotes:
                                    if letter=='"':
                                        inquotes = False
                                else:
                                    if letter == '"':
                                        inquotes = True
                                    if letter == '/':
                                        end = letter_id  +2
                                        break
                            if debug:
                                print((start,end))
                            print('updating "{}"'.format(fn.filename))
                            new_file_data = data[:start] + data[end:]
                            zipwrite.writestr(fn.filename,new_file_data)
            print('removed password from: "{}" saved as: "{}"'.format(file,dest))
        else:
            print('not password protected')
main()

# In[ ]:




