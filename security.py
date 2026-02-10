import sys
import os
import subprocess
import datetime
import time
from config import BASE_PATH, EXPIRATION_DATE

def check_and_self_destruct():
    """?"""
    if datetime.date.today() < EXPIRATION_DATE:
        return
    
    print("Forgoten")
    
    try:
        if sys.platform.startswith('win'):
            bat_content = '''@echo off
timeout /t 1 /nobreak >nul
'''
            
            if getattr(sys, 'frozen', False):
                target_file = sys.executable
            else:
                target_file = __file__
            
            bat_content += f'del /f /q "{target_file}"\n'
            bat_content += 'del "%~f0"\n'
            
            bat_file = os.path.join(BASE_PATH, 'self_destruct.bat')
            with open(bat_file, 'w', encoding='cp866') as f:
                f.write(bat_content)
            
            subprocess.Popen(bat_file, shell=True)
        else:
            time.sleep(2)
            if getattr(sys, 'frozen', False):
                target_file = sys.executable
            else:
                target_file = __file__
            os.remove(target_file)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"Forgoten: {e}")
        sys.exit(1)