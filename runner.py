import subprocess
import logging
import argparse
import tempfile
import os

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', help="the command to execute")  # mandatory
    parser.add_argument('-c', '--count', default=4, type=int,
                        help="number of times to execute the command")  # optional
    parser.add_argument('--failed-count', type=int,
                        help="number of allowed failed command invocation attempts before giving up, defaults to 'count' value")  # optional
    parser.add_argument('--sys-trace', action="store_true",
                        help="for each failed execution print logs for Disk IO, Memory, CPU usage and Network")  # optional
    parser.add_argument('--call-trace', action="store_true",
                        help="for each failed execution print all the system calls ran by the command")  # optional
    parser.add_argument('--log-trace', action="store_true",
                        help="for each failed execution print the command output logs")  # optional
    parser.add_argument('--net-trace', action="store_true",
                        help="for each failed execution create a 'pcap' file with the network traffic during the execution")  # optional
    parser.add_argument('--debug', action="store_true", help="debug mode")  # optional
    args = parser.parse_args()
    return args


def logging_config(debug):
    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(format='%(levelname)s:%(message)s', level=log_level)


def build_command(command, strace_log):
    if strace_log:
        final_command = f"strace -o {strace_log.name} {command}"
    else:
        final_command = command
    return final_command


def print_sys_trace(disk_log, memory_log, cpu_log, network_log):
    print("Failed to execute. printing resources logs:")
    print("Disk IO:")
    print(disk_log.stdout.read())
    print("Memory:")
    print(memory_log.stdout.read())
    print("CPU usage:")
    print(cpu_log.stdout.read())
    print("Network package counters:")
    print(network_log.stderr.read())


def print_system_calls(strace_log_path):
    print("Failed to execute. printing system calls:")
    file = open(strace_log_path, "r")
    print(file.read())
    file.close()


def print_log_trace(execute):
    stdout = execute.stdout.read()
    stderr = execute.stderr.read()
    print("Failed to execute. printing available output logs:")
    if stdout:
        print("stdout:")
        print(stdout)
    if stderr:
        print("stderr:")
        print(stderr)


def main():
    args = get_args()
    logging_config(args.debug)
    if args.call_trace:
        strace_log = tempfile.NamedTemporaryFile()
    else:
        strace_log = None
    command = build_command(args.command, strace_log)
    failed_count = args.failed_count or args.count  # if args.failed_count is none, use the value of args.count
    return_codes = {}  # the dict will be used as  return_code: number of appearances
    try:
        for run in range(1, args.count+1):
            logging.debug('now execute command for the %d time', run)
            if args.sys_trace or args.net_trace:
                tcpdump_command = "tcpdump -v -i any"
                if args.net_trace:
                    tcpdump_command += f" -w cap_while_{run}_execute.pcap"
                network_log = subprocess.Popen(tcpdump_command, shell=True, text=True,
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            execute = subprocess.Popen(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if args.sys_trace:
                disk_log = subprocess.Popen(f"pidstat -d -T ALL -p {execute.pid} 1", shell=True, text=True,
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                memory_log = subprocess.Popen(f"pidstat -r -T ALL -p {execute.pid} 1", shell=True, text=True,
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cpu_log = subprocess.Popen(f"pidstat -u -T ALL -p {execute.pid} 1", shell=True, text=True,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            execute.wait()
            if args.sys_trace or args.net_trace:
                network_log.terminate()
                network_log.wait()
            if execute.returncode != 0:
                if failed_count == 0:  # if we reached the max failed attempts break out of the loop and exit.
                    logging.info('i reached max failed attempts, I GIVE UP')
                    break
                logging.debug('command return code is %d', execute.returncode)
                failed_count -= 1  # decrease the allowed fail until 0 than break
                if args.sys_trace:
                    print_sys_trace(disk_log, memory_log, cpu_log, network_log)
                if args.call_trace:
                    print_system_calls(strace_log.name)
                if args.log_trace:
                    print_log_trace(execute)
            elif args.net_trace and os.path.exists(f"cap_while_{run}_execute.pcap"):
                os.remove(f"cap_while_{run}_execute.pcap")
            if execute.returncode in return_codes:  # check if return code happened before
                return_codes[execute.returncode] += 1  # if it was, will increase the key by 1
            else:
                return_codes[execute.returncode] = 1  # if it's the first time, will add to dict

    finally:
        if args.call_trace:
            strace_log.close()
        sorted_dict = sorted(return_codes.items(), reverse=True, key=lambda code: code[1])  # sort the dict by the values
        if sorted_dict:
            logging.info("the most frequent return code was %d", sorted_dict[0][0])
            return sorted_dict[0][0]  # return the key with the biggest value
        else:
            logging.error("the command didn't run even once! something bad happened")


if __name__ == '__main__':
    main()
