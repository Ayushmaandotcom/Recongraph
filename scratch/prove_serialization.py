import json
from recongraph.serialization import ReconEncoder
from tests.test_challenge_referee import _run

result, _, _ = _run()
j = json.dumps(result, cls=ReconEncoder, indent=2)
for line in j.splitlines()[:20]:
    print(line)
