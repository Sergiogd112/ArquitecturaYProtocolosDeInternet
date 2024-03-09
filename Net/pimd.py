class PIMD:
    def __init__(self, groups: dict = None):
        if groups is None:
            groups = {}
        self.groups: dict = groups

    def load_pimd_config(self, config: str):
        pass
