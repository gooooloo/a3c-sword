tmux kill-session -t a3c

# workaround for that worker process are not killed ( wired.... )
ps xu | grep 'worker.py' | grep -v grep | awk '{ print $2 }' | xargs kill -9
