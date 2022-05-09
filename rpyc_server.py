import rpyc
import random
import _thread
import datetime
from rpyc.utils.server import ThreadedServer
from copy import deepcopy

system_start = datetime.datetime.now()
processes = {}  # list to store all the processes
undefined = 0

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

def print_order_message(minimal_satisfied, k, order, quorum, total, undefined):
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

        majority_quorum = quorum/total
        if majority_quorum > 0.5:
            print(f'Execute order: {order}! {k} faulty node{s} in the system –{quorum} out of {total} '
                  f'quorum suggest {order}')

        else:
            print(f'Execute order: cannot be determined – not enough generals in the system! {k} faulty node{s} '
                  f'in the system {undefined} out of {total} quorum not consistent')
    print()

class Process:
    def __init__(self, id_: int):
        self.id = id_ # 1 to N

        # default variables
        self._status = "NF" # "F" (Faulty) / "NF" (Non-faulty)
        self.majority = "undefined" # "attack" / "retreat"
        self.role = "secondary" # or "primary"
        self.received_status_from_primary = []
        self.received_status_from_secondary = []

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, val):
        assert val in ("NF", "F")
        self._status = val


    def run(self):
        while True:
            pass

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
        global undefined
        undefined = 0
        order = "attack"

        #first message round
        prim_idx = list(processes.keys())[0]
        primary = processes[prim_idx]

        faulty_secondary_exists = False

        true_messages = len(processes) - 1
        for p in processes.values():
            if p.role != "primary":
                if p.status == "F":
                    faulty_secondary_exists = True
                if primary.status == "NF":
                    p.received_status_from_primary.append("T")
                else:
                    status_to_send = random.choice(["T", "F"]) # primary sends value "T" or "F" with 50% probability
                    p.received_status_from_primary.append(status_to_send)
                    if status_to_send == "F":
                        true_messages -= 1
        second_message_round = False

        if true_messages == (len(processes) - 1):
            if faulty_secondary_exists:
                second_message_round = True
            else:
                # in case there all secondary are NF
                for p in processes.values():
                    p.majority = order
                    p.received_status_from_primary = []
        else:
            second_message_round = True

        secondary_processes = deepcopy(processes)
        del secondary_processes[prim_idx]

        if second_message_round:
            # second message round
            # here all secondary generals exchange messages

            for p_send in secondary_processes.values():
                for p_receive in secondary_processes.values():
                    if p_send.id != p_receive.id:
                        if p_send.status == "NF":
                            from_primary = p_send.received_status_from_primary
                            p_receive.received_status_from_secondary.append(from_primary)
                        else:
                            status_to_send = random.choice(
                                ["T", "F"])  # secondary sends value "T" or "F" with 50% probability
                            p_receive.received_status_from_secondary.append(status_to_send)

            for p in secondary_processes.values():
                values_received = []
                from_prim = p.received_status_from_primary[0]
                values_received.append(from_prim)
                for from_secondary in p.received_status_from_secondary:
                    values_received.append(from_secondary[0])

                true_messages = values_received.count("T")
                false_messages = values_received.count("F")

                if true_messages > false_messages:
                    p.majority = order
                elif true_messages < false_messages:
                    p.majority = "retreat"
                else:
                    undefined += 1


            primary.majority = order
            print(f'G{primary.id}, majority={primary.majority}, state={primary.status}')
            for p in secondary_processes.values():
                print(f'G{p.id}, {p.role}, majority={p.majority}, state={p.status}')

        else:
            for p in processes.values():
                print(f'G{p.id}, {p.role}, majority={order}, state={p.status}')


        total = len(processes)
        quorum = 0
        quorum_attack = 0
        quorum_retreat = 0

        if second_message_round:
            for key in secondary_processes.keys():
                p = secondary_processes[key]
                if p.role == "secondary":
                    if p.majority == "retreat":
                        quorum_retreat += 1
                    if p.majority == "attack":
                        quorum_attack += 1

            if quorum_retreat > quorum_attack:
                order = "retreat"
                quorum = quorum_retreat
            else:
                quorum = quorum_attack


        else:
            for key in processes.keys():
                p = processes[key]
                if p.role == "secondary":
                    if p.status == "NF":
                        quorum += 1


        minimal_satisfied, k = check_nodes_minimal_number()
        print_order_message(minimal_satisfied, k, order, quorum, total, undefined)


    def exposed_actual_order_retreat(self):
        print("Got the following command from client: actual-order retreat")
        global undefined
        undefined = 0
        order = "retreat"

        # first message round
        prim_idx = list(processes.keys())[0]
        primary = processes[prim_idx]

        faulty_secondary_exists = False

        true_messages = len(processes) - 1
        for p in processes.values():
            if p.role != "primary":
                if p.status == "F":
                    faulty_secondary_exists = True
                if primary.status == "NF":
                    p.received_status_from_primary.append("T")
                else:
                    status_to_send = random.choice(["T", "F"])  # primary sends value "T" or "F" with 50% probability
                    p.received_status_from_primary.append(status_to_send)
                    if status_to_send == "F":
                        true_messages -= 1
        second_message_round = False

        if true_messages == (len(processes) - 1):
            if faulty_secondary_exists:
                second_message_round = True
            else:
                # in case there all secondary are NF
                for p in processes.values():
                    p.majority = order
                    p.received_status_from_primary = []
        else:
            second_message_round = True

        secondary_processes = deepcopy(processes)
        del secondary_processes[prim_idx]

        if second_message_round:
            # second message round
            # here all secondary generals exchange messages

            for p_send in secondary_processes.values():
                for p_receive in secondary_processes.values():
                    if p_send.id != p_receive.id:
                        if p_send.status == "NF":
                            from_primary = p_send.received_status_from_primary
                            p_receive.received_status_from_secondary.append(from_primary)
                        else:
                            status_to_send = random.choice(
                                ["T", "F"])  # secondary sends value "T" or "F" with 50% probability
                            p_receive.received_status_from_secondary.append(status_to_send)

            for p in secondary_processes.values():
                values_received = []
                from_prim = p.received_status_from_primary[0]
                values_received.append(from_prim)
                for from_secondary in p.received_status_from_secondary:
                    values_received.append(from_secondary[0])

                true_messages = values_received.count("T")
                false_messages = values_received.count("F")

                if true_messages > false_messages:
                    p.majority = order
                elif true_messages < false_messages:
                    p.majority = "attack"
                else:
                    undefined += 1

            primary.majority = order
            print(f'G{primary.id}, majority={primary.majority}, state={primary.status}')
            for p in secondary_processes.values():
                print(f'G{p.id}, {p.role}, majority={p.majority}, state={p.status}')

        else:
            for p in processes.values():
                print(f'G{p.id}, {p.role}, majority={order}, state={p.status}')

        total = len(processes)
        quorum = 0
        quorum_attack = 0
        quorum_retreat = 0

        if second_message_round:
            for key in secondary_processes.keys():
                p = secondary_processes[key]
                if p.role == "secondary":
                    if p.majority == "attack":
                        quorum_retreat += 1
                    if p.majority == "retreat":
                        quorum_attack += 1

            if quorum_retreat > quorum_attack:
                order = "attack"
                quorum = quorum_retreat
            else:
                quorum = quorum_attack


        else:
            for key in processes.keys():
                p = processes[key]
                if p.role == "secondary":
                    if p.status == "NF":
                        quorum += 1

        minimal_satisfied, k = check_nodes_minimal_number()
        print_order_message(minimal_satisfied, k, order, quorum, total, undefined)


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
