"""Display precision only; comparisons and stored numeric values stay unchanged."""

from decimal import Decimal, ROUND_HALF_UP, localcontext

NUMBER_FORMAT = "0.0"
COST_FORMAT = "0.00"


def display_value(value, number_format="General") -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if number_format in {NUMBER_FORMAT, COST_FORMAT} or isinstance(value, float):
            places = 2 if number_format == COST_FORMAT else 1
            number = Decimal(str(value))
            if not number.is_finite():
                return str(value)
            # Match Excel at halfway values (2.25 -> 2.3), including negative costs.
            with localcontext() as context:
                context.prec = max(28, number.adjusted() + places + 2)
                return str(
                    number.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
                )
    return str(value)
