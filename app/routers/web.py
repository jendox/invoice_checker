from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.statement_file import StatementFile
from app.models.transaction import Transaction
from app.schemas.transaction import (
    ClassificationUpdate,
    DeleteTransactionsRequest,
    ReclassifyRequest,
    TransactionFilters,
)
from app.services.bank_service import BankService
from app.services.category_service import CategoryService
from app.services.company_service import CompanyService
from app.services.invoice_owner_service import InvoiceOwnerService
from app.services.parser.bank_presets import (
    STATEMENT_CURRENCIES,
    detect_bank_from_filename,
    detect_currency_from_filename,
    normalize_bank_key,
)
from app.services.rule_service import RuleService
from app.services.transaction_service import TransactionService
from app.utils.categories import category_style_map
from app.utils.filter_labels import STATUS_FILTER_OPTIONS, build_bank_filter_options, build_key_label_options
from app.utils.query import parse_optional_date

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def default_statement_month() -> str:
    return date.today().strftime("%Y-%m")
tx_service = TransactionService()
rule_service = RuleService()
category_service = CategoryService()
bank_service = BankService()
company_service = CompanyService()
invoice_owner_service = InvoiceOwnerService()

STATUSES = [option.key for option in STATUS_FILTER_OPTIONS]
PATTERN_TYPES = ["contains", "regex", "exact"]
INVOICE_CHOICES = {"true": True, "false": False, "unknown": None}
MIN_SEARCH_LENGTH = 2


def _filters_from_bulk_form(
    bank_name: str = "",
    statement_month: str = "",
    date_from: str = "",
    date_to: str = "",
    requires_invoice: str = "",
    status: str = "",
    category: str = "",
    company_name: str = "",
    search: str = "",
) -> TransactionFilters:
    req_invoice_bool = None
    if requires_invoice == "true":
        req_invoice_bool = True
    elif requires_invoice == "false":
        req_invoice_bool = False

    return TransactionFilters(
        bank_name=bank_name or None,
        statement_month=statement_month or None,
        date_from=parse_optional_date(date_from or None),
        date_to=parse_optional_date(date_to or None),
        requires_invoice=req_invoice_bool,
        status=status or None,
        category=category or None,
        company_name=company_name or None,
        search=search.strip() if search and len(search.strip()) >= MIN_SEARCH_LENGTH else None,
    )


def _scope_from_filters(filters: TransactionFilters) -> DeleteTransactionsRequest:
    return DeleteTransactionsRequest(
        bank_name=filters.bank_name,
        statement_month=filters.statement_month,
        date_from=filters.date_from,
        date_to=filters.date_to,
        requires_invoice=filters.requires_invoice,
        status=filters.status,
        category=filters.category,
        company_name=filters.company_name,
        search=filters.search,
    )


def _transactions_query(filters: TransactionFilters, page: int | None = None, **extra: str | int) -> str:
    params: dict[str, str | int] = {}
    for key in ("bank_name", "statement_month", "status", "category", "company_name", "search"):
        value = getattr(filters, key)
        if value:
            params[key] = value
    if filters.date_from:
        params["date_from"] = filters.date_from.isoformat()
    if filters.date_to:
        params["date_to"] = filters.date_to.isoformat()
    if filters.requires_invoice is not None:
        params["requires_invoice"] = str(filters.requires_invoice).lower()
    if page is not None:
        params["page"] = page
    params.update(extra)
    return urlencode(params)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(Transaction.id)))).scalar_one()
    needs_review = (
        await db.execute(
            select(func.count(Transaction.id)).where(Transaction.status == "needs_review"),
        )
    ).scalar_one()
    invoice_required = (
        await db.execute(
            select(func.count(Transaction.id)).where(Transaction.requires_invoice.is_(True)),
        )
    ).scalar_one()
    statements = (
        await db.execute(select(func.count(StatementFile.id)))
    ).scalar_one()

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "stats": {
                "total": total,
                "needs_review": needs_review,
                "invoice_required": invoice_required,
                "statements": statements,
            },
        },
    )


@router.get("/upload", response_class=HTMLResponse)
async def upload_page():
    return RedirectResponse(url="/transactions?open_upload=1", status_code=303)


async def _upload_form_context(
    db: AsyncSession,
    *,
    bank_name: str = "",
    company_name: str = "",
    statement_month: str | None = None,
    statement_currency: str | None = None,
) -> dict:
    return {
        "upload_banks": await bank_service.list_banks(db, active_only=True),
        "upload_companies": await company_service.list_companies(db),
        "default_statement_month": default_statement_month(),
        "default_statement_currency": statement_currency or "GBP",
        "statement_currencies": STATEMENT_CURRENCIES,
        "upload_bank_name": normalize_bank_key(bank_name) if bank_name else "",
        "upload_company_name": company_name,
        "upload_statement_month": statement_month,
        "upload_statement_currency": statement_currency,
    }


@router.post("/upload")
async def upload_form(
    request: Request,
    file: UploadFile,
    bank_name: str = Form(""),
    statement_month: str = Form(default_factory=default_statement_month),
    statement_currency: str = Form("GBP"),
    company_name: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    filename = file.filename or "upload.xlsx"
    detected = detect_bank_from_filename(filename)
    effective_bank = normalize_bank_key(bank_name or detected)
    effective_currency = statement_currency.strip().upper()[:3] or detect_currency_from_filename(filename)

    try:
        result = await tx_service.upload_statement(
            db,
            content,
            filename,
            effective_bank,
            statement_month,
            company_name or None,
            effective_currency,
        )
        return RedirectResponse(
            url=f"/transactions?imported={result.imported_count}&review={result.needs_review_count}",
            status_code=303,
        )
    except ValueError as e:
        params = urlencode(
            {
                "open_upload": "1",
                "upload_error": str(e),
                "upload_bank_name": effective_bank,
                "upload_company_name": company_name,
                "upload_statement_month": statement_month,
                "upload_statement_currency": effective_currency,
            },
        )
        return RedirectResponse(url=f"/transactions?{params}", status_code=303)


@router.get("/transactions", response_class=HTMLResponse)
async def transactions_page(
    request: Request,
    bank_name: str | None = None,
    statement_month: str | None = None,
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    requires_invoice: str | None = None,
    status: str | None = None,
    category: str | None = None,
    company_name: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    imported: int | None = None,
    review: int | None = None,
    reclassified: int | None = None,
    reclassify_skipped: int | None = None,
    deleted: int | None = None,
    open_upload: str | None = None,
    upload_error: str | None = None,
    upload_bank_name: str | None = None,
    upload_company_name: str | None = None,
    upload_statement_month: str | None = None,
    upload_statement_currency: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    req_invoice_bool = None
    if requires_invoice == "true":
        req_invoice_bool = True
    elif requires_invoice == "false":
        req_invoice_bool = False

    filters = TransactionFilters(
        bank_name=bank_name or None,
        statement_month=statement_month or None,
        date_from=parse_optional_date(date_from),
        date_to=parse_optional_date(date_to),
        requires_invoice=req_invoice_bool,
        status=status or None,
        category=category or None,
        company_name=company_name or None,
        search=search.strip() if search and len(search.strip()) >= MIN_SEARCH_LENGTH else None,
        page=page,
        page_size=30,
    )
    items, total = await tx_service.list_transactions(db, filters)

    companies = (
        await db.execute(
            select(StatementFile.company_name)
            .where(StatementFile.company_name.isnot(None))
            .distinct(),
        )
    ).scalars().all()
    banks = (await db.execute(select(Transaction.bank_name).distinct())).scalars().all()
    all_companies = await company_service.list_companies(db, active_only=False)
    all_banks = await bank_service.list_banks(db, active_only=False)
    company_filter_options = build_key_label_options(
        list(companies),
        all_companies,
        filters.company_name,
    )
    bank_filter_options = build_bank_filter_options(
        list(banks),
        all_banks,
        filters.bank_name,
    )
    all_categories = await category_service.list_categories(db)
    categories = [cat for cat in all_categories if cat.is_active]
    category_styles = category_style_map(all_categories)
    invoice_owners = await invoice_owner_service.list_owners(db, active_only=True)
    upload_context = await _upload_form_context(
        db,
        bank_name=upload_bank_name or "",
        company_name=upload_company_name or "",
        statement_month=upload_statement_month,
        statement_currency=upload_statement_currency,
    )

    return templates.TemplateResponse(
        request,
        "transactions.html",
        {
            "transactions": items,
            "total": total,
            "page": page,
            "pages": tx_service.paginate(total, page, 30),
            "filters": filters,
            "categories": categories,
            "category_styles": category_styles,
            "invoice_owners": invoice_owners,
            "statuses": STATUSES,
            "status_options": STATUS_FILTER_OPTIONS,
            "company_filter_options": company_filter_options,
            "bank_filter_options": bank_filter_options,
            "imported": imported,
            "review": review,
            "reclassified": reclassified,
            "reclassify_skipped": reclassify_skipped,
            "deleted": deleted,
            "open_upload": open_upload == "1",
            "upload_error": upload_error,
            "pagination_query": _transactions_query,
            **upload_context,
        },
    )


@router.post("/transactions/{transaction_id}/edit")
async def edit_transaction(
    transaction_id: int,
    category: str = Form(...),
    requires_invoice: str = Form("unknown"),
    invoice_provider: str = Form(""),
    invoice_owner: str = Form(""),
    status: str = Form("confirmed"),
    comment: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    req_map = {"true": True, "false": False, "unknown": None}
    update = ClassificationUpdate(
        category=category,
        requires_invoice=req_map.get(requires_invoice),
        invoice_provider=invoice_provider or None,
        invoice_owner=invoice_owner.strip() or None,
        status=status,
        comment=comment or None,
    )
    await tx_service.update_classification(db, transaction_id, update)
    return RedirectResponse(url="/transactions", status_code=303)


@router.post("/transactions/reclassify")
async def reclassify_transactions_form(
    skip_memory: str = Form("true"),
    bank_name: str = Form(""),
    statement_month: str = Form(""),
    date_from: str = Form(""),
    date_to: str = Form(""),
    requires_invoice: str = Form(""),
    status: str = Form(""),
    category: str = Form(""),
    company_name: str = Form(""),
    search: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    filters = _filters_from_bulk_form(
        bank_name=bank_name,
        statement_month=statement_month,
        date_from=date_from,
        date_to=date_to,
        requires_invoice=requires_invoice,
        status=status,
        category=category,
        company_name=company_name,
        search=search,
    )
    scope = _scope_from_filters(filters)
    updated, skipped = await tx_service.reclassify_transactions(
        db,
        ReclassifyRequest(skip_memory=skip_memory == "true", **scope.model_dump()),
    )
    params = _transactions_query(filters)
    extra = urlencode({"reclassified": updated, "reclassify_skipped": skipped})
    query = f"{params}&{extra}" if params else extra
    return RedirectResponse(url=f"/transactions?{query}", status_code=303)


@router.post("/transactions/delete")
async def delete_transactions_form(
    bank_name: str = Form(""),
    statement_month: str = Form(""),
    date_from: str = Form(""),
    date_to: str = Form(""),
    requires_invoice: str = Form(""),
    status: str = Form(""),
    category: str = Form(""),
    company_name: str = Form(""),
    search: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    filters = _filters_from_bulk_form(
        bank_name=bank_name,
        statement_month=statement_month,
        date_from=date_from,
        date_to=date_to,
        requires_invoice=requires_invoice,
        status=status,
        category=category,
        company_name=company_name,
        search=search,
    )
    deleted = await tx_service.delete_transactions(db, _scope_from_filters(filters))
    return RedirectResponse(url=f"/transactions?deleted={deleted}", status_code=303)


@router.get("/rules", response_class=HTMLResponse)
async def rules_page(request: Request, db: AsyncSession = Depends(get_db)):
    rules = await rule_service.list_rules(db)
    all_categories = await category_service.list_categories(db)
    categories = [cat for cat in all_categories if cat.is_active]
    category_styles = category_style_map(all_categories)
    invoice_owners = await invoice_owner_service.list_owners(db, active_only=True)
    return templates.TemplateResponse(
        request,
        "rules.html",
        {
            "rules": rules,
            "categories": categories,
            "category_styles": category_styles,
            "invoice_owners": invoice_owners,
            "pattern_types": PATTERN_TYPES,
        },
    )


@router.post("/rules/create")
async def create_rule_form(
    name: str = Form(...),
    pattern: str = Form(...),
    pattern_type: str = Form("contains"),
    category: str = Form(...),
    requires_invoice: str = Form("unknown"),
    invoice_provider: str = Form(""),
    invoice_owner: str = Form(""),
    priority: int = Form(100),
    confidence: float = Form(0.8),
    is_active: str = Form("true"),
    db: AsyncSession = Depends(get_db),
):
    from decimal import Decimal

    from app.schemas.rule import RuleCreate

    await rule_service.create_rule(
        db,
        RuleCreate(
            name=name,
            pattern=pattern,
            pattern_type=pattern_type,
            category=category,
            requires_invoice=INVOICE_CHOICES.get(requires_invoice),
            invoice_provider=invoice_provider or None,
            invoice_owner=invoice_owner.strip() or None,
            priority=priority,
            confidence=Decimal(str(confidence)),
            is_active=is_active == "true",
        ),
    )
    return RedirectResponse(url="/rules", status_code=303)


@router.post("/rules/{rule_id}/edit")
async def edit_rule_form(
    rule_id: int,
    name: str = Form(...),
    pattern: str = Form(...),
    pattern_type: str = Form("contains"),
    category: str = Form(...),
    requires_invoice: str = Form("unknown"),
    invoice_provider: str = Form(""),
    invoice_owner: str = Form(""),
    priority: int = Form(100),
    confidence: float = Form(0.8),
    is_active: str = Form("true"),
    db: AsyncSession = Depends(get_db),
):
    from decimal import Decimal

    from app.schemas.rule import RuleUpdate

    try:
        await rule_service.update_rule(
            db,
            rule_id,
            RuleUpdate(
                name=name,
                pattern=pattern,
                pattern_type=pattern_type,
                category=category,
                requires_invoice=INVOICE_CHOICES.get(requires_invoice),
                invoice_provider=invoice_provider or None,
                invoice_owner=invoice_owner.strip() or None,
                priority=priority,
                confidence=Decimal(str(confidence)),
                is_active=is_active == "true",
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedirectResponse(url="/rules", status_code=303)


@router.post("/rules/{rule_id}/delete")
async def delete_rule_form(rule_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await rule_service.delete_rule(db, rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedirectResponse(url="/rules", status_code=303)
