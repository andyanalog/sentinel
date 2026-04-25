from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from sentinel.api.dependencies import get_container
from sentinel.container import Container
from sentinel.models.operator import Operator, OperatorPool

router = APIRouter(prefix="/v1/operators", tags=["operators"])


class CreateOperatorRequest(BaseModel):
    name: str


class CreateOperatorResponse(BaseModel):
    operator: Operator
    pool: OperatorPool


class CreditRequest(BaseModel):
    amount_usdc: float


@router.post("", response_model=CreateOperatorResponse, status_code=201)
async def create_operator(
    body: CreateOperatorRequest,
    container: Container = Depends(get_container),
) -> CreateOperatorResponse:
    op = await container.operators.create(body.name)
    # DummyPayments seeds $100 per new operator automatically; real CirclePayments
    # starts at $0 and requires an onchain deposit via the OperatorPool contract.
    balance = await container.pool.balance(op.id)
    return CreateOperatorResponse(
        operator=op, pool=OperatorPool(operator_id=op.id, balance_usdc=balance)
    )


@router.get("/{operator_id}", response_model=OperatorPool)
async def get_operator_pool(
    operator_id: str,
    container: Container = Depends(get_container),
) -> OperatorPool:
    op = await container.operators.get(operator_id)
    if op is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "operator not found")
    balance = await container.pool.balance(operator_id)
    return OperatorPool(operator_id=operator_id, balance_usdc=balance)


@router.post("/{operator_id}/credit", response_model=OperatorPool)
async def credit_pool(
    operator_id: str,
    body: CreditRequest,
    container: Container = Depends(get_container),
) -> OperatorPool:
    balance = await container.pool.credit(operator_id, body.amount_usdc)
    return OperatorPool(operator_id=operator_id, balance_usdc=balance)
