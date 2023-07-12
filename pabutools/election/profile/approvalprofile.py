from collections.abc import Iterable
from itertools import product
from numbers import Number

from pabutools.election.ballot import (
    Ballot,
    ApprovalBallot,
    FrozenBallot,
    FrozenApprovalBallot,
    get_random_approval_ballot,
)
from pabutools.election.profile.profile import Profile, MultiProfile
from pabutools.election.instance import Instance, Project
from pabutools.utils import powerset


class ApprovalProfile(Profile):
    """
    A profile of approval ballots. Inherits from `pabutools.instance.profile.Profile`.
    Attributes
    ----------
    """

    def __init__(
        self,
        iterable: Iterable[ApprovalBallot] = (),
        instance: Instance | None = None,
        ballot_validation: bool = True,
        ballot_type: type[Ballot] = ApprovalBallot,
        legal_min_length: int | None = None,
        legal_max_length: int | None = None,
        legal_min_cost: Number | None = None,
        legal_max_cost: Number | None = None,
    ):
        super(ApprovalProfile, self).__init__(
            iterable=iterable,
            instance=instance,
            ballot_validation=ballot_validation,
            ballot_type=ballot_type,
        )
        self.legal_min_length = legal_min_length
        self.legal_max_length = legal_max_length
        self.legal_min_cost = legal_min_cost
        self.legal_max_cost = legal_max_cost

    def as_multiprofile(self):
        return ApprovalMultiProfile(
            instance=self.instance,
            profile=self,
            ballot_validation=self.ballot_validation,
            ballot_type=FrozenApprovalBallot,
            legal_min_length=self.legal_min_length,
            legal_max_length=self.legal_max_length,
            legal_min_cost=self.legal_min_cost,
            legal_max_cost=self.legal_max_cost,
        )

    def approval_score(self, project: Project) -> int:
        """
        Returns the approval score of a project, that is, the number of voters who approved of it.
        Parameters
        ----------
            project : pabutools.instance.instance.Project
                The project.
        Returns
        -------
            int
        """
        approval_score = 0
        for ballot in self:
            if project in ballot:
                approval_score += 1
        return approval_score

    def is_trivial(self) -> bool:
        """
        Tests if the profile is trivial, meaning all projects that are approved by at least one voter have a cost
        that exceeds the budget limit.
        Returns
        -------
            bool
        """
        return all(
            project.cost > self.instance.budget_limit
            for project in self.approved_projects()
        )

    def approved_projects(self) -> set[Project]:
        """
        A set of all projects approved by at least one voter.
        Returns
        -------
            set of projects
        """
        approved_projects = set()
        for ballot in self:
            approved_projects.update(ballot)
        return approved_projects

    def is_party_list(self) -> bool:
        """
        Check whether this profile is a party-list profile.
        In a party-list profile all approval sets are either disjoint or equal.
        Returns
        -------
            bool
        """
        return all(len(b1 & b2) in (0, len(b1)) for b1 in self for b2 in self)

    @classmethod
    def _wrap_methods(cls, names):
        def wrap_method_closure(name):
            def inner(self, *args):
                result = getattr(super(cls, self), name)(*args)
                if isinstance(result, list) and not isinstance(result, cls):
                    result = cls(
                        result,
                        instance=self.instance,
                        ballot_validation=self.ballot_validation,
                        ballot_type=self.ballot_type,
                        legal_min_length=self.legal_min_length,
                        legal_max_length=self.legal_max_length,
                        legal_min_cost=self.legal_min_cost,
                        legal_max_cost=self.legal_max_cost,
                    )
                return result

            inner.fn_name = name
            setattr(cls, name, inner)

        for n in names:
            wrap_method_closure(n)


ApprovalProfile._wrap_methods(
    [
        "__add__",
        "__iadd__",
        "__imul__",
        "__mul__",
        "__reversed__",
        "__rmul__",
        "copy",
        "reverse",
    ]
)


def get_random_approval_profile(instance: Instance, num_agents: int) -> ApprovalProfile:
    """
    Generates a random approval profile in which approval ballots are such that each project is approved with
    probability 0.5.
    Parameters
    ----------
        instance : pabutools.instance.instance.PBInstance
            The instance the profile is defined with respect to.
        num_agents : int
            The length of the profile, i.e., the number of agents..
    Returns
    -------
        pabutools.instance.profile.ApprovalBallot
    """
    profile = ApprovalProfile(instance=instance)
    for i in range(num_agents):
        profile.append(
            get_random_approval_ballot(instance, name="RandomAppBallot {}".format(i))
        )
    return profile


def get_all_approval_profiles(instance: Instance, num_agents: int):
    """
    Returns a generator over all the possible profile for a given instance of a given length.
    Parameters
    ----------
        instance : pabutools.instance.instance.PBInstance
            The instance the profile is defined with respect to.
        num_agents : int
            The length of the profile, i.e., the number of agents..
    Returns
    -------
        pabutools.instance.profile.ApprovalBallot
    """
    return product(powerset(instance), repeat=num_agents)


class ApprovalMultiProfile(MultiProfile):
    def __init__(
        self,
        iterable: Iterable[FrozenApprovalBallot] = (),
        instance: Instance | None = None,
        ballot_validation: bool = True,
        ballot_type: type[FrozenBallot] = FrozenApprovalBallot,
        profile: ApprovalProfile = None,
        legal_min_length: int | None = None,
        legal_max_length: int | None = None,
        legal_min_cost: Number | None = None,
        legal_max_cost: Number | None = None,
    ):
        super(ApprovalMultiProfile, self).__init__(
            iterable=iterable,
            instance=instance,
            ballot_validation=ballot_validation,
            ballot_type=ballot_type,
        )
        if profile is not None:
            self.extend(profile)
        self.legal_min_length = legal_min_length
        self.legal_max_length = legal_max_length
        self.legal_min_cost = legal_min_cost
        self.legal_max_cost = legal_max_cost

    def approval_score(self, project: Project) -> int:
        """
        Returns the approval score of a project, that is, the number of voters who approved of it.
        Parameters
        ----------
            project : pabutools.instance.instance.Project
                The project.
        Returns
        -------
            int
        """
        approval_score = 0
        for ballot, multiplicity in self.items():
            if project in ballot:
                approval_score += multiplicity
        return approval_score

    @classmethod
    def _wrap_methods(cls, names):
        def wrap_method_closure(name):
            def inner(self, *args):
                result = getattr(super(cls, self), name)(*args)
                if isinstance(result, dict) and not isinstance(result, cls):
                    result = cls(
                        result,
                        instance=self.instance,
                        ballot_validation=self.ballot_validation,
                        ballot_type=self.ballot_type,
                        legal_min_length=self.legal_min_length,
                        legal_max_length=self.legal_max_length,
                        legal_min_cost=self.legal_min_cost,
                        legal_max_cost=self.legal_max_cost,
                    )
                return result

            inner.fn_name = name
            setattr(cls, name, inner)

        for n in names:
            wrap_method_closure(n)


ApprovalMultiProfile._wrap_methods(
    [
        "__add__",
        "__and__",
        "__iadd__",
        "__iand__",
        "__ior__",
        "__isub__",
        "__imul__",
        "__mul__",
        "__or__",
        "__ror__",
        "__sub__",
        "copy",
    ]
)