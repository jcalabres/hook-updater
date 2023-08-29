class Parser():
     
    def get_class(self, file):
        return open(file, "r").readline().split(" ")[-1][0:-1]

    def get_fields(self, file):
        lines = open(file, "r").readlines()
        fields = []
        for line in lines:
            if ".field" in line:
                fields.append(line)
            if ".method" in line:
                break
        return fields

    def get_methods(self, file):
        lines = open(file, "r").readlines()
        methods = []
        method_txt = ""
        add = False
        for line in lines:
            if ".method" in line:
                add = True 
            elif add and ".end method" in line:
                add = False
                methods.append(method_txt)
                method_txt = ""
            if add:
                method_txt += line
        return methods

    def get_signatures(self, methods):
        signatures = []
        for method in methods:
            signature = method.splitlines()[0]
            signatures.append(signature)
        return signatures

    def find_method_by_signature(self, method, file):
        lines = open(file, "r").readlines()
        add = False
        method_txt = ""
        for line in lines:
            if method in line:   
                add = True
            elif add and ".end method" in line:
                add = False
                method_txt += line       
            if add and line != '\n':
                method_txt += line
        return method_txt