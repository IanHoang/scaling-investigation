from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class AveragedThroughput:
    min: float
    min_rsd: float
    mean: float
    mean_rsd: float
    median: float
    median_rsd: float
    units: str

@dataclass
class AveragedServiceTime:
    _50_0: float = field(metadata={'data_key': '50_0'})
    _50_0_rsd: float = field(metadata={'data_key': '50_0_rsd'})
    _90_0: float = field(metadata={'data_key': '90_0'})
    _90_0_rsd: float = field(metadata={'data_key': '90_0_rsd'})
    _99_0: float = field(metadata={'data_key': '99_0'})
    _99_0_rsd: float = field(metadata={'data_key': '99_0_rsd'})
    _99_9: float = field(metadata={'data_key': '99_9'})
    _99_9_rsd: float = field(metadata={'data_key': '99_9_rsd'})
    _99_99: float = field(metadata={'data_key': '99_99'})
    _99_99_rsd: float = field(metadata={'data_key': '99_99_rsd'})
    _100_0: float = field(metadata={'data_key': '100_0'})
    _100_0_rsd: float = field(metadata={'data_key': '100_0_rsd'})
    units: str

@dataclass
class AveragedLatency:
    _50_0: float = field(metadata={'data_key': '50_0'})
    _50_0_rsd: float = field(metadata={'data_key': '50_0_rsd'})
    _90_0: float = field(metadata={'data_key': '90_0'})
    _90_0_rsd: float = field(metadata={'data_key': '90_0_rsd'})
    _99_0: float = field(metadata={'data_key': '99_0'})
    _99_0_rsd: float = field(metadata={'data_key': '99_0_rsd'})
    _99_9: float = field(metadata={'data_key': '99_9'})
    _99_9_rsd: float = field(metadata={'data_key': '99_9_rsd'})
    _99_99: float = field(metadata={'data_key': '99_99'})
    _99_99_rsd: float = field(metadata={'data_key': '99_99_rsd'})
    _100_0: float = field(metadata={'data_key': '100_0'})
    _100_0_rsd: float = field(metadata={'data_key': '100_0_rsd'})
    units: str

@dataclass
class TestResult:
    test_pattern: List[str]
    averaged_throughput: AveragedThroughput
    averaged_service_time: AveragedServiceTime
    averaged_latency: AveragedLatency

    @classmethod
    def from_dict(cls, data: Dict):
        averaged_throughput = AveragedThroughput(**data['averaged-throughput'])
        averaged_service_time = AveragedServiceTime(**{k.replace('_', ''): v for k, v in data['averaged-service-time'].items()})
        averaged_latency = AveragedLatency(**{k.replace('_', ''): v for k, v in data['averaged-latency'].items()})
        return cls(
            test_pattern=data['test-pattern'],
            averaged_throughput=averaged_throughput,
            averaged_service_time=averaged_service_time,
            averaged_latency=averaged_latency
        )
