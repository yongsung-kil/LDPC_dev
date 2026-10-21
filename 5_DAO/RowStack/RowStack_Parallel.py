"""병렬 통신 추상 (설계 문서 4.5절). 흐름 모듈은 이 API만 쓰므로 rank 1개 검사는 SerialParallel로 돈다."""


class SerialParallel:
    """rank 0, size 1. 통신 없이 자기 값을 돌려준다 (검사용)."""

    def __init__(self):
        self.rank = 0
        self.size = 1

    def gather_to_root(self, obj):
        """root는 모든 rank의 값 목록(rank 순), 다른 rank는 None."""
        return [obj]

    def bcast_from_root(self, obj):
        """root의 값을 모든 rank에게."""
        return obj

    def barrier(self):
        pass


class MpiParallel(SerialParallel):
    """mpi4py communicator 위의 구현."""

    def __init__(self, comm):
        super().__init__()
        self.comm = comm
        self.rank = comm.Get_rank()
        self.size = comm.Get_size()

    def gather_to_root(self, obj):
        return self.comm.gather(obj, root=0)

    def bcast_from_root(self, obj):
        return self.comm.bcast(obj, root=0)

    def barrier(self):
        self.comm.Barrier()


def round_robin_share(num_items: int, rank: int, size: int) -> list:
    """rank가 맡는 index 목록: rank, rank + size, rank + 2 size, ..."""
    return list(range(rank, num_items, size))
