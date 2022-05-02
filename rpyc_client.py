import rpyc
import argparse


def main(N, conn):
    conn.root.exposed_setup(N)

    print("Commands: actual-order attack, actual-order retreat, g-state <ID> <State>, g-state, g-kill <ID>, g-add <K>")
    running = True
    while running:
        inp = input().lower()
        cmd = inp.split(" ")

        command = cmd[0]

        if len(cmd) > 4:
            print("Too many arguments")
        elif command == "exit":
            running = False
        elif command == "actual-order":
            if str(cmd[1]) == "attack":
                conn.root.actual_order_attack()
            if str(cmd[1]) == "retreat":
                conn.root.actual_order_retreat()
        elif command == "g-state":
            if len(cmd) == 1:
                conn.root.g_state()
            else:
                id = int(cmd[1])
                state = str(cmd[2])
                conn.root.g_state_ID_state(id, state)
        elif command == "g-kill":
            id = int(cmd[1])
            conn.root.g_kill_ID(id)
        elif command == "g-add":
            k = int(cmd[1])
            conn.root.g_add_k(k)
        else:
            print("Unsupported command:", inp)

    print("Program exited")


parser = argparse.ArgumentParser()
parser.add_argument('-N', type=int, required=True, help='number of processes to create')
parser.add_argument('--server', type=str, default='localhost', help='host')
args = parser.parse_args()
assert args.N > 0, "N must be at least 1"

conn = rpyc.connect(args.server, 18812)
main(args.N, conn)
