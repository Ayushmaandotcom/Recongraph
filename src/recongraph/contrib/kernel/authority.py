from dataclasses import dataclass


@dataclass(frozen=True, slots=True, order=True)
class AuthorityBasisId:
    value: str


@dataclass(frozen=True, slots=True)
class AuthorityDescriptor:
    """
    Explicitly assigned by the assertion-producing provider. 
    Describes the epistemic basis on which an assertion asks fusion to interpret its evidentiary status.
    K6 performs no authority inheritance or ancestry-based inference.
    """
    basis: AuthorityBasisId
