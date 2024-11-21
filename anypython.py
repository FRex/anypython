#!/usr/bin/env python3
"""A script to run another script through many versions of Python to check compatibility."""
import subprocess
import hashlib
import shlex
import glob
import sys


def eprint(*args):
    """Print through print to sys.stderr"""
    print(*args, file=sys.stderr)


def matching_version(desired: str, gotten: str) -> bool:
    """Check in many ways if gotten version is fit for desired version string"""
    # exact match
    if desired == gotten:
        return True

    # we asked for 3.x so let's try get 3.x.y for any y from 0 to 100
    if any(f"{desired}.{x}" == gotten for x in range(100)):
        return True

    # we asked for 3x so let's try get 3.x.y for any y from 0 to 100
    dotlessgotten = gotten.replace(".", "")
    if any(f"{desired}{x}" == dotlessgotten for x in range(100)):
        return True

    return False


def extract_exe_ver(exe: str) -> str:
    """Extract version string from a file path."""
    # TODO: make this more robust, maybe using a regex?
    return exe.split("/")[-1].split("-")[1]


def extract_exe_ver_int_tuple(exe: str) -> str:
    """Extract version string from a file path and return it as a tuple of ints for sorting."""
    return tuple(map(int, extract_exe_ver(exe).split(".")))


def main():
    """A main function to not run anything when imported as a module."""
    # find all the python.exe exes in direct sub-subdirs of D:/anypython/
    # TODO: make this directory come from env var or similar and take more exes than just -embed-win32
    exes = glob.glob("D:\\anypython\\python-*-embed-win32\\python.exe")
    exes = sorted(exes, key=extract_exe_ver_int_tuple)

    # check args and print small help and all available versions if args are wrong
    if len(sys.argv) < 2 or len(sys.argv[1]) < 2:
        eprint(
            "Pass version (2+ chars) or 'all' and any extra arguments, available versions:"
        )
        for exe in exes:
            eprint(exe.split("/")[-1].split("-")[1])
        sys.exit(1)

    # run via each version we have and do not forward the return codes
    # but print some extra banner before/after the runs
    outcomes = []
    if sys.argv[1] == "all":
        for exe in exes:
            # print the command then run it
            args = [exe] + sys.argv[2:]
            print(shlex.join(args) + " # running")
            result = subprocess.run(args, check=False, stdout=subprocess.PIPE)

            # dump to stdout as is, don't even decode/encode
            sys.stdout.flush()
            sys.stdout.buffer.write(result.stdout)
            sys.stdout.flush()

            # NOTE: extra newline at the end is to space out the output
            h = hashlib.sha512(result.stdout).hexdigest()[:35]
            print(f"Return code = {result.returncode} and hash of stdout = {h}\n")
            outcomes.append((exe, result.returncode, h))

        for out in outcomes:
            print(*out)

        return

    # find the exes
    found = []
    for exe in exes:
        exever = extract_exe_ver(exe)
        if matching_version(sys.argv[1], exever):
            found.append(exe)

    # no exes, print all available versions
    if len(found) == 0:
        eprint("Found no matching exes, available versions:")
        for exe in exes:
            eprint(exe.split("/")[-1].split("-")[1])
        sys.exit(1)

    # more than one exe, print all found versions
    if len(found) > 1:
        eprint("Found more than one matching version:")
        for exe in found:
            eprint(exe.split("/")[-1].split("-")[1])
        sys.exit(1)

    # run the found python exe with the extra arguments and forward return the exit code
    result = subprocess.run([found[0]] + sys.argv[2:], check=False)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
