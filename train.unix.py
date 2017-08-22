import argparse
import os
import sys
from six.moves import shlex_quote
from envs import LOG_DIR, NUM_WORKER, PS_PORT, TB_PORT


parser = argparse.ArgumentParser(description="Run commands")
parser.add_argument('-w', '--num-workers', default=NUM_WORKER, type=int,
                    help="Number of workers")


def new_cmd(session, name, cmd):
    if isinstance(cmd, (list, tuple)):
        cmd = " ".join(shlex_quote(str(v)) for v in cmd)
    return name, "tmux send-keys -t {}:{} {} Enter".format(session, name, shlex_quote(cmd))


def create_commands(session, num_workers, log_dir, shell='bash'):
    # for launching the TF workers and for launching tensorboard
    base_cmd = [
        'CUDA_VISIBLE_DEVICES=',
        sys.executable, 'worker.py'
    ]

    cmds_map = [new_cmd(session, "ps", base_cmd + ["--job-name", "ps", "--num-workers", str(num_workers)])]
    for i in range(num_workers):
        cmds_map += [new_cmd(session, "w-%d" % i, base_cmd + ["--job-name", "worker", "--task", str(i), "--num-workers", str(num_workers)])]

    cmds_map += [new_cmd(session, "tb", ["tensorboard", "--logdir", log_dir, "--port", "{}".format(TB_PORT)])]
    cmds_map += [new_cmd(session, "htop", ["htop"])]

    windows = [v[0] for v in cmds_map]

    notes = []
    cmds = [
        "mkdir -p {}".format(log_dir),
        "echo {} {} > {}/cmd.sh".format(sys.executable, ' '.join([shlex_quote(arg) for arg in sys.argv if arg != '-n']), log_dir),
    ]
    notes += ["Use `tmux attach -t {}` to watch process output".format(session)]
    notes += ["Use `tmux kill-session -t {}` to kill the job".format(session)]
    notes += ["Point your browser to http://localhost:{} to see Tensorboard".format(TB_PORT)]

    cmds += [
    "kill $( lsof -i:{} -t ) > /dev/null 2>&1".format(TB_PORT),  # kill any process using tensorboard's port
    "kill $( lsof -i:{}-{} -t ) > /dev/null 2>&1".format(PS_PORT, num_workers+PS_PORT), # kill any processes using ps / worker ports
    "tmux kill-session -t {}".format(session),
    "tmux new-session -s {} -n {} -d {}".format(session, windows[0], shell)
    ]
    for w in windows[1:]:
        cmds += ["tmux new-window -t {} -n {} {}".format(session, w, shell)]
    cmds += ["sleep 1"]
    for window, cmd in cmds_map:
        cmds += [cmd]

    return cmds, notes


def run():
    args = parser.parse_args()
    cmds, notes = create_commands("a3c", args.num_workers, LOG_DIR)
    print("Executing the following commands:")
    print("\n".join(cmds))
    print("")
    os.environ["TMUX"] = ""
    os.system("\n".join(cmds))
    print('\n'.join(notes))


if __name__ == "__main__":
    run()
