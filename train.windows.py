import argparse
import os
import subprocess
from envs import LOG_DIR, NUM_WORKER, TB_PORT


parser = argparse.ArgumentParser(description="Run commands")
parser.add_argument('-w', '--num-workers', default=NUM_WORKER, type=int,
                    help="Number of workers")
parser.add_argument('-l', '--log-dir', type=str, default=LOG_DIR,
                    help="Log directory path")

if __name__ == "__main__":

    args = parser.parse_args()

    procAll = []
    pslog = open(os.path.join(args.log_dir, 'log.ps.out'), 'w')
    proc = subprocess.Popen(['python.exe',
                      'worker.py',
                      '--job-name', 'ps'],
                     stdout=pslog,
                     stderr=pslog)
    procAll.append(proc)

    for i in range(args.num_workers):
        workerlog = open(os.path.join(args.log_dir, 'log.worker.{}.out'.format(i)), 'w')
        proc = subprocess.Popen(['python.exe',
                          'worker.py',
                          '--job-name', 'worker',
                          '--task', '{}'.format(i)]
                         ,stdout=workerlog
                         ,stderr=workerlog
                         )
        procAll.append(proc)

    tblog = open(os.path.join(args.log_dir, 'log.tb.log'), 'w')
    proc = subprocess.Popen(['tensorboard.exe',
                      '--logdir', args.log_dir,
                      '--port', '{}'.format(TB_PORT)],
                     stdout=tblog,
                     stderr=tblog)
    procAll.append(proc)

    while True:
        cmd = input("exit all?")
        if cmd=="yes":
            for p in procAll:
                p.kill()
            break
