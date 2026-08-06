from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ClassificationSource, TransactionStatus
from app.models.transaction import Transaction
from app.schemas.internal import ClassificationResult


class MemoryMatcher:
    SIMILARITY_THRESHOLD = 0.85

    async def find_match(
        self,
        session: AsyncSession,
        description_normalized: str,
        bank_name: str,
        amount: Decimal,
        account_last4: str | None = None,
    ) -> ClassificationResult | None:
        stmt = (
            select(Transaction)
            .where(
                Transaction.status.in_(["confirmed", "resolved"]),
                Transaction.classification_source == ClassificationSource.MANUAL.value,
            )
            .order_by(Transaction.updated_at.desc())
            .limit(500)
        )
        result = await session.execute(stmt)
        candidates = result.scalars().all()

        best_score = 0.0
        best: Transaction | None = None
        for tx in candidates:
            score = self._score_candidate(
                description_normalized,
                bank_name,
                amount,
                account_last4,
                tx,
            )
            if score > best_score:
                best_score = score
                best = tx

        if best is None or best_score < self.SIMILARITY_THRESHOLD:
            return None

        return ClassificationResult(
            category=best.category,
            requires_invoice=best.requires_invoice,
            invoice_provider=best.invoice_provider,
            invoice_owner=self._resolve_invoice_owner(
                candidates,
                description_normalized,
                amount,
                account_last4,
            ),
            confidence=Decimal(str(min(0.95, 0.7 + best_score * 0.25))),
            classification_source=ClassificationSource.MEMORY.value,
            status=TransactionStatus.NEW.value,
        )

    def _score_candidate(
        self,
        description_normalized: str,
        bank_name: str,
        amount: Decimal,
        account_last4: str | None,
        tx: Transaction,
    ) -> float:
        score = self._similarity(description_normalized, tx.description_normalized)
        if score < self.SIMILARITY_THRESHOLD:
            return score
        if tx.bank_name.lower() == bank_name.lower():
            score += 0.02
        if tx.amount == amount:
            score += 0.05
        if account_last4 and tx.account_last4 == account_last4:
            score += 0.1
        return score

    def _resolve_invoice_owner(
        self,
        candidates: list[Transaction],
        description_normalized: str,
        amount: Decimal,
        account_last4: str | None,
    ) -> str | None:
        owner_matches = [
            tx
            for tx in candidates
            if tx.invoice_owner
            and tx.amount == amount
            and self._similarity(description_normalized, tx.description_normalized)
            >= self.SIMILARITY_THRESHOLD
        ]
        if not owner_matches:
            return None
        if len(owner_matches) == 1:
            return owner_matches[0].invoice_owner

        if account_last4:
            card_matches = [tx for tx in owner_matches if tx.account_last4 == account_last4]
            if len(card_matches) == 1:
                return card_matches[0].invoice_owner
            owners = {tx.invoice_owner for tx in card_matches if tx.invoice_owner}
            if len(owners) == 1:
                return owners.pop()

        return None

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        if a == b:
            return 1.0
        if not a or not b:
            return 0.0
        tokens_a = set(a.split())
        tokens_b = set(b.split())
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b
        return len(intersection) / len(union)
