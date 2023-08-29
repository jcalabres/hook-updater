HEADER = '\033[93m'
INFO = '\033[96m'
SUCCESS = '\033[92m'
SPECIAL = '\033[95m'
FAIL = '\033[91m'
BOLD = '\033[1m'
END = '\033[0m'

class Logger():

    def log(msg, type):
        if type == "info":
            print(BOLD + INFO + "[*] " + msg + END)
        elif type == "success":
            print(BOLD + SUCCESS + "[+] " + msg + END)
        elif type == "error":
             print(BOLD + FAIL + "[-] " + msg + END)
        elif type == "summary":
             print(BOLD + SPECIAL + "[~] " + msg + END)
        elif type == "header":
            print(BOLD + HEADER + msg + END)