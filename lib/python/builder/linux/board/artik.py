import os
from abc import ABCMeta,

from ...utils import num_cores


class Artik(object, metaclass=ABCMeta):
    def __init__(self, *args,
                 arch="arm",
                 cross_compile="arm-linux-gnueabihf-", cc_prefix="",
                 kernel_src, build_path=None, install_mod_path=""):
        self.arch = arch
        self.cross_compile = cross_compile
        self.cross_compile_prefix = cc_prefix

        self.kernel_src_path = kernel_src
        self.build_path = build_path
        self.install_mod_path = install_mod_path

        self._kfiles_path = {
            "patch":  os.path.join(os.getcwd(), "kpatch"),
            "config": os.path.join(os.getcwd(), "kconfig"),
        }

        self._make_targets = [
            "Image",
            "prepare_modules",
            "modules",
            "modules_install",
        ]
        self._make_targets_with_jobs = {
            "Image":    True,
            "modules":  True,
        }

        base_make_vars = ("O", "ARCH", "CROSS_COMPILE")
        self._make_targets_opts = {
            "config":           ("O", "ARCH"),
            "Image":            base_make_vars,
            "prepare_modules":  base_make_vars,
            "modules":          base_make_vars,
            "modules_install":  (*base_make_vars, "INSTALL_MOD_PATH",
                                 "INSTALL_MOD_STRIP"),
        }

        self._make_opts = {
            "ARCH":                 self.arch,
            "CROSS_COMPILE":        os.path.join(self.cross_compile_prefix,
                                                 self.cross_compile),
            "INSTALL_MOD_PATH":     self.install_mod_path,
            "INSTALL_MOD_STRIP":    1
        }
        if self.build_path is not None:
            self._make_opts["O"] = self.build_path

    def _build_opts(self, target):
        def __filter_opts(opt):
            if opt in self._make_opts:
                return True
            else:
                return False

        opts = map(lambda opt: opt + "=" + self._make_opts[opt],
                   filter(__filter_opts,
                          self._make_targets_opts[target]))
        if target != "config":
            opts.append(target)
        if target in self._make_targets_with_jobs:
            opts.append("-j{n}".format(n=num_cores()))

    def make_caller()
