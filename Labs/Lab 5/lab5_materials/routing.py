import threading
import numpy as np
import copy
import time
import traceback
import sys

#function to import network graph from input file
def import_topology(path):
    # Load topology file into a 2-dimensional array
    try:
        narray = np.loadtxt(path)
    except:
        traceback.print_exc()

    return narray


#each thread simulates one router
class RouterThread(threading.Thread):
    def __init__(self, id, routers):
        threading.Thread.__init__(self)
        self.id = id #an id used to differentiate different routers
        self.neighbors = [] #a list to include ids of neighbor routers
        self.node_num = cost_matrix.shape[0] #the total number of routers in the network
        self.lock = threading.Lock() #the lock to be used for receiving distance vectors form neighbor(s)
        self.distance_vector_table = [] #the list used for keeping updated distance vector(s) received from neighbor(s)
        self.routers = routers #the dictionary in which the key is router's id, the value is the corresponding Router
        self.routers[id].thread = self

        self.poisoned_reverse = False #the flag to indicate whether to enable poisoned reverse

        #set neighbors
        for i, cost in enumerate(cost_matrix[self.id]):
            if (not np.isinf(cost)) and (i != self.id):
                self.neighbors.append(i)
        # copy neighbor link costs
        self.costs = copy.deepcopy(cost_matrix[self.id])

        #initialize the successor list, containing successor on current least-cost  
        #path from this router to each destination 
        self.successor = np.ones((self.node_num,))*np.inf
        self.successor[self.id] = self.id
        for w in self.neighbors:
            self.successor[w] = w


    def initialize_distance_vector(self):
        # initialize the distance vectors at this router
        self.dist_vec = {}

        self.dist_vec[self.id] = [np.inf] * self.node_num
        # TODO: set this router's initial distance vector values
        with global_mutex: #acquire lock on cost_matrix
            self.dist_vec[self.id] = copy.deepcopy(cost_matrix[self.id])
        
        #TODO: add initialize distance vectors of neighbors into self.dist_vec
        for w in self.neighbors:
            self.dist_vec[w] = [np.inf] * self.node_num
            with global_mutex: #acquire lock on cost_matrix
                self.dist_vec[w] = copy.deepcopy(cost_matrix[w])    



        #send distance vector to neighbors
        for w in self.neighbors:
            self.send_distvec(w, self.dist_vec[self.id])


    #function to send distance vector to a neighbor
    def send_distvec(self, neighbor_id, d):
        neighbor = self.routers[neighbor_id]
        with neighbor.thread.lock: #acquire lock to write into the distance vector table of the neighbor
            neighbor.thread.distance_vector_table.append((self.id,d))


    #function to update distance vector of this router
    def update_distvec(self):
        changed = False
        
        #TODO: update this router's distance vector; set the changed flag to True if any change in distance vector and update successor accordingly
        with self.lock: #acquire lock on distance vector table of this router
            for v in range(self.node_num):
                if v!=self.id:
                    min_cost = np.inf
                    next_hop = self.successor[v]
                    for w in self.neighbors:
                        if self.dist_vec[w][v]+self.costs[w] < min_cost:
                            min_cost = self.dist_vec[w][v]+self.costs[w]
                            next_hop = w
                    if min_cost!=self.dist_vec[self.id][v]:
                        changed = True
                        self.dist_vec[self.id][v] = min_cost
                        self.successor[v] = next_hop
        
        















        #if Dx(y) changed for any destination y, send distance vector Dx to all neighbors
        if changed:
            for w in self.neighbors:
                if self.poisoned_reverse:
                    d = copy.deepcopy(self.dist_vec[self.id])
                    for y,next_hop in enumerate(self.successor):
                        if next_hop==w and y!=next_hop:
                            d[y] = np.inf
                    self.send_distvec(w,d)
                else:
                    self.send_distvec(w, self.dist_vec[self.id])
                
                

    #functon to check if updated distance vector received from neighbor 
    def is_neighbor_distvect_received(self):
        changed = False
        with self.lock: #acquire lock on distance vector table of this router
            if len(self.distance_vector_table)==0:
                return False
            else:
                changed = True
            while len(self.distance_vector_table) > 0:
                item = self.distance_vector_table.pop()
                neighbor_id = item[0]
                neighbor_d = item[1]
                for v in range(len(self.dist_vec[neighbor_id])):
                    self.dist_vec[neighbor_id][v] = neighbor_d[v]
        return changed
        

    #functon to check if any neighbor link's cost has changed
    def is_neighbor_link_changed(self):
        changed=False
        with global_mutex: #acquire the lock on cost_matrix
            for v in self.neighbors:
                if self.costs[v]!=cost_matrix[self.id][v]:
                    changed=True
                    self.costs[v] = cost_matrix[self.id][v]
        return changed


    def run(self):
        self.initialize_distance_vector()
        while True:
            time.sleep(1)
            changed1 = self.is_neighbor_distvect_received() #check whether this router has received updated distance vector from neighbor
            changed2 = self.is_neighbor_link_changed() # check whether this router sees a link cost change to some neighbor
            changed = changed1 or changed2
            if changed:
                self.update_distvec()
                
  
    #auxiliary function to return distance vectors of this router and its neighbors
    def get_d(self):
        return self.dist_vec


    #auxiliary function to return successor list of this router to all destinations
    def get_s(self):
        return self.successor
        

class Router():
    def __init__(self):
        self.thread = None


if __name__=="__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 routing.py <topology_file_name>")
        sys.exit(1)

    topology_file = sys.argv[1]
    cost_matrix = import_topology(topology_file) #cost_matrix is a 2-dimensional array containing costs between nodes
    node_num = cost_matrix.shape[0] #node_num is the total number of routers in the network
    
    #global_mutex is a lock on cost_matrix
    global_mutex = threading.Lock()

    #routers is a dictionary which can map router's id to its corresponding thread 
    routers = {}
    for id in range(node_num):
        routers[id] = Router()

    #start one thread to simulate each router
    threads = []
    for i in range(node_num):
        _thread = RouterThread(i, routers)
        _thread.daemon = True #set the daemon attribute
        threads.append(_thread)    
    for thread in threads:
        thread.start()

    #The following commands are provided to check the status of each router, to change link costs, etc.
    while True:
        command = input("Command:")
        
        if(command=="GETD"):  # Get distance vectors maintained at each router
            for thread in threads:
                print("Router:",thread.id)
                distance_vectors = thread.get_d()
                for w in sorted(distance_vectors.keys()):
                    print(w, ": ", distance_vectors[w])
                        
        if(command=="GETS"):  # Get succssor list at each router
            for thread in threads:
                print("Router:",thread.id)
                #print(thread.get_s())
                successors = thread.get_s()
                for y in range(node_num):
                    print(y, ": ",int(successors[y]))
                
        if(command=="CHANGECOST"):  #Change the cost of a specific link
            command = input("start node:")
            src = int(command)
            command = input("end node:")
            dst = int(command)
            command = input("updated cost:")
            cost = int(command)
            with global_mutex:
                cost_matrix[src][dst] = cost
                cost_matrix[dst][src] = cost
                
        if(command=="POISONEDREVERSE"): #enable poisoned reverse
            for thread in threads:
                #with thread_mutex[thread.id]:
                thread.poisoned_reverse=True

        if(command=="EXIT"): #exit from the program 
            sys.exit()




