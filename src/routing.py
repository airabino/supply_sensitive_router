import time
import numpy as np

from copy import deepcopy
from scipy.stats import norm
from scipy.special import factorial

from .progress_bar import ProgressBar
from .dijkstra import dijkstra, multi_directional_dijkstra
from .bellman import bellman
from .queuing import queuing_time_distribution

def in_range(x, lower, upper):

    return (x >= lower) & (x <= upper)

def super_quantile(x, p = (0, 1), n = 100):
    
    p_k = np.linspace(p[0], p[1], n)

    q_k = np.quantile(x, p_k)

    return np.nan_to_num(q_k.mean(), nan = np.inf)

def shortest_paths(graph, origins, method = 'dijkstra', **kwargs):
    '''
    Return path costs, path values, and paths using Dijkstra's or Bellman's method

    Produces paths to each destination from closest origin

    Depends on an Objective object which contains the following four functions:

    values = initial() - Function which produces the starting values of each problem state
    to be applied to the origin node(s)

    values = infinity() - Function which produces the starting values for each non-origin
    node. The values should be intialized such that they are at least higher than any
    conceivable value which could be attained during routing.

    values, feasible = update(values, edge, node) - Function which takes current path state
    values and updates them based on the edge traversed and the target node and whether the
    proposed edge traversal is feasible. This function returns the values argument and a
    boolean feasible.

    values, savings = compare(values, approximation) - Function for comparing path state
    values with the existing best approximation at the target node. This function returns
    the values argument and a boolean savings.
    '''

    if method == 'dijkstra':

        costs, values, paths = dijkstra(graph, origins, **kwargs)

    elif method == 'bellman':

        costs, values, paths = bellman(graph, origins, **kwargs)

    destinations = kwargs.get('destinations', [])
    
    if destinations:

        costs_d = {}
        values_d = {}
        paths_d = {}

        for destination in destinations:

            costs_d[destination] = costs[destination]
            values_d[destination] = values[destination]
            paths_d[destination] = paths[destination]

        return costs_d, values_d, paths_d

    else:

        return costs, values, paths

def all_pairs_shortest_paths(graph, origins, method = 'dijkstra', **kwargs):
    '''
    Return path costs, path values, and paths using Dijkstra's or Bellman's method

    Produces paths to each origin from each origin

    Depends on an Objective object which contains the following four functions:

    values = initial() - Function which produces the starting values of each problem state
    to be applied to the origin node(s)

    values = infinity() - Function which produces the starting values for each non-origin
    node. The values should be intialized such that they are at least higher than any
    conceivable value which could be attained during routing.

    values, feasible = update(values, edge, node) - Function which takes current path state
    values and updates them based on the edge traversed and the target node and whether the
    proposed edge traversal is feasible. This function returns the values argument and a
    boolean feasible.

    values, savings = compare(values, approximation) - Function for comparing path state
    values with the existing best approximation at the target node. This function returns
    the values argument and a boolean savings.
    '''

    # print(origins)
    # print(kwargs.get('progress_bar_kw', {}))

    # print(graph.nodes)

    if method == 'multi_dijkstra':

        return multi_directional_dijkstra(graph, origins, **kwargs)

    else:

        if method == 'dijkstra':

            routing_function = dijkstra

        elif method == 'bellman':

            routing_function = bellman

        costs = {}
        values = {}
        paths = {}

        for origin in ProgressBar(origins, **kwargs.get('progress_bar_kw', {})):

            result = shortest_paths(
                graph, [origin],
                destinations = origins,
                method = method, 
                **kwargs
                )

            costs[origin] = result[0]
            values[origin] = result[1]
            paths[origin] = result[2]

        return costs, values, paths

def impedance(values, origins = {}, destinations = {}, **kwargs):

    field = kwargs.get('field', 'time')
    expectation = kwargs.get('expectation', np.mean)
    constant = kwargs.get('constant', 1)


    if not origins:

        origins = {k: 1 for k in values.keys()}

    if not destinations:

        destinations = {k: 1 for k in values.keys()}

    sum_cost = 0

    n = 0

    for origin, mass_o in origins.items():

        for destination, mass_d in destinations.items():

            if origin != destination:

                sum_cost += (
                    constant * mass_o * mass_d *
                    expectation(np.atleast_1d(values[origin][destination][field]))
                    )

            n += 1

            # print(sum_cost)

    return sum_cost / n

def current(values, origins = {}, destinations = {}, **kwargs):

    field = kwargs.get('field', 'time')
    expectation = kwargs.get('expectation', np.mean)
    constant = kwargs.get('constant', 1)


    if not origins:

        origins = {k: 1 for k in values.keys()}

    if not destinations:

        destinations = {k: 1 for k in values.keys()}

    sum_cost = 0

    n = 0

    total_weight = sum([v for v in origins.values()])

    for origin, weight_o in origins.items():

        for destination, weight_d in destinations.items():

            if origin != destination:

                # print(constant * (voltage_d - voltage_o) )

                sum_cost += (
                    constant * weight_o * weight_d /
                    expectation(
                        np.atleast_1d(values[destination][origin][field]) * total_weight
                        )
                    )

            n += 1

    return sum_cost / n

class Objective():

    def __init__(self, field = 'weight', limit = np.inf):

        self.field = field
        self.limit = limit

    def initial(self):

        return 0

    def infinity(self):

        return np.inf

    def update(self, values, link, node):

        values += link.get(self.field, 1)

        return values, values <= self.limit

    def compare(self, values, approximation):

        return values, values < approximation

class Scout():

    def __init__(self, **kwargs):

        self.field = kwargs.get('field', 'time')
        self.limit = kwargs.get('limit', np.inf)
        self.edge_limit = kwargs.get('edge_limit', np.inf)
        self.exclude = kwargs.get('exclude', ['city_city'])
        self.disambiguation = kwargs.get('disambiguation', 0)

    def initial(self):

        return 0

    def infinity(self):

        return np.inf

    def update(self, values, edge, node):

        if (edge['type'] in self.exclude) or (edge[self.field] > self.edge_limit):

            return values, False

        values += edge.get(self.field, 1)

        return values, values <= self.limit

    def combine(self, values_0, values_1):

        return values_0 + values_1

    def compare(self, values, approximation):

        if approximation == np.inf:

            return values, values < approximation

        return values, values * (1 + self.disambiguation) < approximation

def edge_types(graph):

    _adj = graph._adj
    _node = graph._node

    for source, adj in _adj.items():
        for target, edge in adj.items():

            edge['type'] = (
                f"to_{_node[target].get('type', 'none')}"
                )

    return graph

def supply_costs(graph, vehicle, station_kw):

    graph = edge_types(graph)

    for source, node in graph._node.items():

        if node['type'] in station_kw:

            kw = station_kw[node['type']]

            if 'queue' in kw:

                kw['queue']['n'] = node.get('n_dcfc', 1)

                node['station'] = SimulatedStation(**kw)

            else:

                node['station'] = Station(**kw)

    for source, adj in graph._adj.items():
        for target, edge in adj.items():

            station = graph._node[source]['station']

            if station is not None:

                edge = station.update(vehicle, edge)

    return graph

def origins_destinations(graph, origins, destinations):

    for source, adj in graph._adj.items():
        for target, edge in adj.items():

            # Edges from a non-origin destination are disallowed
            if (source in destinations) and (source not in origins):

                edge['feasible'] = False

            # Edges to and origin are disallowed
            if target in origins:

                edge['feasible'] = False

    return graph

class Vehicle():

    def __init__(self, **kwargs):

        self.cases = kwargs.get('cases', 1) # [-]

        self.capacity = kwargs.get('capacity', 80 * 3.6e6) # [J]
        self.consumption = kwargs.get('consumption', 550) # [J/m]
        self.charge_rate = kwargs.get('charge_rate', 80e3) # [W]

        self.soc_bounds = kwargs.get('soc_bounds', (0, 1)) # ([-], [-])
        self.max_charge_start_soc = kwargs.get('max_charge_start_soc', 1) # [-]

        self.risk_attitude = kwargs.get('risk_attitude', (0, 1)) # ([-], [-])

        self.out_of_charge_penalty = kwargs.get('out_of_charge_penalty', 4 * 3600) # [s]

        self.cost = kwargs.get('cost', 'total_time')

        if self.cases == 1:

            self.expectation = kwargs.get(
                'expectation',
                lambda x: x[0],
                )

        else:

            self.expectation = kwargs.get(
                'expectation',
                lambda x: super_quantile(x, self.risk_attitude),
                )
            
        self.initial_values = kwargs.get(
            'initial_values',
            {
                'total_time': np.zeros(self.cases), # [s]
                'driving_time': np.zeros(self.cases), # [s]
                'distance': np.zeros(self.cases), # [m]
                'price': np.zeros(self.cases), # [$]
            },
        )

        self.usable_capacity = (
            (self.soc_bounds[1] - self.soc_bounds[0]) * self.capacity
            )

        self.range = self.usable_capacity / self.consumption

        self.min_edge_distance = (1 - self.max_charge_start_soc) * self.range


    def select_case(self, case):

        new_object = deepcopy(self)
        new_object.expectation = lambda x: x[case]

        return new_object

    def initial(self):

        return self.initial_values

    def infinity(self):

        return {k: np.ones(self.cases) * np.inf for k in self.initial_values.keys()}

    def update(self, values, edge):

        updated_values = {}

        updated_values['total_time'] = values['total_time'] + edge['total_time']
        updated_values['driving_time'] = values['driving_time'] + edge['time']
        updated_values['distance'] = values['distance'] + edge['distance']
        updated_values['price'] = values['price'] + edge['price']

        return updated_values

    def compare(self, values, approximation):

        values_expectation = self.expectation(values[self.cost])
        approximation_expectation  = self.expectation(approximation[self.cost])

        savings = values_expectation < approximation_expectation 

        return values_expectation, savings

    def edge_feasible(self, edge):

        if edge.get('type', '') == 'to_destination':

            min_edge_distance = 0

        else:

            min_edge_distance = self.min_edge_distance

        feasible = in_range(
            edge['distance'],
            min_edge_distance,
            self.range,
            )

        return feasible

    def energy(self, station, edge):

        charge_rate = min([self.charge_rate, station.charge_rate])

        edge_energy = self.consumption * edge['distance']

        feasible = self.edge_feasible(edge)

        if feasible:

            charge_duration = edge_energy / charge_rate

            return feasible, edge_energy, charge_duration

        else:

            charge_duration = (
                self.usable_capacity / charge_rate + self.out_of_charge_penalty
                )

            return feasible, edge_energy, charge_duration

class Station():

    def __init__(self, **kwargs):

        self.seed = kwargs.get('seed', None)
        self.rng = kwargs.get('rng', np.random.default_rng(self.seed))

        self.cases = kwargs.get('cases', 1) # [-]

        # Parameters for charge events
        self.charge_rate = kwargs.get('charge_rate', lambda rng: 400e3)(self.rng)
        self.charge_price = kwargs.get('charge_price', lambda rng: .5 / 3.6e6)(self.rng) # [$/J]

        self.queue_time = kwargs.get('queue_time', lambda rng: 0)(self.rng) # [s]
        self.setup_time = kwargs.get('setup_time', lambda rng: 0)(self.rng) # [s]

        self.delay_time = np.zeros(self.cases) + self.queue_time + self.setup_time
        
        self.risk_attitude = None
        self.delay_time_expected = None


    def expect(self, vehicle):

        if self.risk_attitude != vehicle.risk_attitude:

            self.risk_attitude = vehicle.risk_attitude

            self.delay_time_expected = super_quantile(self.delay_time, self.risk_attitude)

    def update(self, vehicle, edge):

        feasible, charge_energy, charge_duration = vehicle.energy(self, edge)

        if vehicle.cases == 1:

            self.expect(vehicle)

            delay_time = self.delay_time_expected

        else:

            delay_time = self.delay_time

        if self.charge_rate == np.inf:

            charge_duration = 0
            delay_time = 0

        edge['feasible'] = feasible
        edge['energy'] = charge_energy
        edge['charge_time'] = charge_duration
        edge['total_time'] = edge['time'] + delay_time + charge_duration

        return edge

class SimulatedStation(Station):

    def __init__(self, **kwargs):

        self.seed = kwargs.get('seed', None)
        self.rng = kwargs.get('rng', np.random.default_rng(self.seed))

        self.cases = kwargs.get('cases', 1) # [-]

        # Parameters for charge events
        self.charge_rate = kwargs.get('charge_rate', lambda rng: 400e3)(self.rng)
        self.charge_price = kwargs.get('charge_price', lambda rng: .5 / 3.6e6)(self.rng) # [$/J]

        self.compute_queue_times(kwargs.get('queue', {}))
        self.setup_time = kwargs.get('setup_time', lambda rng: 0)(self.rng) # [s]

        self.delay_time = np.zeros(self.cases) + self.queue_time + self.setup_time
        
        self.risk_attitude = None
        self.delay_time_expected = None

    def compute_queue_times(self, kwargs):

        self.qtd = queuing_time_distribution(**kwargs)

        self.queue_time = self.qtd.rvs(size = self.cases, random_state = self.rng)