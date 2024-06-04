import time
import numpy as np

from heapq import heappop, heappush
from itertools import count
from scipy.stats import rv_histogram

class Server():

	def __init__(self, **kwargs):

		self.rng = kwargs.get('rng', np.random.default_rng())

		self.service_rate = kwargs.get('service_rate', lambda rng: 1)(self.rng) # [u/s]

		self.customer = None

		self.status = 'vacant'

	def start(self, customer):

		self.customer = customer

		self.status = 'occupied'

	def step(self, step):

		self.customer.step(step)

		status = self.customer.receive(self.service_rate, step)

		if status == 'complete':

			self.status = 'complete'

	def finish(self):

		self.status = 'vacant'

		return self.customer

class Demand():

	def __init__(self, **kwargs):

		self.rng = kwargs.get('rng', np.random.default_rng())

		self.max_length = kwargs.get('max_length', np.inf)

		self.inter_arrival = kwargs.get('inter_arrival', lambda rng: rng.exponential(1))

		self.interval = self.inter_arrival(self.rng)

		self.capacity = kwargs.get('capacity', lambda rng: 1) # [u]

		self.initial = kwargs.get('initial', 0)

		self.initial_customers = (
			[Customer(capacity = self.capacity(self.rng)) for idx in range(self.initial)]
			)
		
	def spawn(self, step):


		self.interval -= step
		# print(self.interval)

		if self.interval <= 0:

			self.interval = self.inter_arrival(self.rng)

			return Customer(capacity = self.capacity(self.rng))

class Customer():

	def __init__(self, **kwargs):

		self.capacity = kwargs.get('capacity', 1) # [u]

		self.level = 0

		self.steps = 0
		self.steps_service = 0

		self.status = 'queuing'

	def step(self, step):

		self.steps += step
	
	def receive(self, service_rate, step):

		self.status = 'receiving'

		self.level += service_rate * step

		self.steps_service += step

		if self.level >= self.capacity:

			self.status = 'complete'

		return self.status

class System():

	def __init__(self, servers, demand):

		self.servers = servers
		self.demand = demand

	def simulate(self, steps = 1000, step = 1):

		counter = count()

		queue = []
		served = []

		for customer in self.demand.initial_customers:

			heappush(queue, (next(counter), customer))

		in_queue = 0
		in_service = 0
		in_served = 0

		status = {
			'in_queue': [],
			'in_service': [],
			'in_served': [],
		}

		for idx in range(0, steps, step):

			# Advancing customers
			for customer in queue:

				customer[1].step(step)

			# Creating new customers
			customer = self.demand.spawn(step)

			if (customer is not None) and (len(queue) <= self.demand.max_length - 1):

				heappush(queue, (next(counter), customer))

				in_queue += 1

			# Advancing servers
			for server in self.servers:

				# Simulating one step
				if server.status == 'occupied':

					server.step(step)

				# Moving served customers
				if server.status == 'complete':

					customer = server.finish()

					served.append(customer)

					in_service -= 1
					in_served += 1

				# Moving customers to vacant servers
				if (server.status) == 'vacant' and queue:

					_, customer = heappop(queue)

					server.start(customer)

					in_queue -= 1
					in_service += 1

			status['in_queue'].append(in_queue)
			status['in_service'].append(in_service)
			status['in_served'].append(in_served)

		return queue, served, status

def queuing_time_distribution(**kwargs):

	servers = [Server(**kwargs.get('server', {})) for idx in range(kwargs.get('n', 1))]

	demand = Demand(**kwargs.get('demand', {}))

	system = System(servers, demand)

	_, served, _ = system.simulate(**kwargs.get('simulation', {}))

	queue_steps = np.array([customer.steps - customer.steps_service for customer in served])

	return rv_histogram(np.histogram(queue_steps, **kwargs.get('histogram', {})))

