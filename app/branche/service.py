from fastapi import HTTPException
from app.branche import schemas
from app.database import execute, fetch_all, fetch_one


def get_branch(db, branch_id: int):
    branch = fetch_one(
        db,
        """
        SELECT id, name, address, phone, is_active, created_at
        FROM branches
        WHERE id = %s AND deleted_at IS NULL
        """,
        (branch_id,),
    )
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch


def get_branches(db, skip: int = 0, limit: int = 100):
    return fetch_all(
        db,
        """
        SELECT id, name, address, phone, is_active, created_at
        FROM branches
        WHERE deleted_at IS NULL
        ORDER BY id ASC
        OFFSET %s LIMIT %s
        """,
        (skip, limit),
    )


def create_branch(db, branch_data: schemas.BranchCreate):
    return execute(
        db,
        """
        INSERT INTO branches (name, address, phone, is_active)
        VALUES (%s, %s, %s, %s)
        RETURNING id, name, address, phone, is_active, created_at
        """,
        (
            branch_data.name,
            branch_data.address,
            branch_data.phone,
            branch_data.is_active,
        ),
        returning=True,
    )


def update_branch(db, branch_id: int, branch_data: schemas.BranchUpdate):
    existing = get_branch(db, branch_id)

    payload = branch_data.model_dump(exclude_unset=True)
    if not payload:
        return existing

    return execute(
        db,
        """
        UPDATE branches
        SET
            name = COALESCE(%s, name),
            address = COALESCE(%s, address),
            phone = COALESCE(%s, phone),
            is_active = COALESCE(%s, is_active)
        WHERE id = %s AND deleted_at IS NULL
        RETURNING id, name, address, phone, is_active, created_at
        """,
        (
            payload.get("name"),
            payload.get("address"),
            payload.get("phone"),
            payload.get("is_active"),
            branch_id,
        ),
        returning=True,
    )


def delete_branch(db, branch_id: int):
    get_branch(db, branch_id)
    return execute(
        db,
        """
        UPDATE branches
        SET deleted_at = NOW()
        WHERE id = %s AND deleted_at IS NULL
        RETURNING id, name, address, phone, is_active, created_at
        """,
        (branch_id,),
        returning=True,
    )