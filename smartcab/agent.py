import random
from pdb import set_trace
from collections import defaultdict

from environment import Agent, Environment
from planner import RoutePlanner
from simulator import Simulator

class LearningAgent(Agent):
    """An agent that learns to drive in the smartcab world."""

    def __init__(self, env):
        super(LearningAgent, self).__init__(env)  # sets self.env = env, state = None, next_waypoint = None, and a default color
        self.color = 'red'  # override color
        self.planner = RoutePlanner(self.env, self)  # simple route planner to get next_waypoint


        # Initialize Q value for unseen (state,action) pairs
        self.Q_naught = 0.0
        
        self.Q = defaultdict(lambda: self.Q_naught) # the Q-table, unseen (state,action) pairs default to Q_naught=0

        self.gamma = 0.33 # our discount factor of Q(s',a')
        self.alpha = 0.5 # our learning rate
        self.epsilon = 0.9  # How likely are we to pick random action / explore new paths?

        self.T = 0 # number of trials performed
        self.goal_reached = 0 # number of times agent reach goal before deadline
        self.total_reward = 0 # sum total of reward over all trials

    def reset(self, destination=None):
        self.planner.route_to(destination)
        # New trip; reset the previous state,action, and reward
        self.S_previous = None
        self.A_previous = None
        self.R_previous = None
        self.T += 1 # update number of trials performed

    def update(self, t):
        """
        Update state, pick an action, get a reward, update Q-table, repeat
        """
        # Gather inputs
        self.next_waypoint = self.planner.next_waypoint()  # from route planner, also displayed by simulator
        deadline = self.env.get_deadline(self)

        # Current state
        self.state = (('light', self.env.sense(self)['light']),('waypoint',self.next_waypoint))


        # act randomly
        # action = random.choice(Environment.valid_actions)

        # Pick an action based on Q-table
        Q_sa, action = self.getAction(self.state)

        # Execute action and get reward
        reward = self.env.act(self, action)
        
        # Calculate how successful the agent is at learning the optimal model
        if self.env.agent_states[self]['location'] == self.env.agent_states[self]['destination']:
            print "Goal Reached %d out of %d times:"%(self.goal_reached,self.T)
            self.goal_reached += 1
        self.total_reward += reward


        # Update the Q-table
        if self.S_previous != None: # Don't update Q-table on the inital move,
            if (self.S_previous, self.A_previous) not in self.Q:
                self.Q[(self.S_previous, self.A_previous)] = self.Q_naught # For previously unseen state,action pairs

            Q_sa = self.Q[(self.S_previous,self.A_previous)]
            Q_max = self.getAction(self.state)[0] # max Q(s',a') over a'
            
            # Q(s,a) <- Q(s,a) + alpha[r' + gamma*max{a'} Q(s',a') - Q(s,a)]
            # From: Pg. 332 "Foundations of Machine Learning" Mohri, Rostamizadeh, and Talwalker 2012
            self.Q[(self.S_previous,self.A_previous)] = Q_sa + self.alpha*(self.R_previous + self.gamma*Q_max - Q_sa)


        self.S_previous = self.state
        self.A_previous = action
        self.R_previous = reward

        self.env.status_text +=  "\nGoal Reached {} out of {} times\nTotal Reward: {}".format(self.goal_reached,self.T,self.total_reward,deadline)
        #print "LearningAgent.update(): deadline = {}, Total Reward = {}, action = {}, reward = {}".format(deadline, self.total_reward, action, reward)  # [debug]


    def getAction(self, state):
        """
        Find best action for a given state based on lookup of value in Q-table
        using the epsilon greedy method
        """
        best_action = random.choice(Environment.valid_actions)
        # Pick random direction with P==(1-epsilon) to make sure we explore all state,action pairs (in theory infinitely many times)
        if random.random() > self.epsilon:
            Q_max = self.Q[state, best_action]
        # Otherwise pick the action based on a Q-value lookup
        else:
            Q_max = 0
            for action in Environment.valid_actions:
                # search through all possible actions given this state
                q_value = self.Q[state, action]
                if q_value > Q_max:
                    Q_max = q_value
                    best_action = action
            # In the case where we haven't been to this state before, just use a random action
        return (Q_max, best_action)

def run():
    """Run the agent for a finite number of trials."""
    # Set up environment and agent
    e = Environment()  # create environment (also adds some dummy traffic)
    a = e.create_agent(LearningAgent)  # create agent
    e.set_primary_agent(a, enforce_deadline=True)  # set agent to track

    # Now simulate it
    sim = Simulator(e, update_delay=0)  # reduce update_delay to speed up simulation
    sim.run(n_trials=100)  # press Esc or close pygame window to quit


if __name__ == '__main__':
    run()