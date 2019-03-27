from daemon import Daemon
from subprocess import call

class WNGDeamon(Deamon):
    def run(self):
        call(["python ./webNameGen.py -load data/villesfr-10-0"],shell=true)

if __name__ == "__main__":
    deamon=WNGDeamon("/tmp/WNG.pid")

    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)