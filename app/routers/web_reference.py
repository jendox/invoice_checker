from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.bank import BankCreate, BankUpdate
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.invoice_owner import InvoiceOwnerCreate, InvoiceOwnerUpdate
from app.schemas.vendor import VendorCreate, VendorUpdate
from app.services.bank_service import BankService
from app.services.category_service import CategoryService
from app.services.invoice_owner_service import InvoiceOwnerService
from app.services.vendor_service import VendorService
from app.utils.categories import category_style_map

router = APIRouter(tags=["web-reference"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

category_service = CategoryService()
bank_service = BankService()
invoice_owner_service = InvoiceOwnerService()
vendor_service = VendorService()

INVOICE_CHOICES = {"true": True, "false": False, "unknown": None}


def _parse_aliases(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


async def _reference_context(session: AsyncSession) -> dict:
    all_categories = await category_service.list_categories(session)
    return {
        "categories": [cat for cat in all_categories if cat.is_active],
        "category_styles": category_style_map(all_categories),
        "invoice_owners": await invoice_owner_service.list_owners(session),
    }


@router.get("/categories", response_class=HTMLResponse)
async def categories_page(request: Request, db: AsyncSession = Depends(get_db)):
    categories = await category_service.list_categories(db)
    return templates.TemplateResponse(
        request,
        "categories.html",
        {
            "categories": categories,
            "category_styles": category_style_map(categories),
        },
    )


@router.post("/categories/create")
async def create_category_form(
    slug: str = Form(...),
    label: str = Form(...),
    sort_order: int = Form(100),
    requires_invoice: str = Form("unknown"),
    is_active: str = Form("true"),
    badge_bg: str = Form("#334155"),
    badge_text: str = Form("#e2e8f0"),
    db: AsyncSession = Depends(get_db),
):
    await category_service.create(
        db,
        CategoryCreate(
            slug=slug.strip(),
            label=label.strip(),
            sort_order=sort_order,
            requires_invoice_default=INVOICE_CHOICES.get(requires_invoice),
            is_active=is_active == "true",
            badge_bg=badge_bg.strip(),
            badge_text=badge_text.strip(),
        ),
    )
    return RedirectResponse(url="/categories", status_code=303)


@router.post("/categories/{category_id}/edit")
async def edit_category_form(
    category_id: int,
    slug: str = Form(...),
    label: str = Form(...),
    sort_order: int = Form(100),
    requires_invoice: str = Form("unknown"),
    is_active: str = Form("true"),
    badge_bg: str = Form(...),
    badge_text: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        await category_service.update(
            db,
            category_id,
            CategoryUpdate(
                slug=slug.strip(),
                label=label.strip(),
                sort_order=sort_order,
                requires_invoice_default=INVOICE_CHOICES.get(requires_invoice),
                is_active=is_active == "true",
                badge_bg=badge_bg.strip(),
                badge_text=badge_text.strip(),
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedirectResponse(url="/categories", status_code=303)


@router.post("/categories/{category_id}/delete")
async def delete_category_form(category_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await category_service.delete(db, category_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedirectResponse(url="/categories", status_code=303)


@router.get("/banks", response_class=HTMLResponse)
async def banks_page(request: Request, db: AsyncSession = Depends(get_db)):
    banks = await bank_service.list_banks(db)
    return templates.TemplateResponse(request, "banks.html", {"banks": banks})


@router.post("/banks/create")
async def create_bank_form(
    key: str = Form(...),
    display_name: str = Form(...),
    default_currency: str = Form("GBP"),
    is_active: str = Form("true"),
    db: AsyncSession = Depends(get_db),
):
    await bank_service.create(
        db,
        BankCreate(
            key=key.strip().lower(),
            display_name=display_name.strip(),
            default_currency=default_currency.strip().upper(),
            is_active=is_active == "true",
        ),
    )
    return RedirectResponse(url="/banks", status_code=303)


@router.post("/banks/{bank_id}/edit")
async def edit_bank_form(
    bank_id: int,
    key: str = Form(...),
    display_name: str = Form(...),
    default_currency: str = Form("GBP"),
    is_active: str = Form("true"),
    db: AsyncSession = Depends(get_db),
):
    try:
        await bank_service.update(
            db,
            bank_id,
            BankUpdate(
                key=key.strip().lower(),
                display_name=display_name.strip(),
                default_currency=default_currency.strip().upper(),
                is_active=is_active == "true",
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedirectResponse(url="/banks", status_code=303)


@router.post("/banks/{bank_id}/delete")
async def delete_bank_form(bank_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await bank_service.delete(db, bank_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedirectResponse(url="/banks", status_code=303)


@router.get("/invoice-owners", response_class=HTMLResponse)
async def invoice_owners_page(request: Request, db: AsyncSession = Depends(get_db)):
    owners = await invoice_owner_service.list_owners(db)
    return templates.TemplateResponse(request, "invoice_owners.html", {"owners": owners})


@router.post("/invoice-owners/create")
async def create_invoice_owner_form(
    name: str = Form(...),
    email: str = Form(""),
    notes: str = Form(""),
    is_active: str = Form("true"),
    db: AsyncSession = Depends(get_db),
):
    await invoice_owner_service.create(
        db,
        InvoiceOwnerCreate(
            name=name.strip(),
            email=email.strip() or None,
            notes=notes.strip() or None,
            is_active=is_active == "true",
        ),
    )
    return RedirectResponse(url="/invoice-owners", status_code=303)


@router.post("/invoice-owners/{owner_id}/edit")
async def edit_invoice_owner_form(
    owner_id: int,
    name: str = Form(...),
    email: str = Form(""),
    notes: str = Form(""),
    is_active: str = Form("true"),
    db: AsyncSession = Depends(get_db),
):
    try:
        await invoice_owner_service.update(
            db,
            owner_id,
            InvoiceOwnerUpdate(
                name=name.strip(),
                email=email.strip() or None,
                notes=notes.strip() or None,
                is_active=is_active == "true",
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedirectResponse(url="/invoice-owners", status_code=303)


@router.post("/invoice-owners/{owner_id}/delete")
async def delete_invoice_owner_form(owner_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await invoice_owner_service.delete(db, owner_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedirectResponse(url="/invoice-owners", status_code=303)


@router.get("/vendors", response_class=HTMLResponse)
async def vendors_page(request: Request, db: AsyncSession = Depends(get_db)):
    ctx = await _reference_context(db)
    vendors = await vendor_service.list_vendors(db)
    return templates.TemplateResponse(
        request,
        "vendors.html",
        {**ctx, "vendors": vendors},
    )


@router.post("/vendors/create")
async def create_vendor_form(
    name: str = Form(...),
    aliases: str = Form(""),
    default_category: str = Form(""),
    requires_invoice: str = Form("unknown"),
    default_invoice_provider: str = Form(""),
    default_invoice_owner: str = Form(""),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    await vendor_service.create(
        db,
        VendorCreate(
            name=name.strip(),
            aliases=_parse_aliases(aliases),
            default_category=default_category or None,
            default_requires_invoice=INVOICE_CHOICES.get(requires_invoice),
            default_invoice_provider=default_invoice_provider.strip() or None,
            default_invoice_owner=default_invoice_owner.strip() or None,
            notes=notes.strip() or None,
        ),
    )
    return RedirectResponse(url="/vendors", status_code=303)


@router.post("/vendors/{vendor_id}/edit")
async def edit_vendor_form(
    vendor_id: int,
    name: str = Form(...),
    aliases: str = Form(""),
    default_category: str = Form(""),
    requires_invoice: str = Form("unknown"),
    default_invoice_provider: str = Form(""),
    default_invoice_owner: str = Form(""),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    try:
        await vendor_service.update(
            db,
            vendor_id,
            VendorUpdate(
                name=name.strip(),
                aliases=_parse_aliases(aliases),
                default_category=default_category or None,
                default_requires_invoice=INVOICE_CHOICES.get(requires_invoice),
                default_invoice_provider=default_invoice_provider.strip() or None,
                default_invoice_owner=default_invoice_owner.strip() or None,
                notes=notes.strip() or None,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedirectResponse(url="/vendors", status_code=303)


@router.post("/vendors/{vendor_id}/delete")
async def delete_vendor_form(vendor_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await vendor_service.delete(db, vendor_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedirectResponse(url="/vendors", status_code=303)
