import logging
from typing import Iterable, Sequence, Any
from recongraph.plugins.provider import EvidenceProvider, EvidenceContribution
from recongraph.plugins.provider_v2 import EvidenceProviderV2, EvidencePipeline, EvidenceContributionV2
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.candidate_generation.blockers import Blocker

logger = logging.getLogger(__name__)

class SandboxedProvider(EvidenceProvider):
    """
    Wraps a V1 EvidenceProvider to isolate exceptions thrown by third-party code.
    If the plugin crashes during evaluation, it emits a safe fallback contribution.
    """
    def __init__(self, provider: EvidenceProvider):
        self.provider = provider
        
    def get_name(self) -> str:
        try:
            return self.provider.get_name()
        except Exception as e:
            logger.error(f"Plugin crash during get_name(): {e}")
            return "crashed_plugin"
            
    def get_blockers(self) -> Iterable[Blocker]:
        try:
            return self.provider.get_blockers()
        except Exception as e:
            logger.error(f"Plugin {self.get_name()} crashed during get_blockers(): {e}")
            return []
            
    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        try:
            return self.provider.evaluate(purchases, gsts)
        except Exception as e:
            name = self.get_name()
            logger.error(f"Plugin {name} crashed during evaluate(): {e}")
            return EvidenceContribution(
                provider_name=name,
                score=0.0,
                violations=frozenset(["PLUGIN_CRASH"]),
                metadata={"crash_reason": str(e)}
            )


class SandboxedPipeline(EvidencePipeline):
    """
    Wraps a V2 EvidencePipeline to isolate exceptions during the three phases.
    """
    def __init__(self, pipeline: EvidencePipeline, provider_name: str):
        self.pipeline = pipeline
        self.provider_name = provider_name
        
    def extract(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> Any:
        try:
            return self.pipeline.extract(purchases, gsts)
        except Exception as e:
            logger.error(f"Plugin {self.provider_name} crashed during extract(): {e}")
            raise PluginCrashError(f"Crashed in extract: {e}")
            
    def interpret(self, extraction: Any) -> Any:
        try:
            return self.pipeline.interpret(extraction)
        except Exception as e:
            logger.error(f"Plugin {self.provider_name} crashed during interpret(): {e}")
            raise PluginCrashError(f"Crashed in interpret: {e}")
            
    def contribute(self, interpretation: Any) -> EvidenceContributionV2:
        try:
            return self.pipeline.contribute(interpretation)
        except Exception as e:
            logger.error(f"Plugin {self.provider_name} crashed during contribute(): {e}")
            raise PluginCrashError(f"Crashed in contribute: {e}")


class PluginCrashError(Exception):
    pass


class SandboxedProviderV2(EvidenceProviderV2):
    """
    Wraps a V2 EvidenceProvider to isolate exceptions thrown by third-party code.
    """
    def __init__(self, provider: EvidenceProviderV2):
        self.provider = provider
        
    def get_name(self) -> str:
        try:
            return self.provider.get_name()
        except Exception as e:
            logger.error(f"Plugin crash during get_name(): {e}")
            return "crashed_plugin"
            
    def get_blockers(self) -> Iterable[Blocker]:
        try:
            return self.provider.get_blockers()
        except Exception as e:
            logger.error(f"Plugin {self.get_name()} crashed during get_blockers(): {e}")
            return []
            
    def get_pipeline(self) -> EvidencePipeline[Any, Any]:
        try:
            pipeline = self.provider.get_pipeline()
            return SandboxedPipeline(pipeline, self.get_name())
        except Exception as e:
            logger.error(f"Plugin {self.get_name()} crashed during get_pipeline(): {e}")
            # Return a dummy pipeline that throws on extract
            class CrashPipeline(EvidencePipeline):
                def extract(self, purchases, gsts):
                    raise PluginCrashError(str(e))
                def interpret(self, extraction):
                    raise PluginCrashError(str(e))
                def contribute(self, interpretation):
                    raise PluginCrashError(str(e))
            return CrashPipeline()
