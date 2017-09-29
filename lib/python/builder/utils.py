import os


def num_cores():
    """
    Detects the number of CPUs on a system. Cribbed from pp.
    """
    # Linux, Unix and MacOS:
    if hasattr(os, "sysconf"):
        # Linux & Unix
        if "SC_NPROCESSORS_ONLN" in os.sysconf_names:
            ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
            if isinstance(ncpus, int) and ncpus > 0:
                return ncpus
        # OSX:
        else:
            return int(os.popen2("sysctl -n hw.ncpu")[1].read())
        # Windows:
        if "NUMBER_OF_PROCESSORS" in os.environ:
            ncpus = int(os.environ["NUMBER_OF_PROCESSORS"])
            if ncpus > 0:
                return ncpus
            # Default
            return 1
