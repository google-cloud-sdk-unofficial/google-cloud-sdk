
transport inheritance structure
_______________________________

`SemanticGovernancePolicyEngineServiceTransport` is the ABC for all transports.
- public child `SemanticGovernancePolicyEngineServiceGrpcTransport` for sync gRPC transport (defined in `grpc.py`).
- public child `SemanticGovernancePolicyEngineServiceGrpcAsyncIOTransport` for async gRPC transport (defined in `grpc_asyncio.py`).
- private child `_BaseSemanticGovernancePolicyEngineServiceRestTransport` for base REST transport with inner classes `_BaseMETHOD` (defined in `rest_base.py`).
- public child `SemanticGovernancePolicyEngineServiceRestTransport` for sync REST transport with inner classes `METHOD` derived from the parent's corresponding `_BaseMETHOD` classes (defined in `rest.py`).
