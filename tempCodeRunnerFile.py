bp = os.getcwd()
os.chdir('..')
os.chdir('ResDatabase')
ResDataDir = os.getcwd()
os.chdir('..')
os.chdir('Magnicon-Offline-Analyzer')
sys.path.append(ResDataDir)
from ResDataBase import ResData