import os
import subprocess
from abc import ABCMeta, abstractmethod

from ...utils import num_cores
from ..features.devicetree import DeviceTreeMixin


class Artik(object, metaclass=ABCMeta):
    __base_make_vars = ("O", "ARCH", "CROSS_COMPILE")

    def __init__(self, *args,
                 arch="arm",
                 cross_compile="arm-linux-gnueabihf-", cc_prefix="",
                 kernel_src, build_path=None, install_mod_path="", **kwargs):
        super().__init__(**kwargs)

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

        self._make_targets_opts = {
            "config":           ("O", "ARCH"),
            "Image":            self.__class__.__base_make_vars,
            "prepare_modules":  self.__class__.__base_make_vars,
            "modules":          self.__class__.__base_make_vars,
            "modules_install":  (*self.__class__.__base_make_vars,
                                 "INSTALL_MOD_PATH", "INSTALL_MOD_STRIP"),
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
        else:
            opts.append(self.config_name)
        if target in self._make_targets_with_jobs:
            opts.append("-j{n}".format(n=num_cores()))

    def make_caller(self, target, *args, cwd=os.getcwd()):
        cmd = "make"
        if callable(args[0]):
            fn = args[0]
            fn_args = args[1:]
            try:
                fn(fn_args)
            except Exception as e:
                print("Failed to call function!")

        opts = self._build_opts(target)
        opts.insert(0, cmd)
        try:
            subprocess.check_output(opts, cwd=cwd)
        except subprocess.CalledProcessError as os_error:
            print("Failed `make {tgt}`! Return code: {ret}".format(
                tgt=target, ret=os_error.returncode))
            print(os_error.stdout)
            print(os_error.stderr)
            exit()

    def make_vmlinux(self):
        self.make_caller("Image", cwd=self.kernel_src_path)

    def make_prepare_modules(self):
        self.make_caller("prepare_modules", cwd=self.kernel_src_path)

    def make_modules(self):
        self.make_caller("modules", cwd=self.kernel_src_path)

    def make_modules_install(self):

        def create_modules_path(self):
            os.makedirs(self.install_mod_path, mode=0o775, exist_ok=True)

        self.make_caller("modules_install", create_modules_path,
                         cwd=self.kernel_src_path)

    def make_mrproper(self):
        self.make_caller("mrproper")


class Artik710(DeviceTreeMixin, Artik):
    __make_ext4fs_def_opts = {
        "block_size":   4096,
        "label":        "modules",
        "size":         "{sz:d}M".format(sz=32)
    }

    def __init__(self, *args, make_ext4fs_args={}, kernel_src, **kwargs):
        super().__init__(arch="arm64",
                         cross_compile="aarch64-linux-gnu-",
                         kernel_src=kernel_src,
                         **kwargs)
        if "output_file_path" not in make_ext4fs_args:
            raise Exception

        mod_path_postfix = os.path.join("lib", "modules")

        self._make_ext4fs_opts = self.__class__.__make_ext4fs_def_opts.copy()
        self._make_ext4fs_opts.update(make_ext4fs_args)
        self._make_ext4fs_opts["source_dir_path"] = os.path.join(
            self.install_mod_path, mod_path_postfix)

        if "config_name" not in kwargs:
            self.config_name = "artik710_raptor_defconfig"
        else:
            self.config_name = kwargs["config_name"]

        self.prepare_repo()
        self.configure_kernel()
        self.patch_kernel()

    def __delete__(self):
        self.revert_patches()
        self.make_mrproper()

    def _get_base_make_vars(self):
        from pprint import pprint as pp
        pp(self.__class__.__dict__)
        return self.__class__.__base_make_vars

    def _build_make_ext4fs_opts(self):
        translation_table = {
            "block_size":   "-b",
            "label":        "-L",
            "size":         "-l",
        }
        opts = []
        for key in translation_table.keys():
            opts.append(translation_table[key])
            opts.append(self._make_ext4fs_opts[key])
        opts.append(self._make_ext4fs_opts["output_file_path"])
        opts.append(self._make_ext4fs_opts["source_dir_path"])
        return opts

    def prepare_repo(self):
        opts = ["git", "checkout", "origin/tizen_3.0"]
        try:
            subprocess.check_output(opts, cwd=self.kernel_src_path)
        except subprocess.CalledProcessError as os_error:
            print("Failed checkout {brch} branch! Return code: {ret}".format(
                brch=opts[2], ret=os_error.returncode))
            print(os_error.stdout)
            print(os_error.stderr)
            exit()

    def configure_kernel(self):
        self.make_config
        opts = [os.join(os.getcwd, "bin", "utils", "config-merger",
                        "--main", os.join(self.build_path, ".config"),
                        "--merge", os.join(self._kfiles_path["config"],
                                           "board",
                                           "unwds-artik-710",
                                           "4.4.19-tizen",
                                           ".config"))]
        try:
            subprocess.check_output(opts)
        except subprocess.CalledProcessError as os_error:
            print("Failed merging configs! Return code: {ret}".format(
                ret=os_error.returncode))
            print(os_error.stdout)
            print(os_error.stderr)
            exit()

    def patch_kernel(self):
        self.patch_opts = ["git", "apply",
                           os.join(self._kfiles_path["patch"],
                                   "mali.patch")]
        opts = self.patch_opts
        try:
            subprocess.check_output(opts)
        except subprocess.CalledProcessError as os_error:
            print("Failed patch kernel! Return code: {ret}".format(
                ret=os_error.returncode))
            print(os_error.stdout)
            print(os_error.stderr)
            exit()

    def revert_patches(self):
        opts = self.patch_opts[:2] + "-R" + self.patch_opts[2:]
        try:
            subprocess.check_output(opts)
        except subprocess.CalledProcessError as os_error:
            print("Failed reverting opts! Return code: {ret}".format(
                ret=os_error.returncode))
            print(os_error.stdout)
            print(os_error.stderr)
            exit()

    def make_config(self):
        self.make_caller("config")

    def make_ext4fs_mod_part(self):
        opts = self._build_make_ext4fs_opts()
        opts.insert(0, "make_ext4fs")
