class Tool:
    def __init__(self):
        raise NotImplementedError()
    
    def run_before(self) -> None:
        pass

    def run_after(self) -> None:
        pass