import pytest
from recongraph.plugins.sandbox import SandboxedProvider, SandboxedProviderV2, PluginCrashError
from recongraph.plugins.provider import EvidenceProvider, EvidenceContribution
from recongraph.plugins.provider_v2 import EvidenceProviderV2, EvidencePipeline, EvidenceContributionV2

class CrashingProviderV1(EvidenceProvider):
    def get_name(self) -> str:
        return "crashing_v1"
        
    def get_blockers(self):
        raise ValueError("Crash in get_blockers")
        
    def evaluate(self, purchases, gsts):
        raise ValueError("Crash in evaluate")

class CrashingPipeline(EvidencePipeline):
    def extract(self, purchases, gsts):
        raise ValueError("Crash in extract")
    def interpret(self, extraction):
        raise ValueError("Crash in interpret")
    def contribute(self, interpretation):
        raise ValueError("Crash in contribute")

class CrashingProviderV2(EvidenceProviderV2):
    def get_name(self) -> str:
        return "crashing_v2"
        
    def get_blockers(self):
        return []
        
    def get_pipeline(self):
        return CrashingPipeline()

def test_sandbox_v1_isolation():
    provider = CrashingProviderV1()
    sandboxed = SandboxedProvider(provider)
    
    assert sandboxed.get_name() == "crashing_v1"
    
    # get_blockers should not crash, return empty
    blockers = sandboxed.get_blockers()
    assert blockers == []
    
    # evaluate should not crash, return fallback contribution
    contrib = sandboxed.evaluate([], [])
    assert contrib.score == 0.0
    assert "PLUGIN_CRASH" in contrib.violations
    assert "Crash in evaluate" in contrib.metadata["crash_reason"]

def test_sandbox_v2_isolation():
    provider = CrashingProviderV2()
    sandboxed = SandboxedProviderV2(provider)
    
    pipeline = sandboxed.get_pipeline()
    
    with pytest.raises(PluginCrashError) as exc:
        pipeline.extract([], [])
    assert "Crash in extract" in str(exc.value)
    
    with pytest.raises(PluginCrashError):
        pipeline.interpret("foo")
        
    with pytest.raises(PluginCrashError):
        pipeline.contribute("foo")
