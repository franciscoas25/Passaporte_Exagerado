from fastapi import Request, HTTPException, status


def verificar_admin(request: Request):
    if not request.session.get("autenticado"):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/admin/login"},
        )