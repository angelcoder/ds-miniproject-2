import rpyc
import time
import random
import _thread
import datetime
from rpyc.utils.server import ThreadedServer

# class CriticalSection:
#     def __init__(self):
#         self.t_low = 10
#         self.t_up = 10
#
#     def possess(self):
#         """" simulate resource possession"""
#         time.sleep(self.gen_hold_time)  # simulate possession
#
#     @property
#     def gen_hold_time(self):
#         """generate random value within [t_up, t_low] range"""
#         return random.random() * (self.t_up - self.t_low) + self.t_low


class Message:
    def __init__(self, resource_name: str, process_id: int, logical_time: int):
        self.resource_name = resource_name
        self.process_id = process_id
        self.logical_time = logical_time

    def __repr__(self):
        return f"Message(resource_name={self.resource_name}, process_id={self.process_id}, logical_time={self.logical_time})"


system_start = datetime.datetime.now()
processes = {}  # list to store all the processes

class Process:
    def __init__(self, id_: int):
        self.id = id_ # 1 to N

        # default variables
        self._status = "NF" # "F" (Faulty) / "NF" (Non-faulty)
        self.majority = "undefined" # "attack" / "retreat"
        self.role = "secondary" # or "primary"

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, val):
        assert val in ("NF", "F")
        self._status = val


    def request(self, msg):
        """generate response to a request"""
        if self._status == "DO-NOT-WANT" or (self._status == "WANTED" and msg.logical_time < self.logical_time):
            return "OK"  # reply message

    def run(self):
        while True:
            pass
            # diff = time.perf_counter() - self.tick  # time passed
            # if diff > self.gen_time_out:
            #     # switch status and send messages
            #     self.status = "WANTED"
            #     self.broadcast()
            #
            #     # wait until all the reply messages to be "OK"
            #     responses = self.responses.values()
            #     while not all(map(lambda r: r == "OK", responses)):
            #         responses = self.responses.values()
            #
            #     # possession
            #     self.status = "HELD"
            #     self.status = "DO-NOT-WANT"
            #
            #     # send reply messages to deferred requests
            #     for p in processes.values():
            #         if self.id != p.id:
            #             p.responses[self.id] = "OK"
            #
            #     self.reset_tick()

    # starts a thread that runs the process
    def start(self):
        _thread.start_new_thread(self.run, ())


class MonitorService(rpyc.Service):
    def on_connect(self, conn):
        print("\nconnected on {}".format(system_start))

    def on_disconnect(self, conn):
        print("disconnected on {}\n".format(system_start))

    def exposed_setup(self, N: int):
        """create and start N processes"""
        p = Process(1)
        p.role = "primary"
        processes[1] = p

        for i in range(2, N+1):
            p = Process(i)
            processes[i] = p

        # start threads of all processes
        for p in processes.values():
            p.start()

    def exposed_actual_order_attack(self):
        print("Got the following command from client: actual-order attack")
        for p in processes.values():
            p.majority = "attack"

        for p in processes.values():
            print(f'G{p.id}, {p.role}, majority={p.majority}, state={p.status}')
        # attack = "cannot be determined"
        attack = "attack"
        # if ..:
        #     attack = True
        # else:
        #     attack = False
        print(f'Execute order: {attack}! Non-faulty nodes in the system –{1} out of {2} quorum suggest {attack}')
        print()


    def exposed_actual_order_retreat(self):
        print("Got the following command from client: actual-order retreat")
        for p in processes.values():
            p.majority = "retreat"

        for p in processes.values():
            print(f'G{p.id}, {p.role}, majority={p.majority}, state={p.status}')
        # attack = "cannot be determined"
        attack = "retreat"

        # if ..:
        #     attack = True
        # else:
        #     attack = False

        print(f'Execute order: {attack}! Non-faulty nodes in the system –{1} out of {2} quorum suggest {attack}')
        print()

    def exposed_g_state(self):
        print("Got the following command from client: g-state")
        for p in processes.values():
            print(f'G{p.id}, {p.role}, state={p.status}')
        print()


    def exposed_g_state_ID_state(self, id: int, state: str):
        print(f'Got the following command from client: g-state {id} {state}')
        p = processes[id]
        if state == "faulty":
            p.status = "F"
        if state == "non-faulty":
            p.status = "NF"

        for p in processes.values():
            print(f'G{p.id}, state={p.status}')
        print()


    def exposed_g_kill_ID(self, id: int):
        print(f'Got the following command from client: g-kill {id}')
        p_delete = processes[id]
        processes.pop(id)

        if p_delete.role == "primary":
            next_primary = next(iter(processes.items()))[1]
            next_primary.role = "primary"

        for p in processes.values():
            print(f'G{p.id}, state={p.status}')
        print()


    def exposed_g_add_k(self, k: int):
        print(f'Got the following command from client: g-add {k}')
        last_element = list(processes)[-1]
        print(last_element)
        for _k in range(1, k+1):
            pos = last_element+_k
            p = Process(pos)
            processes[pos] = p

        for p in processes.values():
            print(f'G{p.id}, state={p.status}')
        print()



if __name__ == '__main__':
    t = ThreadedServer(MonitorService, port=18812)
    t.start()
