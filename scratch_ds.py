from recongraph.graph.dempster_shafer import MassFunction
from recongraph.contrib.kernel.assertions import AssertionPolarity

m_initial = MassFunction(match=0.0, no_match=0.0, uncertainty=1.0)
m1 = MassFunction.from_assertion(AssertionPolarity.SUPPORT, 1.0)
m_fused = m_initial.combine(m1)
print(f"Fused 1: {m_fused}")
m2 = MassFunction.from_assertion(AssertionPolarity.SUPPORT, 1.0)
m_fused = m_fused.combine(m2)
print(f"Fused 2: {m_fused}")

# What if magnitudes are 0.9?
m1 = MassFunction.from_assertion(AssertionPolarity.SUPPORT, 0.9)
m2 = MassFunction.from_assertion(AssertionPolarity.SUPPORT, 0.9)
m_initial = MassFunction(match=0.0, no_match=0.0, uncertainty=1.0)
m_fused = m_initial.combine(m1).combine(m2)
print(f"Fused 0.9: {m_fused}")
