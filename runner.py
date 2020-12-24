import subprocess
import logging
import argparse


# DO NOT FORGET TO ADD HELP FOR ARGS!!!!
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', help="the command to execute")  # mandatory
    parser.add_argument('-c', '--count', default=4, type=int, help="number of times to execute the command")  # optional - default is 4 like in ping, should be changed?
    parser.add_argument('--failed-count', type=int,
                        help="number of allowed failed command invocation attempts before giving up, defaults to 'count' value")  # optional
    parser.add_argument('--sys-trace', action="store_true", help="")  # optional
    parser.add_argument('--call-trace', action="store_true", help="")  # optional
    parser.add_argument('--log-trace', action="store_true", help="")  # optional
    parser.add_argument('--debug', action="store_true", help="")  # optional
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(format='%(levelname)s:%(message)s', level=log_level)
    command = args.command.split()
    failed_count = args.failed_count or args.count  # if args.failed_count is none, use the value of args.count
    return_codes = {}  # the dict will be used as  return_code: number of appearances
    try:
        for run in range(1, args.count+1):
            logging.debug('now execute command for the %d time', run)
            execute = subprocess.run(command)
            if execute.returncode != 0:
                if failed_count == 0:  # if we reached the max failed attempts break out of the loop and exit.
                    logging.info('i reached max failed attempts, I GIVE UP')
                    break
                logging.debug('command return code is %d', execute.returncode)
                failed_count -= 1  # decrease the allowed fail until 0 than break
            if execute.returncode in return_codes:  # check if return code happened before
                return_codes[execute.returncode] += 1  # if it was, will increase the key by 1
            else:
                return_codes[execute.returncode] = 1  # if it's the first time, will add to dict
    finally:
        sorted_dict = sorted(return_codes.items(), reverse=True, key=lambda code: code[1])  # sort the dict by the values
        if sorted_dict:
            logging.info("the most frequent return code was %d", sorted_dict[0][0])
            return sorted_dict[0][0]  # return the key with the biggest value
        else:
            logging.error("the command didn't run even once! something bad happened ")


if __name__ == '__main__':
    main()
