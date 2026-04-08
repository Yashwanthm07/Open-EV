"""Email Triage OpenEnv — Real-world email management environment."""
from .environment import EmailTriageEnvironment
from .models import EmailTriageAction, EmailTriageObservation, EmailTriageReward, EmailTriageState

__all__ = [
    "EmailTriageEnvironment",
    "EmailTriageAction",
    "EmailTriageObservation",
    "EmailTriageReward",
    "EmailTriageState",
]
__version__ = "1.0.0"
