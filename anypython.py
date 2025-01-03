#!/usr/bin/env python3
"""A script to run another script through many versions of Python to check compatibility."""
import collections
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


def format_pretty_table(origdata, rjust=()) -> str:
    """Format a table using | to separate columns and - as a row separator."""
    data = [None if row is None else tuple(map(str, row)) for row in origdata]
    colcount = max(map(len, (row for row in data if row is not None)))
    maxlens = colcount * [0]
    for row in data:
        if row is None:
            continue
        for i, l1 in enumerate(map(len, row)):
            if l1 > maxlens[i]:
                maxlens[i] = l1
    ret = []
    for row in data:
        if row is None:
            ret.append("|".join("-" * width for width in maxlens))
        else:
            parts = []
            for i, (data, width) in enumerate(zip(row, maxlens)):
                if i in rjust:
                    parts.append(data.rjust(width))
                else:
                    parts.append(data.ljust(width))
            ret.append("|".join(parts))
    return "\n".join(ret)


# for each Python version note what Ubuntu xx.04 LTS it ships on
VERSION_NOTES = {
    (3, 5): " no f-strings ",
    (3, 6): " Ubuntu 18 ",
    (3, 8): " Ubuntu 20 ",
    (3, 10): " Ubuntu 22 ",
    (3, 12): " Ubuntu 24 ",
}


def get_note_for_exe(exe: str) -> str:
    """Get notes for a given python by its version, for example if it ships on Ubuntu LTS."""
    ver = extract_exe_ver_int_tuple(exe)
    ver = ver[:2]
    return VERSION_NOTES.get(ver, "")


SIGNIFICAN_HASH_CHARS = 35


def run_all(exes: list, argv2):
    """Run all exes and show summary results of errors and stdout hashes."""

    rows = []
    rows.append(
        (
            " Executable ",
            " Version ",
            "Code",
            f" Stdout Hash {SIGNIFICAN_HASH_CHARS} chars of SHA512 ",
            " Note",
            " # ",
        )
    )
    rows.append(None)

    counts = collections.defaultdict(int)
    for exe in exes:
        # print the command then run it, entire shlex join line is copy pasteable
        args = [exe] + argv2
        print(shlex.join(args) + " # running")
        result = subprocess.run(args, check=False, stdout=subprocess.PIPE)

        # dump to stdout as is, don't even decode/encode
        # TODO: check if those flushes are needed or not
        sys.stdout.flush()
        sys.stdout.buffer.write(result.stdout)
        sys.stdout.flush()

        # NOTE: extra newline at the end is to space out the output
        h = hashlib.sha512(result.stdout).hexdigest()[:SIGNIFICAN_HASH_CHARS]
        print(f"Return code = {result.returncode} and hash of stdout = {h}\n")
        rows.append(
            [
                f" {exe} ",
                extract_exe_ver(exe) + " ",
                f"{result.returncode} ",
                " " + h + " ",
                get_note_for_exe(exe),
                -1,
            ]
        )
        counts[rows[-1][-3]] += 1

    for i in range(2, len(rows)):
        rows[i][-1] = " " + str(counts[rows[i][-3]])

    # TODO: sort by stdout hash or something? and show some summary row?
    print(format_pretty_table(rows, rjust=(1, 2, 3)))


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

    if sys.argv[1] == "all":
        run_all(exes, sys.argv[2:])
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
