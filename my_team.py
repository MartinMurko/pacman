import random
import contest.util as util
from contest.capture_agents import CaptureAgent
from contest.game import Directions, Actions
from contest.util import nearest_point

def create_team(first_index, second_index, is_red, first='OffensiveReflexAgent', second='DefensiveReflexAgent', num_training=0):
    return [eval(first)(first_index), eval(second)(second_index)]

class ReflexCaptureAgent(CaptureAgent):

    def register_initial_state(self,game_state):
        CaptureAgent.register_initial_state(self, game_state)
        self.start = game_state.get_agent_position(self.index)
        self.walls = game_state.get_walls()
        mid=self.walls.width//2
        if self.red:
            hx=mid-1
            ex=mid
        else:
            hx=mid
            ex=mid-1
        self.enemy_side=[]
        for i in range (self.walls.width):
            for j in range (self.walls.height):
                if(not self.walls[i][j] and not self.is_home((i,j))):
                    self.enemy_side.append((i,j))
        self.home_border=[]
        for i in range (self.walls.height):
            if(not self.walls[hx][i] and not self.walls[ex][i]):
                self.home_border.append((hx,i))

    def choose_action(self,game_state):
        legal = game_state.get_legal_actions(self.index)
        try:
            action=self.decide(game_state)
        except Exception:
            action=None
        if(action not in legal):
            action=random.choice(legal)
        return action

    def decide(self,game_state):
        raise NotImplementedError

    def my_pos(self,game_state):
        return game_state.get_agent_position(self.index)

    def dist(self,a,b):
        return self.get_maze_distance(a,b)

    def closest(self,pos,targets):
        best=None
        bestd=None
        for t in targets:
            d=self.dist(pos,t)
            if(bestd is None or d<bestd):
                best=t
                bestd=d
        return best

    def hdist(self,pos):
        return self.dist(pos,self.closest(pos,self.home_border))

    def visible_enemies(self,game_state):
        ene=[]
        for i in self.get_opponents(game_state):
            st=game_state.get_agent_state(i)
            if(st.get_position() is not None):
                ene.append((i,st))
        return ene

    def is_home(self,pos):
        mid=self.walls.width//2
        if(self.red):
            return pos[0]<mid
        else:
            return pos[0]>=mid

    def next_pos(self,pos,action):
        dx,dy=Actions.direction_to_vector(action)
        return (int(pos[0]+dx),int(pos[1]+dy))

    def move(self,game_state,target,avoid=()):
        pos=self.my_pos(game_state)
        baction=None
        bdist=None
        for action in game_state.get_legal_actions(self.index):
            npos=self.next_pos(pos,action)
            if(npos in avoid):
                continue
            d=self.dist(npos,target)
            if(bdist is None or d<bdist):
                baction=action
                bdist=d
        return baction

    def flee(self,game_state,threats):
        pos=self.my_pos(game_state)
        baction=None
        bdist=None
        for action in game_state.get_legal_actions(self.index):
            npos=self.next_pos(pos,action)
            d=10000
            for t in threats:
                d=min(d,self.dist(npos,t))
            if(bdist is None or d>bdist):
                baction=action
                bdist=d
        return baction


class OffensiveReflexAgent(ReflexCaptureAgent):
    MAXFOOD=5
    MGHOSTDIST=5

    def decide(self,game_state):
        bot=game_state.get_agent_state(self.index)
        pos=bot.get_position()
        food=self.get_food(game_state).as_list()
        capsules=self.get_capsules(game_state)
        ghosts=[]
        for index,st in self.visible_enemies(game_state):
            if not st.is_pacman and st.scared_timer<=2:
                ghosts.append(st.get_position())
        ghostd=10000
        for g in ghosts:
            ghostd=min(ghostd,self.dist(pos,g))
        danger=set()
        for g in ghosts:
            danger.add(g)
            for n in Actions.get_legal_neighbors(g,self.walls):
                danger.add(n)
        if(bot.num_carrying>0):
            if(len(food)<=2 or bot.num_carrying>=self.MAXFOOD or ghostd<=self.MGHOSTDIST or game_state.data.timeleft//4<=self.hdist(pos)+5):
                target=self.closest(pos,self.home_border)
                if(ghostd<=self.MGHOSTDIST and len(capsules)>0):
                    cap=self.closest(pos,capsules)
                    if(self.dist(pos,cap)<self.dist(pos,target)):
                        target=cap
                action=self.move(game_state,target,avoid=danger)
                if(action is None):
                    action=self.flee(game_state,ghosts)
                return action
        if(ghostd<=self.MGHOSTDIST and len(capsules)>0):
            cap=self.closest(pos,capsules)
            action=self.move(game_state,cap,avoid=danger)
            if(action is not None):
                return action
        if(len(food)>0):
            target=self.closest(pos,food)
            action=self.move(game_state,target,avoid=danger)
            if(action is None):
                action=self.flee(game_state,ghosts)
            return action
        return self.move(game_state,self.closest(pos,self.home_border),avoid=danger)


class DefensiveReflexAgent(ReflexCaptureAgent):

    def register_initial_state(self,game_state):
        super().register_initial_state(game_state)
        self.last_food=set(self.get_food_you_are_defending(game_state).as_list())
        self.last_eaten = None
        food = list(self.last_food)
        bsquare = None
        btotal = None
        for b in self.home_border:
            total=0
            for f in food:
                total += self.dist(b,f)
            if btotal is None or total < btotal:
                bsquare=b
                btotal=total
        self.guard=bsquare

    def decide(self,game_state):
        bot=game_state.get_agent_state(self.index)
        pos=bot.get_position()
        stay_home=set(self.enemy_side)
        food=set(self.get_food_you_are_defending(game_state).as_list())
        for f in self.last_food:
            if(f not in food):
                self.last_eaten=f
        self.last_food=food
        if(self.last_eaten is not None and pos==self.last_eaten):
            self.last_eaten=None
        invaders=[]
        for index,st in self.visible_enemies(game_state):
            if(st.is_pacman):
                invaders.append(st.get_position())
        if(len(invaders)>0):
            target=self.closest(pos,invaders)
            self.last_eaten=None
            if(bot.scared_timer>0):
                if(self.dist(pos,target)<=2):
                    return self.flee(game_state,[target])
            action=self.move(game_state,target,avoid=stay_home)
            if(action is not None):
                return action
        if(self.last_eaten is not None):
            action=self.move(game_state,self.last_eaten,avoid=stay_home)
            if(action is not None):
                return action
        return self.move(game_state,self.guard,avoid=stay_home)
