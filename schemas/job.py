from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Job:
    ran_at:str = datetime.now().isoformat()
    created_at:str = datetime.now().isoformat()
    manual: bool = False
    triggered_by: str = "automatic worker"
    duplicates: int = 0
    ads_failed_to_create: int = 0
    total_ads_created: int = 0
    completed: bool = False

    def to_dict(self):
        return asdict(self)

@dataclass
class JobResponse(Job):
    id: int | None = None


def create_default_job():
    return Job()

if __name__ == "__main__":
    job = Job()
    print(job.to_dict())
