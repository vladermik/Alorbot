import os
import platform

def set_permissions(path):
    if platform.system() == 'Windows':
        os.system(f'icacls "{path}" /grant Everyone:F /T /C /Q')
    else:
        os.chmod(path, 0o777)
        os.system(f'chmod -R 777 {path}')