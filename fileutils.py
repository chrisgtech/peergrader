import logging
logger = logging.getLogger(__name__)

import os
import shutil
import shlex
import subprocess
import webbrowser
import sys
import tempfile
import getpass
from uuid import uuid4

def yesno(question, default="yes"):
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    if default == None:
        choices = " [y/n] "
    elif default == "yes":
        choices = " [Y/n] "
    elif default == "no":
        choices = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        choice = prompt(question + choices).lower().strip()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            logger.error("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")

def menu(question, choices):
    if len(choices) < 1:
        return None
    while True:
        for index, choice in enumerate(choices):
            print '%s. %s' % (index + 1, choice)
        response = prompt('%s (1-%s)' % (question, len(choices)))
        if response.isdigit():
            choiceindex = int(response) - 1
            if -1 < choiceindex < len(choices):
                return choices[choiceindex]
            else:
                logger.error('Invalid choice: "%s"' % response)
        else:
            logger.error('Count not understand choice: "%s"' % response)

def prompt(question='', default=None, password=False, repromptcheck=None):
    print '\n'
    prompt = question
    
    while True:
        if default:
            prompt = '%s [%s]' % (prompt, default)
        prompt += ': '
        response = ''
        
        if password:
            response = getpass.getpass(prompt)
        else:
            sys.stdout.write(prompt)
            print '\n'
            response = raw_input()
        
        if response == '' and default:
            response = default
        
        if repromptcheck:
            reprompt = repromptcheck(response)
            if reprompt:
                prompt = '%s\n%s' % (reprompt, question)
                continue
                
        return response
            
                             
def clipboardcopy(text):
    import pyperclip
    pyperclip.copy(text)
    
def clipboardpaste():
    import pyperclip
    return pyperclip.paste()
    
def uuid():
    return uuid4().hex
    
def tempfolder(unique=False):
    temp = tempfile.gettempdir()
    if unique:
        id = uuid()
        temp = joinpath(temp, id)
        createdirs(temp)
    return temp
    
def home():
    return os.path.expanduser("~")
    
def browse(url):
    webbrowser.open(url)

def getfiles(path, includeexts=None, excludeexts=None):
    includeexts = includeexts or []
    excludeexts = excludeexts or []
    logger.debug('Getting files from %s' % path)
    files = []
    checkinclude, checkexclude = (len(includeexts)>0), (len(excludeexts)>0)
    checkext = checkinclude or checkexclude
    for dirname, dummydirnames, filenames in os.walk(path):
        for filename in filenames:
            excludefile = False
            if checkext:
                ext = os.path.splitext(filename)[1]
                if (checkinclude and not ext in includeexts) or (checkexclude and ext in excludeexts):
                    excludefile = True
            if not excludefile:
                files.append(os.path.join(dirname, filename))
    return files

def splitpath(path):
    folders = []
    while True:
        path, folder = os.path.split(path)
        if folder != '':
            folders.append(folder)
        else:
            if path != '':
                folders.append(path)
            break
    folders.reverse()
    return folders
    
def joinpath(path1, path2):
    return os.path.join(path1, path2)
    
def folderpath(path):
    return os.path.normpath(path) + os.sep
    
def changeextension(file, newextension):
    filename, fileextension = os.path.splitext(file)
    return filename + newextension

def fileinsourcedir(filename):
    sourcedir = os.path.dirname(__file__)
    absdir = os.path.abspath(sourcedir)
    return os.path.join(absdir, filename)
    
def prettyprint(obj):
    import yaml
    print yaml.dump(obj, default_flow_style=False)
    
def dumppath(filename):
    import yaml
    ext = os.path.splitext(filename)[-1].lower()
    if ext != os.path.extsep + 'yaml':
        filename = filename + os.path.extsep + 'yaml'
    return filename

def dump(obj, filename, pretty=True):
    import yaml
    filename = dumppath(filename)
    text = yaml.dump(obj, default_flow_style=not pretty)
    savetext(text, filename)
    
def load(filename):
    import yaml
    filename = dumppath(filename)
    if not exists(filename):
        return None
    with open(filename) as yamlfile:
        return yaml.load(yamlfile)
    
def savetext(text, filename):
    with open(filename, 'w') as textfile:
        textfile.write(text)
    
def loadtext(filename):
    with open(filename) as textfile:
        return textfile.readlines()
    
def appendline(text, filename):
    with open(filename, 'a') as textfile:
        textfile.write(text + '\n')

def currentdirectory():
    return os.getcwd()

def fullpath(filename):
    return os.path.realpath(filename)

def filenameof(path, ext=True):
    name = os.path.basename(path)
    if not ext:
       name = os.path.splitext(name)[0]
    return name
    
def basename(path):
    return os.path.basename(os.path.normpath(path))
    
def parentdirectory(path):
    return os.path.dirname(path)
    
def fileextension(file, stripdot=False):
    filename, fileextension = os.path.splitext(file)
    if stripdot:
        fileextension = fileextension.split(os.extsep)[-1] 
    return fileextension

def runfile(filename):
    logger.debug('Running file %s' % filename)
    os.startfile(filename)

def runprogram(args):
    logger.debug('Running program %s' % args)
    os.system(args)

def execute(args):
    logger.debug('Executing %s' % args)
    process = executestart(args)
    (out,err) = process.communicate()
    #process.wait()
    return {'stdout':out, 'stderr':err}

def executestart(args):
    logger.debug('Execute starting %s' % args)
    if osname() == 'nt':
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        process = subprocess.Popen(shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process

class ExecutionException(Exception):
    def __init__(self, message, output):
        Exception.__init__(self, message)
        self.output = output
        
def osname():
    return os.name

def copy(src, dst):
    shutil.copy2(src, dst)

def move(src, dst):
    logger.info('Moving %s to %s' % (src, dst))
    copy(src, dst)
    delete(src)

def rename(oldname, newname):
    os.rename(oldname, newname)

def delete(filename):
    os.remove(filename)
    
def deletefolder(path):
    shutil.rmtree(path)

def exists(filename):
    return os.path.isfile(filename)

def direxists(path):
    return os.path.isdir(path)
    
def createdirs(path):
    if not direxists(path):
        os.makedirs(path)
    
def filesize(filename):
    return filestats(filename).st_size

def filestats(filename):
    return os.stat(filename)

def freespace(directory):
    import platform
    if platform.system() == 'Windows':
        import ctypes
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(directory), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value
    else:
        stats = os.statvfs(directory)
        return stats.f_bfree * stats.f_frsize
