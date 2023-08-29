from random import betavariate
from sys import implementation
from types import new_class

from charset_normalizer import CharsetNormalizerMatches
from sqlalchemy import false
from logger import Logger
import subprocess
import shutil
import re
import os 

class Helper:

    def __init__(self):
        self.config_w_file, self.config = {}, {}
        self.aux = Aux()
        self.work_directory = os.path.join(os.getcwd(), "work")
        self.old_apk_directory = os.path.join(self.work_directory, "old_apk")
        self.new_apk_directory = os.path.join(self.work_directory, "new_apk")
        self.old_smali_directory = os.path.join(self.work_directory, "old_smali")
        self.new_smali_directory =  os.path.join(self.work_directory, "new_smali")

    def folder_rm_exists(self, folder_path):
        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path)   
        
    def gen_new_hooks(self, results, old_hooks, new_hooks):
        text_in = open(old_hooks, "r").read()
        file_out = open(new_hooks, "w")
        text_out, custom_line = "", ""
        found = False
        for line in text_in.splitlines():
            for k, v in results.items() :
                (old_class, old_method) = k
                single_quote_old_class = f"Java.use('{self.aux.smali_to_class(old_class)}')"
                double_quote_old_class = single_quote_old_class.replace("'",'"')
                if found:
                    found = False
                    break
                for values in v:
                    if "\\u" in line:
                        line = self.aux.unscape_unicode(line)
                    if "<init>" in old_method.split("(")[0]:
                        old_method = old_method.replace("<init>","$init")
                    new_class = self.aux.scape_unicode(self.aux.smali_to_class(values[0]))
                    new_method = self.aux.scape_unicode(values[1].split("(")[0])
                    if single_quote_old_class in line or double_quote_old_class in line: 
                        single_quote_new_class = f"Java.use('{new_class}')"
                        custom_line = line.split("Java.use")[0] + single_quote_new_class +";" 
                    if ".implementation" in line:
                        if "." + old_method.split("(")[0]+".overload" in line or "." + old_method.split("(")[0]+".implementation" in line:
                            args = self.aux.get_smali_args(values[1])
                            custom_line = line.split(".")[0]+"."+new_method+f".overload({args}).implementation =" +line.split("=")[-1]  
                            found = True
                            break   
                        elif f'["{old_method.split("(")[0]}"].overload' in line or f'["{old_method.split("(")[0]}"].implementation' in line:
                            args = self.aux.get_smali_args(values[1])
                            custom_line = line.split('"')[0]+'"'+self.aux.scape_unicode(old_method.split("(")[0])+'"].overload('+args+').implementation ='+line.split("=")[-1]  
                            found = True
                            break      
            if not custom_line:
                text_out += line+"\n" 
            else:
                text_out += custom_line+"\n" 
                custom_line = ""
        file_out.write(text_out)
        Logger.log(f"Created updated Frida hooks in {new_hooks}.","success")

    def get_frida_config(self, file):
        hooks = self.aux.remove_comments(open(file, "r").read())
        hooks_lines = "\n".join([ll.strip() for ll in hooks.splitlines() if ll.strip()]).splitlines()
        filter = ["android.", "java.", "javax.", "okhttp3."]
        java_use = "Java.use("
        config = {}
        Logger.log(f"Finding Frida hooks to update from {file}.","info")
        for i in range(len(hooks_lines)):
            line = hooks_lines[i]
            if java_use in line:
                match = self.aux.between_quotes(line)
                if match:
                    class_hook = match.group(0).replace('"', "").replace("'","")
                    if "\\u" in class_hook:
                        class_hook = self.aux.unscape_unicode(class_hook)
                    if class_hook !="" and not any(substring in class_hook for substring in filter): 
                        next_line = hooks_lines[i+1] 
                        args = 0   
                        if ".overload" in next_line:
                            args = len(next_line.split(".overload")[1].rsplit(".implementation")[0].split(","))
                            method_hook = next_line.rsplit(".overload")[0].split(".")[-1]
                        else:
                            args = 0
                            method_hook = next_line.rsplit(".implementation")[0].split(".")[-1]
                        match = self.aux.between_quotes(method_hook)
                        if match and match.group(0)!="":
                            method_hook = self.aux.between_quotes(method_hook).group(0).replace('"',"")
                        method_hook +="(" + str(args) + ")"
                        if "\\u" in method_hook:
                            method_hook = self.aux.unscape_unicode(method_hook)
                        if "$init(" in method_hook:
                            method_hook = f"<init>({args})"
                        Logger.log(f"Found hook with class {class_hook} and method {method_hook}.","success")
                        smali_class_hook = self.aux.class_to_smali(class_hook)
                        if smali_class_hook in config:
                            config[smali_class_hook].append(method_hook) 
                        else:
                            config[smali_class_hook] = [method_hook]
        return config

    def unpack_apks(self, old_apk_path, new_apk_path):
        Logger.log("Unpacking the old apk file.","info")
        self.folder_rm_exists(self.work_directory)
        subprocess.call(['java', '-jar', 'apktool.jar','d', old_apk_path, '-o', self.old_apk_directory, '-f'], stdout=open(os.devnull, 'w'), 
        stderr=subprocess.STDOUT)
        Logger.log("Unpacking the new apk file.","info")
        subprocess.call(['java', '-jar', 'apktool.jar','d', new_apk_path, '-o', self.new_apk_directory, '-f'], stdout=open(os.devnull, 'w'), 
        stderr=subprocess.STDOUT)

    def get_smali_config(self, hooks, old_apk, new_apk):
        self.config = self.get_frida_config(hooks)
        self.unpack_apks(old_apk, new_apk)
        self.get_old_smali()
        self.get_new_smali()
        return self.config_w_file, self.new_smali_directory

    def get_old_smali(self):
        Logger.log("Finding the old smali file.","info")
        self.folder_rm_exists(self.old_smali_directory)
        os.mkdir(self.old_smali_directory)
        for config_class, values in self.config.items():
            try:
                output = subprocess.check_output(f'grep -rin \'.class .* {config_class}\' {self.old_apk_directory}/smali*', shell=True).decode("utf-8")
                smali_file = output.split(":")[0]
                shutil.copyfile(smali_file, os.path.join(self.old_smali_directory, os.path.basename(smali_file)))
                self.config_w_file[(config_class, os.path.join(self.old_smali_directory, os.path.basename(smali_file)))] = values
                Logger.log(f"Old class {config_class} has been found in {os.path.basename(smali_file)}.","success")
            except Exception as e:
                Logger.log(f"Old class {config_class} has not been found.","error")
    
    def get_new_smali(self):
        self.folder_rm_exists(self.new_smali_directory)
        os.mkdir(self.new_smali_directory)
        Logger.log("Copying all the smali files to the work folder.","info")
        for dir in os.listdir(self.new_apk_directory):  
            if "smali" in dir:
                path_dir = os.path.join(self.new_apk_directory,dir)
                shutil.copytree(path_dir, os.path.join(self.new_smali_directory, dir), dirs_exist_ok=True)

class Aux():

    def unscape_unicode(self, in_str):
        in_str = in_str.encode('unicode-escape')   
        in_str = in_str.replace(b'\\\\u', b'\\u') 
        in_str = in_str.decode('unicode-escape') 
        return in_str

    def scape_unicode(self, string):
        string = string.encode('unicode-escape').decode("utf-8")
        return string

    def remove_comments(self, string):
        pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)"
        regex = re.compile(pattern, re.MULTILINE|re.DOTALL)
        def _replacer(match):
            if match.group(2) is not None:
                return ""
            else: 
                return match.group(1) 
        return regex.sub(_replacer, string)

    def between_quotes(self, string):
        return re.search(r"\"([^\"\\]*(\\.[^\"\\]*)*)\"|\'([^\'\\]*(\\.[^\'\\]*)*)\'", string)

    def class_to_smali(self, class_hook):
        return "L"+class_hook.replace(".", "/")+";"

    def smali_to_class(self, string):
        return string[1:-1].replace("/",".") 

    def get_smali_args(self, string):
        if len(string.split(";"))>1:
            args = ""
            for arg in string.split("(")[1].split(")")[0].split(";"):
                arg = arg.replace("/",".").replace(";",",")
                if arg != "":
                    if arg[:2].isupper():
                        arg = arg[2:]
                    elif arg[:1].isupper:
                        arg = arg[1:]
                    args+='"'+arg+'"'+", "
            return args.strip(", ")
        else:
            return ""