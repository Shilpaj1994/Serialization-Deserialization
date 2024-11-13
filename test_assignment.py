import pytest
from datetime import date, datetime
from decimal import Decimal
import json
from assignment import Stock, Trade, CustomEncoder, custom_decoder, StockSchema, TradeSchema, serialize_with_marshmallow, deserialize_with_marshmallow

# Sample data for testing
activity = {
    "quotes": [
        Stock('TSLA', date(2018, 11, 22), Decimal('338.19'), Decimal('338.64'), Decimal('337.60'), Decimal('338.19'), 365_607),
        Stock('AAPL', date(2018, 11, 22), Decimal('176.66'), Decimal('177.25'), Decimal('176.64'), Decimal('176.78'), 3_699_184),
        Stock('MSFT', date(2018, 11, 22), Decimal('103.25'), Decimal('103.48'), Decimal('103.07'), Decimal('103.11'), 4_493_689)
    ],
    "trades": [
        Trade('TSLA', datetime(2018, 11, 22, 10, 5, 12), 'buy', Decimal('338.25'), 100, Decimal('9.99')),
        Trade('AAPL', datetime(2018, 11, 22, 10, 30, 5), 'sell', Decimal('177.01'), 20, Decimal('9.99'))
    ]
}

def test_custom_encoder_stock_serialization():
    """Test that Stock objects are serialized correctly with CustomEncoder."""
    stock_json = json.dumps(activity["quotes"][0], cls=CustomEncoder)
    assert '"symbol": "TSLA"' in stock_json
    assert '"date": "2018-11-22"' in stock_json

def test_custom_encoder_trade_serialization():
    """Test that Trade objects are serialized correctly with CustomEncoder."""
    trade_json = json.dumps(activity["trades"][0], cls=CustomEncoder)
    assert '"symbol": "TSLA"' in trade_json
    assert '"timestamp": "2018-11-22T10:05:12"' in trade_json

def test_custom_encoder_nested_serialization():
    """Test that a nested dictionary with Stock and Trade objects is serialized correctly."""
    nested_json = json.dumps(activity, cls=CustomEncoder)
    assert '"quotes"' in nested_json
    assert '"trades"' in nested_json

def test_custom_decoder_stock_deserialization():
    """Test that Stock objects are deserialized correctly with CustomDecoder."""
    stock_json = json.dumps(activity["quotes"], cls=CustomEncoder)
    stocks = json.loads(stock_json, object_hook=custom_decoder)
    assert isinstance(stocks[0], Stock)
    assert stocks[0].symbol == 'TSLA'

def test_custom_decoder_trade_deserialization():
    """Test that Trade objects are deserialized correctly with CustomDecoder."""
    trade_json = json.dumps(activity["trades"], cls=CustomEncoder)
    trades = json.loads(trade_json, object_hook=custom_decoder)
    assert isinstance(trades[0], Trade)
    assert trades[0].symbol == 'TSLA'

def test_custom_decoder_nested_deserialization():
    """Test that a nested dictionary with Stock and Trade objects is deserialized correctly."""
    nested_json = json.dumps(activity, cls=CustomEncoder)
    data = json.loads(nested_json, object_hook=custom_decoder)
    assert isinstance(data["quotes"][0], Stock)
    assert isinstance(data["trades"][0], Trade)


def test_marshmallow_stock_serialization():
    """Test that Stock objects are serialized correctly with Marshmallow."""
    stock_json = serialize_with_marshmallow(activity["quotes"][0])
    assert "TSLA" in stock_json
    assert "2018-11-22" in stock_json

def test_marshmallow_trade_serialization():
    """Test that Trade objects are serialized correctly with Marshmallow."""
    trade_json = serialize_with_marshmallow(activity["trades"][0])
    assert "TSLA" in trade_json
    assert "2018-11-22T10:05:12" in trade_json

def test_marshmallow_nested_serialization():
    """Test that a nested dictionary with Stock and Trade objects is serialized correctly with Marshmallow."""
    quotes_json = [serialize_with_marshmallow(stock) for stock in activity["quotes"]]
    trades_json = [serialize_with_marshmallow(trade) for trade in activity["trades"]]
    assert len(quotes_json) == 3
    assert len(trades_json) == 2

def test_marshmallow_stock_deserialization():
    """Test that Stock objects are deserialized correctly with Marshmallow."""
    stock_json = serialize_with_marshmallow(activity["quotes"][0])
    stock = deserialize_with_marshmallow(stock_json, StockSchema())
    assert isinstance(stock, Stock)
    assert stock.symbol == 'TSLA'

def test_marshmallow_trade_deserialization():
    """Test that Trade objects are deserialized correctly with Marshmallow."""
    trade_json = serialize_with_marshmallow(activity["trades"][0])
    trade = deserialize_with_marshmallow(trade_json, TradeSchema())
    assert isinstance(trade, Trade)
    assert trade.symbol == 'TSLA'

def test_marshmallow_nested_deserialization():
    """Test that a nested dictionary with Stock and Trade objects is deserialized correctly with Marshmallow."""
    quotes_json = [serialize_with_marshmallow(stock) for stock in activity["quotes"]]
    trades_json = [serialize_with_marshmallow(trade) for trade in activity["trades"]]
    quotes = [deserialize_with_marshmallow(q, StockSchema()) for q in quotes_json]
    trades = [deserialize_with_marshmallow(t, TradeSchema()) for t in trades_json]
    assert len(quotes) == 3
    assert len(trades) == 2


# Additional tests for edge cases
def test_empty_stock_list_serialization():
    """Test that an empty list of stocks serializes and deserializes correctly."""
    empty_list_json = json.dumps([], cls=CustomEncoder)
    result = json.loads(empty_list_json, object_hook=custom_decoder)
    assert result == []

def test_empty_trade_list_serialization():
    """Test that an empty list of trades serializes and deserializes correctly."""
    empty_list_json = json.dumps([], cls=CustomEncoder)
    result = json.loads(empty_list_json, object_hook=custom_decoder)
    assert result == []

def test_invalid_json_for_custom_decoder():
    """Test that invalid JSON raises a decoding error with CustomDecoder."""
    invalid_json = '{"quotes": [invalid data]}'
    with pytest.raises(json.JSONDecodeError):
        json.loads(invalid_json, object_hook=custom_decoder)

def test_invalid_json_for_marshmallow_decoder():
    """Test that invalid JSON raises a decoding error with Marshmallow."""
    invalid_json = '{"quotes": [invalid data]}'
    with pytest.raises(ValueError):
        deserialize_with_marshmallow(invalid_json, StockSchema())

def test_custom_encoder_handles_decimal_properly():
    """Test that decimals are serialized as strings in JSON."""
    stock_json = json.dumps(activity["quotes"][0], cls=CustomEncoder)
    assert '"338.19"' in stock_json

def test_custom_decoder_handles_decimal_properly():
    """Test that decimals are deserialized back into Decimal objects."""
    stock_json = json.dumps(activity["quotes"], cls=CustomEncoder)
    stocks = json.loads(stock_json, object_hook=custom_decoder)
    assert isinstance(stocks[0].open, Decimal)