import argparse
from logger import Logger
from helper import Helper
from solver import Solver

LOGO = """
         ___  ___                   ___  ___  _   _____  __  __  
  /\  /\/___\/___\/\ /\     /\ /\  / _ \/   \/_\ /__   \/__\/__\ 
 / /_/ //  ///  // //_/____/ / \ \/ /_)/ /\ //_\\  / /\/_\ / \// 
/ __  / \_// \_// __ \_____\ \_/ / ___/ /_//  _  \/ / //__/ _  \ 
\/ /_/\___/\___/\/  \/      \___/\/  /___,'\_/ \_/\/  \__/\/ \_/                                                               
"""

def parse_args():
    parser = argparse.ArgumentParser(description='Hook updater!')
    parser.add_argument('-old', help='Outdated Old .apk file.', required=True),
    parser.add_argument('-new', help='New .apk file.', required=True),
    parser.add_argument('-hooks', help='Frida hooks.', required=True)
    parser.add_argument('-out', help='New Frida hooks path.', required=True)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    Logger.log(LOGO, "header")
    helper = Helper()
    config_w_file, smali_directory = helper.get_smali_config(args.hooks, args.old, args.new)
    
    solver = Solver()
    results = solver.solve(config_w_file, smali_directory)
    helper.gen_new_hooks(results, args.hooks, args.out)