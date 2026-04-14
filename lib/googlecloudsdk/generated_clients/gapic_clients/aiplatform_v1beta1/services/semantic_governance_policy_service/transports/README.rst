
transport inheritance structure
_______________________________

`SemanticGovernancePolicyServiceTransport` is the ABC for all transports.
- public child `SemanticGovernancePolicyServiceGrpcTransport` for sync gRPC transport (defined in `grpc.py`).
- public child `SemanticGovernancePolicyServiceGrpcAsyncIOTransport` for async gRPC transport (defined in `grpc_asyncio.py`).
- private child `_BaseSemanticGovernancePolicyServiceRestTransport` for base REST transport with inner classes `_BaseMETHOD` (defined in `rest_base.py`).
- public child `SemanticGovernancePolicyServiceRestTransport` for sync REST transport with inner classes `METHOD` derived from the parent's corresponding `_BaseMETHOD` classes (defined in `rest.py`).
