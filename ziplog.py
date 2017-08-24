import os
import argparse
from envs import VSTR, LOG_DIR, NUM_WORKER


parser = argparse.ArgumentParser(description="Run commands")
parser.add_argument('-w', '--num-workers', default=NUM_WORKER, type=int,
                    help="Number of workers")

def main():
    args = parser.parse_args()

    os.chdir(LOG_DIR)
    with open(os.path.join('train', 'checkpoint'), 'r') as f:
        l = f.readline()
    ckpt = l.split('"')[1]
    step = ckpt.split('-')[1]
    step_in_k = int(int(step)/ 1000)

    cmd = 'tar -cf {}.log.{}k.tar'.format(VSTR, step_in_k)
    cmd += ' train/{}.*'.format(ckpt)
    cmd += ' train/checkpoint'
    cmd += ' train/graph.pbtxt'
    for i in range(args.num_workers):
        cmd += ' train_{}'.format(i)

    os.system(cmd)


if __name__ == '__main__':
    main()
