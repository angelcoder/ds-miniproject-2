# ds-miniproject-2

* The program receives N as a parameter for starting its execution. Here, N is the number of
processes (each process is a thread and depicts a general) that are created concurrently. N
cannot be zero (N>0). All of these processes (generals) will forward a propose order (attack or
retreat) when planning the attack.
* Each general has a unique identifier in the range of (1 to N)
* Each general has a state value S, which can be set either to F (Faulty) or NF (Non-faulty).
* A general is elected as primary of the system, while others are secondary nodes. Notice that if
the primary is killed/crashed, it should be replaced by a secondary general (promoted to
primary).
