import gym
import logging
from collections import deque
import numpy as np



import types
import gym

import numpy as np
from easydict import EasyDict as edict
from gymgame.engine import Vector2
from gymgame.tinyrpg.sword import config, Serializer, EnvironmentGym
from gymgame.tinyrpg.framework import Skill, Damage, SingleEmitter
from gym import spaces

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PS_IP = '127.0.0.1'
PS_PORT = 12222
TB_PORT = 12345
NUM_GLOBAL_STEPS = 90000000
SAVE_MODEL_SECS = 30
SAVE_SUMMARIES_SECS = 30
LOG_DIR = './log/'
NUM_WORKER = 4
VISUALISED_WORKERS = []  # e.g. [0] or [1,2]

_N_AVERAGE = 100

VSTR = 'V3.5.1'

ACT_LENGTH_IN_STATE = 40
OB_SPACE_SHAPE = [4 + ACT_LENGTH_IN_STATE]


GAME_NAME = config.GAME_NAME

config.BOKEH_MODE = "bokeh_serve"  # you need run `bokeh serve` firstly

config.MAP_SIZE = Vector2(10, 10)

config.GAME_PARAMS.fps = 24

config.GAME_PARAMS.max_steps = 300

config.NUM_PLAYERS = 1

config.NUM_NPC = 1

config.PLAYER_INIT_RADIUS = (0.0, 0.0)

config.NPC_INIT_RADIUS = 1 / config.MAP_SIZE * 7#(0.15, 0.2)

config.NPC_SKILL_COUNT = 1

config.SKILL_DICT = {
    'normal_attack' : Skill(
        id = 'normal_attack',
        cast_time = 0.0,#0.1,
        mp_cost = 0,
        target_required = True,
        target_relation = config.Relation.enemy,
        cast_distance = 1.0,
        target_factors = [Damage(200.0, config.Relation.enemy)]
    ),

    'normal_shoot' : Skill(
        id = 'normal_shoot',
        cast_time = 0.0, #0.3,
        mp_cost = 0,
        bullet_emitter = SingleEmitter(
            speed=0.3 * config.GAME_PARAMS.fps,
            penetration=1.0,
            max_range=config.MAP_SIZE.x * 0.8,
            radius=0.1,
            factors=[Damage(5.0, config.Relation.enemy)])
    ),

    'puncture_shoot' : Skill(
        id = 'normal_shoot',
        cast_time = 0.0,#0.3,
        mp_cost = 0,
        bullet_emitter = SingleEmitter(
            speed=0.3 * config.GAME_PARAMS.fps,
            penetration=np.Inf,
            max_range=config.MAP_SIZE.x * 0.8,
            radius=0.1,
            factors=[Damage(5.0, config.Relation.enemy)])
    ),
}

config.PLAYER_SKILL_LIST = [config.SKILL_DICT['puncture_shoot']]

config.NPC_SKILL_LIST = [config.SKILL_DICT['normal_attack']]

config.BASE_PLAYER = edict(
    id = "player-{0}",
    position = Vector2(0, 0),
    direct = Vector2(0, 0),
    speed = 0.3 * config.GAME_PARAMS.fps,
    radius = 0.5,
    max_hp = 100.0,
    camp = config.Camp[0],
    skills=config.PLAYER_SKILL_LIST
)

config.BASE_NPC = edict(
    id = "npc-{0}",
    position = Vector2(0, 0),
    direct = Vector2(0, 0),
    speed = 0.1 * config.GAME_PARAMS.fps,
    radius = 0.5,
    max_hp = 800.0,
    camp = config.Camp[1],
    skills=config.NPC_SKILL_LIST
)


def myextension(cls):

    def decorate_extension(ext_cls):
        dict = ext_cls.__dict__
        for k, v in dict.items():
            if type(v) is not types.MethodType and \
                            type(v) is not types.FunctionType and \
                            type(v) is not property:
                continue
            if hasattr(cls, k):
                setattr(cls, k+'_orig', getattr(cls, k))
            setattr(cls, k, v)
        return ext_cls

    return decorate_extension


@myextension(Serializer)
class SerializerExtension():

    DIRECTS = [Vector2.up,
               Vector2.up + Vector2.right,
               Vector2.right,
               Vector2.right + Vector2.down,
               Vector2.down,
               Vector2.down + Vector2.left,
               Vector2.left,
               Vector2.left + Vector2.up,
               ]

    def _deserialize_action(self, data):
        index, target = data
        if index < 8:
            direct = SerializerExtension.DIRECTS[index]
            actions = [('player-0', config.Action.move_toward, direct, None)]

        else:
            skill_index = index - 8
            skill_id = config.BASE_PLAYER.skills[skill_index].id
            actions = [('player-0', config.Action.cast_skill, skill_id, target, None)]

        return actions

    def _serialize_map(self, k, map):
        s_players = k.do_object(map.players, self._serialize_player)
        s_npcs = k.do_object(map.npcs, self._serialize_npc)
        s_bullets = []

        return np.hstack([s_players, s_npcs, s_bullets])

    def _serialize_character(self, k, char):

        # def norm_position_relative(v, norm):
        #     map = norm.game.map
        #     player = map.players[0]
        #     return (v - player.attribute.position) / map.bounds.max

        def norm_position_abs(v, norm):
            map = norm.game.map
            return v / map.bounds.max

        attr = char.attribute
        k.do(attr.position, None, norm_position_abs)
        k.do(attr.hp, None, k.n_div_tag, config.Attr.hp)


@myextension(EnvironmentGym)
class EnvExtension():
    def _init_action_space(self): return spaces.Discrete(9)

    def _my_state(self):
        p = self._my_poses()
        ret = [p[0], p[1], p[2], p[3]]
        ret.extend(self._ep_actions)
        return ret

    def _my_poses(self):
        map = self.game.map
        max_x, max_y = config.MAP_SIZE[0], config.MAP_SIZE[1]
        player, npcs = map.players[0], map.npcs
        pp0 = player.attribute.position[0]/max_x
        pp1 = player.attribute.position[1]/max_y

        if len(npcs) == 0:
            delta = 0, 0
        else:
            delta = npcs[0].attribute.position - player.attribute.position  # [2]
            delta[0] = delta[0] / max_x
            delta[1] = delta[1] / max_x

        return pp0, pp1, delta[0], delta[1]

    def _my_get_hps(self):
        map = self.game.map
        player, npcs = map.players[0], map.npcs
        return player.attribute.hp / player.attribute.max_hp, sum([o.attribute.hp / o.attribute.max_hp for o in npcs])

    def _my_did_I_move(self):
        pos1 = self.last_pos
        pos2 = self._my_poses()[:2]
        d = abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1])
        return d[0] > 1e-5 or d[1] > 1e-5

    def reset(self):
        self._ep_count += 1
        self._ep_steps = 0
        self._ep_rewards = []
        self._ep_actions = deque(maxlen=ACT_LENGTH_IN_STATE)
        for _ in range(ACT_LENGTH_IN_STATE): self._ep_actions.append(0)
        self.reset_orig()

        return self._my_state()

    def step(self, act):
        self.last_hps = self._my_get_hps()
        self.last_act = act
        self.last_pos = self._my_poses()[:2]

        _, r, t, _ = self.step_orig((act, self.game.map.npcs[0]))

        self._ep_steps += 1
        self._ep_rewards.append(r)
        self._ep_actions.append(1 if act == 8 else 0)

        i = {}
        if t:
            self._steps_last_n_eps.append(self._ep_steps)
            self._rewards_last_n_eps.append(np.sum(self._ep_rewards))

            i['{}/ep_count'.format(VSTR)] = self._ep_count
            i['{}/ep_steps'.format(VSTR)] = self._steps_last_n_eps[-1]
            i['{}/ep_rewards'.format(VSTR)] = self._rewards_last_n_eps[-1]
            i['{}/aver_steps_{}'.format(VSTR, _N_AVERAGE)] = np.average(self._steps_last_n_eps)
            i['{}/aver_rewards_{}'.format(VSTR, _N_AVERAGE)] = np.average(self._rewards_last_n_eps)

            print(i)


        return self._my_state(), r, t, i

    def _reward(self):
        hps = self._my_get_hps()
        delta_hps = hps[0] - self.last_hps[0], hps[1] - self.last_hps[1]

        r_attack = -delta_hps[1]  # -1 -> 1
        r_defense = delta_hps[0]  # -1 -> -1
        r_edge = -1 if self.last_act < 8 and not self._my_did_I_move() else 0

        return r_attack + r_defense + r_edge


def create_env(unused):
    env = gym.make(GAME_NAME).unwrapped
    env._ep_count = 0
    env._steps_last_n_eps = deque(maxlen=_N_AVERAGE)
    env._rewards_last_n_eps = deque(maxlen=_N_AVERAGE)
    env.observation_space = gym.spaces.Box(np.inf, np.inf, OB_SPACE_SHAPE)
    return env


