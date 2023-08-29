from logger import Logger
from parser import Parser
import os 

class Solver:

    def __init__(self):
        self.parser = Parser()
        self.weight_number_fields = 25
        self.weight_number_methods = 25
        self.weight_fields = 50
        self.weight_methods = 50
        self.weight_signature = 25

    def solve(self, config_w_file, new_smali_path):
        if config_w_file:
            Logger.log("Starting the solver...", "info")
            found = {}
            for key, signatures in config_w_file.items():
                (old_class, old_smali) = key 
                new_smali = self.find_smali(old_smali, new_smali_path)
                if new_smali == "":
                    Logger.log(f"New smali file not found for class {old_class}", "error")
                    break
                class_name = self.parser.get_class(new_smali)
                if  new_smali != "":   
                    Logger.log(f"New class {class_name} has been found in {os.path.basename(new_smali)}.", "success")
                    for signature in signatures:
                        old_method = self.parser.find_method_by_signature(signature.split('(')[0], old_smali)
                        new_method = self.find_method(old_method, new_smali, signature) 
                        if  new_method != "":   
                            Logger.log(f"Old method partial signature {signature} has been found as {new_method}.", "success")
                            self.print_summary(old_class, old_smali, class_name, signature, new_smali, new_method)
                            if old_class in found:
                                found[(old_class, signature)].append([class_name, new_method])
                            else:
                                found[(old_class, signature)] = [[class_name, new_method]]
                        else:
                            Logger.log(f"Old method partial signature {signature} has not been found.", "error")
                else:
                    Logger.log(f"New class has not been found.", "error")
        else:
            Logger.log(f"Old classes have been not found. Aborting...", "error")
        return found
        
    def find_method(self, old_method, new_smali, signature):
        new_methods = self.parser.get_methods(new_smali)
        new_signatures = self.parser.get_signatures(new_methods)
        found_signature, last_score = "", 0
        for new_signature in new_signatures:
            signature_name = signature.split("(")[0]
            args_signature = int(signature.split("(")[1].split(")")[0])
            if args_signature == 0 and signature_name+"(" in new_signature:
                found_signature = new_signature.split(' ')[-1]
                return found_signature
            elif args_signature>0 and args_signature==len(new_signature.split(";"))-1:
                if signature_name+"(" in new_signature:
                    found_signature = new_signature.split(' ')[-1]
                    return found_signature         
        if found_signature == "":
            for new_method in new_methods:
                score = self.eval_smali(old_method, new_method)
                if last_score == 0 or score >= last_score:
                    found_signature = self.parser.get_signatures([new_method])[0].split(" ")[-1]
                    last_score = score
        return found_signature

    def find_smali(self, old_smali, new_smali_path):
        smali_found, last_score = "", 0
        old_fields = self.parser.get_fields(old_smali)
        old_methods = self.parser.get_methods(old_smali)
        for dirpath, dirname, files in os.walk(new_smali_path): 
            for smali in files:
                new_methods = self.parser.get_methods(os.path.join(dirpath,smali))
                score = self.eval_fields(old_fields, self.parser.get_fields(os.path.join(dirpath,smali)))
                score += self.eval_methods(old_methods, new_methods)
                score += self.eval_signatures(self.parser.get_signatures(old_methods), self.parser.get_signatures(new_methods))
                if last_score == 0 or score >= last_score:
                    smali_found = os.path.join(dirpath,smali) 
                    last_score = score
        return smali_found
        
    def eval_fields(self, old_fields, new_fields):
        score, fields_found = 0, 0
        if len(old_fields)==len(new_fields):
            score+=self.weight_number_fields
        for field in old_fields: 
            if field in new_fields:
                fields_found+=1
        if len(new_fields) !=0:
            score += (fields_found*self.weight_fields)/(len(new_fields))
        return int(score)

    def eval_methods(self, old_methods, new_methods):
        score, methods_found = 0, 0
        if len(old_methods)==len(new_methods):
            score+=self.weight_number_methods
        for method in old_methods: 
            if method in new_methods:
                methods_found+=1
        if len(new_methods) !=0:
            score += (methods_found*self.weight_methods)/(len(new_methods))
        return int(score)

    def eval_signatures(self, old_signatures, new_signatures):
        score, signatures_found = 0, 0
        for signature in old_signatures: 
            if signature in new_signatures:
                signatures_found+=1
        if len(new_signatures) !=0:
            score += (signatures_found*self.weight_methods)/(len(new_signatures))
        return int(score)

    def eval_smali(self, old_method, new_method):
        score, lines_found = 0, 0
        lines = old_method.split("\n")
        for line in lines:
            if line in new_method.split("\n"):
                lines_found += 1    
        score = (lines_found*100)/(len(lines))
        return int(score)
    
    def print_summary(self, old_class, old_smali, class_name, signature, new_smali, new_method):
        Logger.log(f"Class: {old_class} --> {class_name}","summary")
        Logger.log(f"Method: {signature}* --> {new_method}","summary")
        Logger.log(f"File: {old_smali} --> {new_smali}","summary")