# A3C

My daily used A3C implementaion. Based on openai's A3C implementation(https://github.com/openai/universe-starter-agent.git).
I make some tiny changes to fit my working preferences.


## environment
To run this algo, I use tmux. I use python3.


## coding
- Typically I don't change `a3c.py` and `worker.py`. 
- If I want to change the model, I change `model.py`. 
- If I want to handle the env stuff, I change `envs.py`. 
- If I want to handle the hyper-parameters, I also change `envs.py`. 
- I hard-code almost every argument in `envs.py`, so that I can easily start the program in CLI without too much typing.


## running
To start training with default num-workers(=4), just run below in CLI:
```
./do.a3c.sh
```

To start training with 32 workers:
```
./do.a3c.sh -w 32
```

To stop training:
```
./no.a3c.sh
```


## log archiving
```
python ./ziplog.py

```


## Versioning when tuning
I use `VSTR` in `envs.py` to identify my hyper-parameter and algo version info. I use `git` so I can easily check out
detail of every version. I use `ziplog.py` to archive tuning result.
