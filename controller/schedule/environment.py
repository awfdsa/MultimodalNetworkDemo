from io import BufferedReader
from typing_extensions import TypeAlias,Iterable,Callable,TypeVar,Union,Sequence,NamedTuple,cast,Tuple
from itertools import permutations,product

from iperf_handle import NetworkState,IperfHandle
from bmv2_handle import MultipathState,download_multipath_state

#给外部返回的总的state
class AllState(NamedTuple):
    out_of_order:float
    bandwidth:float

    path1_num:int
    path2_num:int
    path3_num:int

    path1_order:int
    path2_order:int
    path3_order:int

    @staticmethod
    def from_net_and_mp_state(net_states:Sequence[NetworkState],mp_state:MultipathState):
        return AllState(
            get_avg_bandwidth(net_states),
            get_percentage_out_of_order(net_states),
            *mp_state.num,
            1,2,3,
        )

Mbps:TypeAlias = float
NumOfPackets:TypeAlias = int

delta_actions = ((0,0,0),*permutations((1,0,-1),3))
order_actions = permutations((1,2,3),3)

class Action(NamedTuple):
    path1_delta:int
    path2_delta:int
    path3_delta:int
    path1_order:int
    path2_order:int
    path3_order:int

actions=tuple( Action(*i,*j) for i,j in product(delta_actions,order_actions) )

T=TypeVar('T')
U=TypeVar('U',float,int)
def sum_skip_none(container:Iterable[T],value_getter:Callable[[T],Union[None,U]]) -> U:
    sumed = 0
    for i in container:
        value = value_getter(i)
        if value is not None:
            sumed+=value
    return sumed

def get_avg_bandwidth(networkStates:Sequence[NetworkState]) -> float:
    return sum_skip_none(networkStates,lambda i:i.bandwidth)/len(networkStates)

def get_percentage_out_of_order(networkStates:Sequence[NetworkState])->float:
    return sum_skip_none(networkStates,lambda i:i.lost)/sum_skip_none(networkStates,lambda i:i.total)

class Environment:
    stdout:BufferedReader
    iperf_handle:IperfHandle
    max_total_bw:float
    mp_state:MultipathState

    def __init__(self, max_total_bw:float) -> None:
        self.iperf_handle = IperfHandle()
        self.max_total_bw=max_total_bw
    
    def reset(self,wait_clients=True) -> AllState:
        if wait_clients:
            input("请启动或重启iperf客户端，并按下回车以继续程序")
        self.mp_state=MultipathState(
            (5,5,5),
            (1,2,3),
        )
        state = AllState.from_net_and_mp_state(self.iperf_handle.get_network_state(),self.mp_state)
        self._reseted=True
        return state

    def step(self,action_index:int):
        if not getattr(self,'_reseted',False):
            raise Exception("必须先执行reset")
        
        action=actions[action_index]
        self.mp_state=MultipathState(
            num=cast(Tuple[int,int,int],tuple(i+j for i,j in zip(self.mp_state.num,action[:3]))),
            order=action[3:]
        )

        download_multipath_state(self.mp_state)
        net_states=self.iperf_handle.monitor_for_seconds(1.1)

        reward = 0.3 * get_avg_bandwidth(net_states)/self.max_total_bw - 0.7 * get_percentage_out_of_order(net_states)
        reward *=100

        return AllState.from_net_and_mp_state(net_states,self.mp_state),reward
    
    def close(self) -> None:
        self.iperf_handle.close()

if __name__ == "__main__":
    env=Environment(max_total_bw=10)
    env.reset()
    try:
        while True:
            env.step(int(input()))
            print(env.mp_state)
    except KeyboardInterrupt:
        env.close()