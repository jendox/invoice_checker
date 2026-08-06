import math
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ClassificationSource, TransactionStatus
from app.models.feedback import Feedback
from app.models.statement_file import StatementFile
from app.models.transaction import Transaction
from app.schemas.internal import ClassificationResult, ParsedTransaction
from app.schemas.statement import StatementUploadResponse
from app.schemas.transaction import (
    ClassificationUpdate,
    DeleteTransactionsRequest,
    ReclassifyRequest,
    TransactionFilters,
    TransactionScopeRequest,
)
from app.services.classifier.classifier import TransactionClassifier
from app.services.classifier.normalizer import make_fingerprint
from app.services.parser.statement_parser import ParseError, StatementParser
from app.services.parser.bank_presets import normalize_bank_key
from app.services.seed_rules import seed_default_rules


def _apply_equal_filters(stmt, filters: TransactionFilters, fields: tuple[tuple[str, object], ...]):
    for field, column in fields:
        value = getattr(filters, field)
        if value:
            stmt = stmt.where(column == value)
    return stmt


def _apply_transaction_filters(stmt, filters: TransactionFilters):
    stmt = _apply_equal_filters(
        stmt,
        filters,
        (
            ("bank_name", Transaction.bank_name),
            ("status", Transaction.status),
            ("category", Transaction.category),
            ("statement_month", StatementFile.statement_month),
            ("company_name", StatementFile.company_name),
        ),
    )
    if filters.date_from:
        stmt = stmt.where(Transaction.transaction_date >= filters.date_from)
    if filters.date_to:
        stmt = stmt.where(Transaction.transaction_date <= filters.date_to)
    if filters.requires_invoice is not None:
        stmt = stmt.where(Transaction.requires_invoice == filters.requires_invoice)
    if filters.search:
        pattern = f"%{filters.search.lower()}%"
        stmt = stmt.where(
            Transaction.description_raw.ilike(pattern)
            | Transaction.description_normalized.ilike(pattern)
            | Transaction.merchant_name.ilike(pattern),
        )
    return stmt


def _apply_classification(
    tx: Transaction,
    desc_norm: str,
    merchant: str | None,
    classification: ClassificationResult,
) -> None:
    tx.description_normalized = desc_norm
    if merchant and not tx.merchant_name:
        tx.merchant_name = merchant
    tx.category = classification.category
    tx.requires_invoice = classification.requires_invoice
    tx.invoice_provider = classification.invoice_provider
    tx.invoice_owner = classification.invoice_owner
    tx.confidence = classification.confidence
    tx.classification_source = classification.classification_source
    tx.status = classification.status


def _classification_unchanged(tx: Transaction, classification: ClassificationResult) -> bool:
    return (
        tx.category,
        tx.requires_invoice,
        tx.invoice_provider,
        tx.invoice_owner,
        tx.classification_source,
        tx.status,
    ) == (
        classification.category,
        classification.requires_invoice,
        classification.invoice_provider,
        classification.invoice_owner,
        classification.classification_source,
        classification.status,
    )


def _filters_from_scope(scope: TransactionScopeRequest) -> TransactionFilters:
    return TransactionFilters(
        bank_name=scope.bank_name,
        statement_month=scope.statement_month,
        date_from=scope.date_from,
        date_to=scope.date_to,
        requires_invoice=scope.requires_invoice,
        status=scope.status,
        category=scope.category,
        company_name=scope.company_name,
        search=scope.search,
    )


def _filtered_transactions_stmt(scope: TransactionScopeRequest):
    return _apply_transaction_filters(
        select(Transaction).join(StatementFile),
        _filters_from_scope(scope),
    )


class TransactionService:
    def __init__(self) -> None:
        self.parser = StatementParser()
        self.classifier = TransactionClassifier()

    async def upload_statement(
        self,
        session: AsyncSession,
        content: bytes,
        filename: str,
        bank_name: str,
        statement_month: str,
        company_name: str | None = None,
        statement_currency: str = "GBP",
    ) -> StatementUploadResponse:
        await seed_default_rules(session)

        bank_key = normalize_bank_key(bank_name)
        currency = statement_currency.strip().upper()[:3]

        try:
            parsed = self.parser.parse_file(content, filename, bank_key, currency)
        except ParseError as e:
            raise ValueError(str(e)) from e

        statement = StatementFile(
            bank_name=bank_key,
            company_name=company_name,
            statement_month=statement_month,
            currency=currency,
            original_filename=filename,
        )
        session.add(statement)
        await session.flush()

        imported = 0
        skipped = 0
        needs_review = 0
        requires_invoice = 0

        for item in parsed:
            created = await self._import_transaction(session, statement, item, bank_key)
            if created is None:
                skipped += 1
                continue
            imported += 1
            if created.status == TransactionStatus.NEEDS_REVIEW.value:
                needs_review += 1
            if created.requires_invoice is True:
                requires_invoice += 1

        await session.commit()
        await session.refresh(statement)

        return StatementUploadResponse(
            statement_file_id=statement.id,
            bank_name=statement.bank_name,
            company_name=statement.company_name,
            statement_month=statement.statement_month,
            currency=statement.currency,
            original_filename=statement.original_filename,
            imported_count=imported,
            skipped_duplicates=skipped,
            needs_review_count=needs_review,
            requires_invoice_count=requires_invoice,
        )

    async def _import_transaction(
        self,
        session: AsyncSession,
        statement: StatementFile,
        item: ParsedTransaction,
        bank_name: str,
    ) -> Transaction | None:
        desc_norm, merchant, classification = await self.classifier.classify_transaction(
            session,
            item.description_raw,
            bank_name,
            item.direction,
            item.amount,
            item.account_last4,
        )

        fingerprint = make_fingerprint(
            bank_name, item.transaction_date, item.amount, item.currency, desc_norm,
        )

        existing = await session.execute(
            select(Transaction.id).where(Transaction.fingerprint == fingerprint),
        )
        if existing.scalar_one_or_none():
            return None

        tx = Transaction(
            statement_file_id=statement.id,
            bank_name=bank_name,
            transaction_date=item.transaction_date,
            posting_date=item.posting_date,
            description_raw=item.description_raw,
            description_normalized=desc_norm,
            amount=item.amount,
            currency=item.currency,
            direction=item.direction,
            account_last4=item.account_last4,
            merchant_name=item.merchant_name or merchant,
            category=classification.category,
            requires_invoice=classification.requires_invoice,
            invoice_provider=classification.invoice_provider,
            invoice_owner=classification.invoice_owner,
            confidence=classification.confidence,
            classification_source=classification.classification_source,
            status=classification.status,
            fingerprint=fingerprint,
        )
        session.add(tx)
        return tx

    async def list_transactions(
        self, session: AsyncSession, filters: TransactionFilters,
    ) -> tuple[list[Transaction], int]:
        stmt = _apply_transaction_filters(select(Transaction).join(StatementFile), filters)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        offset = (filters.page - 1) * filters.page_size
        stmt = stmt.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        stmt = stmt.offset(offset).limit(filters.page_size)

        result = await session.execute(stmt)
        return list(result.scalars().all()), total

    async def update_classification(
        self,
        session: AsyncSession,
        transaction_id: int,
        update: ClassificationUpdate,
    ) -> Transaction:
        result = await session.execute(select(Transaction).where(Transaction.id == transaction_id))
        tx = result.scalar_one_or_none()
        if tx is None:
            raise ValueError(f"Transaction {transaction_id} not found")

        feedback = Feedback(
            transaction_id=tx.id,
            old_category=tx.category,
            new_category=update.category or tx.category,
            old_requires_invoice=tx.requires_invoice,
            new_requires_invoice=update.requires_invoice
            if update.requires_invoice is not None
            else tx.requires_invoice,
            old_invoice_provider=tx.invoice_provider,
            new_invoice_provider=update.invoice_provider
            if update.invoice_provider is not None
            else tx.invoice_provider,
            old_invoice_owner=tx.invoice_owner,
            new_invoice_owner=update.invoice_owner
            if update.invoice_owner is not None
            else tx.invoice_owner,
            comment=update.comment,
        )
        session.add(feedback)

        if update.category is not None:
            tx.category = update.category
        if update.requires_invoice is not None:
            tx.requires_invoice = update.requires_invoice
        if update.invoice_provider is not None:
            tx.invoice_provider = update.invoice_provider
        if update.invoice_owner is not None:
            tx.invoice_owner = update.invoice_owner or None
        if update.status is not None:
            tx.status = update.status
        else:
            tx.status = TransactionStatus.CONFIRMED.value

        tx.classification_source = ClassificationSource.MANUAL.value
        tx.confidence = Decimal("1.0")

        await session.commit()
        await session.refresh(tx)
        return tx

    async def reclassify_transactions(
        self,
        session: AsyncSession,
        options: ReclassifyRequest,
    ) -> tuple[int, int]:
        stmt = _filtered_transactions_stmt(options)
        stmt = stmt.where(Transaction.classification_source != ClassificationSource.MANUAL.value)

        result = await session.execute(stmt)
        transactions = list(result.scalars().all())

        updated = 0
        skipped = 0
        for tx in transactions:
            desc_norm, merchant, classification = await self.classifier.classify_transaction(
                session,
                tx.description_raw,
                tx.bank_name,
                tx.direction,
                tx.amount,
                tx.account_last4,
                skip_memory=options.skip_memory,
            )
            if _classification_unchanged(tx, classification):
                skipped += 1
                continue

            _apply_classification(tx, desc_norm, merchant, classification)
            updated += 1

        await session.commit()
        return updated, skipped

    async def count_transactions(self, session: AsyncSession, scope: TransactionScopeRequest) -> int:
        stmt = _filtered_transactions_stmt(scope)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        return (await session.execute(count_stmt)).scalar_one()

    async def delete_transactions(
        self,
        session: AsyncSession,
        options: DeleteTransactionsRequest,
    ) -> int:
        result = await session.execute(_filtered_transactions_stmt(options))
        transactions = list(result.scalars().all())
        if not transactions:
            return 0

        ids = [tx.id for tx in transactions]
        await session.execute(delete(Feedback).where(Feedback.transaction_id.in_(ids)))
        for tx in transactions:
            await session.delete(tx)

        await session.commit()
        return len(transactions)

    async def get_invoice_requests(self, session: AsyncSession) -> list[Transaction]:
        result = await session.execute(
            select(Transaction)
            .where(Transaction.requires_invoice.is_(True))
            .order_by(Transaction.transaction_date.desc()),
        )
        return list(result.scalars().all())

    @staticmethod
    def paginate(total: int, page: int, page_size: int) -> int:
        return max(1, math.ceil(total / page_size)) if total else 1
