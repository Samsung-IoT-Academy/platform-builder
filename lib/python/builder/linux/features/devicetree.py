from abc import ABCMeta


class DeviceTreeMixin(metaclass=ABCMeta):
    def __init__(self):
        super(self.__class__, self).__init__()
        self._make_targets_opts["dtbs"] = self.__class__.__base_make_vars

    def make_dtbs(self):
            self.make_caller("dtbs", cwd=self.kernel_src_path)
