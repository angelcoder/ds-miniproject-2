import rpyc
import random
import _thread
import datetime
from rpyc.utils.server import ThreadedServer


class Message:
    def __init__(self, resource_name: str, process_id: int, logical_time: int):
        self.resource_name = resource_name
        self.process_id = process_id
        self.logical_time = logical_time

    def __repr__(self):
        return f"Message(resource_name={self.resource_name}, process_id={self.process_id}, logical_time={self.logical_time})"


system_start = datetime.datetime.now()
processes = {}  # list to store all the processes


def check_nodes_minimal_number():
    k = 0
    total = len(processes)
    for key in processes.keys():
        p = processes[key]
        if p.status == "F":
            k += 1

    minimal_satisfied = True
    min_number = 3 * k + 1
    if total < min_number:
        minimal_satisfied = False
        return minimal_satisfied, k
    return minimal_satisfied, k

def print_order_message(minimal_satisfied, k, order, quorum, total):
    s = ''
    if k > 1:
        s = 's'

    if minimal_satisfied:
        if k == 0:
            print(f'Execute order: {order}! Non-faulty nodes in the system –{quorum} out of {total} '
                  f'quorum suggest {order}')
        else:
            print(f'Execute order: {order}! {k} faulty node{s} in the system –{quorum} out of {total} '
                  f'quorum suggest {order}')

    else:
        print(f'Execute order: cannot be determined – not enough generals in the system! {k} faulty node{s} in the '
              f'system {quorum} out of {total} quorum not consistent')
    print()

class Process:
    def __init__(self, id_: int):
        self.id = id_ # 1 to N

        # default variables
        self._status = "NF" # "F" (Faulty) / "NF" (Non-faulty)
        self.majority = "undefined" # "attack" / "retreat"
        self.role = "secondary" # or "primary"
        self.received_status = []
        self.received_generals = []

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

        # attack = "cannot be determined"
        order = "attack"

        print(processes.values(), processes.keys())

        #first message round
        prim_idx = list(processes.keys())[0]
        print(prim_idx)
        print(processes)
        primary = processes[prim_idx]

        faulty_secondary_exists = False

        true_messages = len(processes) - 1
        for p in processes.values():
            if p.role != "primary":
                if p.status == "F":
                    faulty_secondary_exists = True
                if primary.status == "NF":
                    p.received_status.append("T")
                else:
                    status_to_send = random.choice(["T", "F"]) # primary sends value "T" or "F" with 50% probability
                    p.received_status.append(status_to_send)
                    if status_to_send == "F":
                        true_messages -= 1
        second_message_round = False

        if true_messages == len(processes) - 1:
            if faulty_secondary_exists:
                second_message_round = True
            else:
                # in case there all secondary are NF
                for p in processes.values():
                    p.majority = order
                    p.received_status = []
                    print(f'G{p.id}, {p.role}, majority={p.majority}, state={p.status}')
        else:
            second_message_round = True

        if second_message_round:
            # second message round
            # here all secondary generals exchange messages


        # for idx in list(processes.keys())[1:]:
        #     print(list(processes.values())[idx].id)

        # for p in processes.values():
        #     for pr in processes.values():
        #         if p.id != pr.id:
        #             print(p.id, pr.id)
        #             print(p.status, pr.status)
        #             if pr.id not in p.received_generals:
        #                 p.received_generals.append(pr.id)
        #                 if p.status == "F":
        #                     pr.received_status.append(0)
        #                 else:
        #                     pr.received_status.append(1)

        for p in processes.values():
            print(p.id, p.status, p.received_status)

        # if ..:
        #     attack = True
        # else:
        #     attack = False
        total = len(processes)
        quorum = 0
        for key in processes.keys():
            p = processes[key]
            if p.role == "secondary":
                if p.status == "NF":
                    quorum+=1

        minimal_satisfied, k = check_nodes_minimal_number()
        print_order_message(minimal_satisfied, k, order, quorum, total)


    def exposed_actual_order_retreat(self):
        print("Got the following command from client: actual-order retreat")
        for p in processes.values():
            p.majority = "retreat"

        for p in processes.values():
            print(f'G{p.id}, {p.role}, majority={p.majority}, state={p.status}')
        # attack = "cannot be determined"
        order = "retreat"

        # if ..:
        #     attack = True
        # else:
        #     attack = False
        total = len(processes)
        quorum = 0
        for key in processes.keys():
            p = processes[key]
            if p.role == "secondary":
                if p.status == "NF":
                    quorum += 1

        minimal_satisfied, k = check_nodes_minimal_number()
        print_order_message(minimal_satisfied, k, order, quorum, total)


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
        for _k in range(1, k+1):
            pos = last_element+_k
            p = Process(pos)
            processes[pos] = p

        for p in processes.values():
            print(f'G{p.id}, state={p.role}')
        print()



if __name__ == '__main__':
    t = ThreadedServer(MonitorService, port=18812)
    t.start()
