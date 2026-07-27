import pytest
from recongraph.contrib.kernel.authority import AuthorityBasisId, AuthorityDescriptor


def test_ea067_unknown_authority_basis_transported():
    basis = AuthorityBasisId("plugin.acme.authority.bank_confirmation")
    desc = AuthorityDescriptor(basis=basis)
    assert desc.basis.value == "plugin.acme.authority.bank_confirmation"


def test_ea068_unknown_authority_basis_not_fusion_eligible_by_implication():
    # This is a rule implemented at the Stage 8J boundary, 
    # but at the K6 level it means the descriptor merely holds the basis ID 
    # and has no 'trusted=True' flag or priority integer.
    desc = AuthorityDescriptor(basis=AuthorityBasisId("plugin.unknown"))
    assert not hasattr(desc, "priority")
    assert not hasattr(desc, "trusted")
