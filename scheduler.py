import threading, queue, time, random, math
from enum import Enum

class TaskType(Enum):
    TRIP_MATCHING = 0
    PAYMENT = 1
    FEEDBACK = 2

class Scheduler:
    def __init__(self):
        self.queues = {
            TaskType.TRIP_MATCHING: queue.PriorityQueue(),
            TaskType.PAYMENT: queue.Queue(),
            TaskType.FEEDBACK: queue.Queue()
        }
        self.riders = {}
        self.customers = [f"Customer_{i}" for i in range(1, 41)]
        self.customer_status = {}
        self.lock = threading.Lock()
        self.log_lock = threading.Lock()
        self.metrics = {
            'trip_busy': 0.0,
            'trip_idle': 0.0,
            'payment_busy': 0.0,
            'payment_idle': 0.0,
            'feedback_busy': 0.0,
            'feedback_idle': 0.0,
            'trip_response_times': [],
            'throughput': 0,
            'completed_trips': 0
        }
        self.running = False
        self.logs = []
        
        for cust in self.customers:
            self.customer_status[cust] = {
                'status': 'idle',
                'lock': threading.Lock(),
                'location': (random.uniform(0, 100), random.uniform(0, 100))
            }

    def reset(self):
        with self.lock:
            for q in self.queues.values():
                while not q.empty():
                    q.get()
            self.metrics = {
                'trip_busy': 0.0,
                'trip_idle': 0.0,
                'payment_busy': 0.0,
                'payment_idle': 0.0,
                'feedback_busy': 0.0,
                'feedback_idle': 0.0,
                'trip_response_times': [],
                'throughput': 0,
                'completed_trips': 0
            }
            self.logs = []
            for rider in self.riders.values():
                rider['status'] = 'available'
                rider['feedback'] = []
                rider['trips_completed'] = 0
            for cust in self.customer_status.values():
                cust['status'] = 'idle'

    def add_rider(self, rider_id):
        with self.lock:
            self.riders[rider_id] = {
                'status': 'available',
                'location': (random.uniform(0, 100), random.uniform(0, 100)),
                'feedback': [],
                'trips_completed': 0,
                'lock': threading.Lock()
            }

    def _calculate_distance(self, point1, point2):
        return math.sqrt((point1[0]-point2[0])**2 + (point1[1]-point2[1])**2)

    def _get_best_rider(self, customer_loc):
        min_distance = float('inf')
        candidate_riders = []
        
        # First pass: Find minimum distance
        for rider_id, rider in self.riders.items():
            with rider['lock']:
                if rider['status'] != 'available':
                    continue
                distance = self._calculate_distance(customer_loc, rider['location'])
                if distance < min_distance:
                    min_distance = distance
                    candidate_riders = [(rider_id, rider)]
                elif distance == min_distance:
                    candidate_riders.append((rider_id, rider))

        if not candidate_riders:
            return None

        # Second pass: Evaluate feedback and trips for closest riders
        best_score = -1
        best_rider_id = None
        for rider_id, rider in candidate_riders:
            avg_feedback = (sum(rider['feedback']))/len(rider['feedback']) if rider['feedback'] else 3.0
            trips = rider['trips_completed']
            score = (avg_feedback * 0.7) + (trips * 0.3)
            if score > best_score:
                best_score = score
                best_rider_id = rider_id

        return best_rider_id

    def add_task(self, task_type, priority, task):
        if task_type == TaskType.TRIP_MATCHING:
            self.queues[task_type].put((priority, time.time(), task))
        else:
            self.queues[task_type].put(task)

    def process_trip_matching_tasks(self):
        while self.running:
            start_time = time.time()
            if not self.queues[TaskType.TRIP_MATCHING].empty():
                time.sleep(0.7)  # Increased processing time
                _, _, task = self.queues[TaskType.TRIP_MATCHING].get()
                task()
                self.metrics['trip_busy'] += time.time() - start_time
            else:
                time.sleep(0.1)

    def process_payment_tasks(self):
        while self.running:
            start_time = time.time()
            if not self.queues[TaskType.PAYMENT].empty():
                time.sleep(0.5)  # Increased processing time
                task = self.queues[TaskType.PAYMENT].get()
                task()
                self.metrics['payment_busy'] += time.time() - start_time
            else:
                time.sleep(0.1)

    def process_feedback_tasks(self):
        while self.running:
            start_time = time.time()
            if not self.queues[TaskType.FEEDBACK].empty():
                time.sleep(0.3)  # Increased processing time
                task = self.queues[TaskType.FEEDBACK].get()
                task()
                self.metrics['feedback_busy'] += time.time() - start_time
            else:
                time.sleep(0.1)

    def _simulate_trip(self, customer):
        def execute_trip():
            start_time = time.time()
            with self.log_lock:
                self.logs.append(f"🚗 [{customer}] Searching for rider...")
            
            customer_loc = self.customer_status[customer]['location']
            best_rider = self._get_best_rider(customer_loc)
            
            if best_rider:
                response_time = time.time() - start_time
                self.metrics['trip_response_times'].append(response_time)
                self.metrics['throughput'] += 1
                with self.riders[best_rider]['lock']:
                    self.riders[best_rider]['status'] = 'busy'
                with self.log_lock:
                    self.logs.append(f"✅ [{customer}] Matched with {best_rider} in {response_time:.3f}s")
                
                trip_duration = random.uniform(3.0, 8.0)
                time.sleep(trip_duration)
                
                with self.riders[best_rider]['lock']:
                    self.riders[best_rider]['status'] = 'available'
                    self.riders[best_rider]['trips_completed'] += 1
                with self.log_lock:
                    self.logs.append(f"🏁 [{customer}] Trip completed ({trip_duration:.1f}s) → Processing payment")
                self.add_task(TaskType.PAYMENT, 0, lambda: self._process_payment(customer, best_rider))
            else:
                with self.log_lock:
                    self.logs.append(f"⚠️ [{customer}] No riders available. Retrying...")
                time.sleep(0.5)
                self.add_task(TaskType.TRIP_MATCHING, 2, lambda: self._simulate_trip(customer))
        
        threading.Thread(target=execute_trip).start()

    def _process_payment(self, customer, rider):
        with self.log_lock:
            self.logs.append(f"💸 [{customer}] Processing payment...")
        
        payment_time = random.uniform(0.5, 1.5)
        time.sleep(payment_time)
        
        with self.log_lock:
            self.logs.append(f"✅ [{customer}] Payment processed ({payment_time:.1f}s) → Collecting feedback")
            self.metrics['completed_trips'] += 1
        self.add_task(TaskType.FEEDBACK, 0, lambda c=customer, r=rider: self._collect_feedback(c, r))

    def _collect_feedback(self, customer, rider):
        with self.log_lock:
            self.logs.append(f"🌟 [{customer}] Collecting feedback...")
        
        time.sleep(0.5)
        feedback = random.choices([1, 2, 3, 4, 5], weights=[1, 2, 3, 4, 5])[0]
        
        with self.riders[rider]['lock']:
            self.riders[rider]['feedback'].append(feedback)
        with self.log_lock:
            self.logs.append(f"⭐ [{customer}] Gave {feedback} stars to {rider}")
        with self.customer_status[customer]['lock']:
            self.customer_status[customer]['status'] = 'idle'

    def simulate_task_arrivals(self):
        while self.running:
            if random.random() < 0.9:  # Higher probability
                available_customers = [cust for cust in self.customers 
                                    if self.customer_status[cust]['status'] == 'idle']
                if available_customers:
                    customer = random.choice(available_customers)
                    with self.customer_status[customer]['lock']:
                        self.customer_status[customer]['status'] = 'in_trip'
                    self.add_task(TaskType.TRIP_MATCHING, random.randint(1, 5), lambda c=customer: self._simulate_trip(c))
            time.sleep(random.uniform(0.1, 0.3))  # Shorter interval