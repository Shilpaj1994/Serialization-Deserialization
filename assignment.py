#!/usr/bin/env python3
"""
This script is used to serialize and deserialize the data using custom encoder and decoder.
"""
# Standard imports
from datetime import date, datetime
from decimal import Decimal
import json

# Third party imports
from marshmallow import Schema, fields, validate, ValidationError, post_load, EXCLUDE
from marshmallow.fields import Field
from marshmallow.utils import missing


class Stock:
    """
    Stock class to represent a stock.
    """
    def __init__(self, symbol, date, open_, high, low, close, volume):
        """
        Initialize the Stock object.
        """
        self.symbol: str = symbol
        self.date: date = date
        self.open: Decimal = open_
        self.high: Decimal = high
        self.low: Decimal = low
        self.close: Decimal = close
        self.volume: int = volume
        self.datatype: str = 'stock'

    def toJSON(self):
        """
        Convert the Stock object to a JSON serializable dictionary.
        """
        return vars(self)


class Trade:
    """
    Trade class to represent a trade.
    """
    def __init__(self, symbol, timestamp, order, price, volume, commission):
        """
        Initialize the Trade object.
        """
        self.symbol: str = symbol
        self.timestamp: datetime = timestamp
        self.order: str = order
        self.price: Decimal = price
        self.commission: Decimal = commission
        self.volume: int = volume
        self.datatype: str = 'trade'

    def toJSON(self):
        """
        Convert the Trade object to a JSON serializable dictionary.
        """
        return vars(self)


class CustomEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle the serialization of custom objects.
    """
    def default(self, arg):
        """
        Default method to handle the serialization of custom objects.
        """
        if isinstance(arg, Stock):
            data = arg.toJSON()
            if 'open' in data:
                data['open_'] = data.pop('open')
            return data
        elif isinstance(arg, Trade):
            return arg.toJSON()
        elif isinstance(arg, datetime):
            return arg.isoformat()
        elif isinstance(arg, date):
            return dict(
                datatype="date",
                date=arg.isoformat(),
            )
        elif isinstance(arg, Decimal):
            return str(arg)
        return super().default(arg)


def custom_decoder(arg):
    """
    Custom decoder to handle the deserialization of custom objects.
    :param arg: The object to be deserialized.
    :return: The deserialized object.
    """
    if isinstance(arg, dict) and 'datatype' in arg:
        datatype = arg['datatype']
        arg_copy = arg.copy()
        del arg_copy['datatype']
        
        if datatype == 'date':
            return date.fromisoformat(arg['date'])
        elif datatype == 'trade':
            arg_copy['timestamp'] = datetime.fromisoformat(arg_copy.get('timestamp', ''))
            for key in ['price', 'commission']:
                arg_copy[key] = Decimal(str(arg_copy[key]))
            return Trade(**arg_copy)
        elif datatype == 'stock':
            if 'open' in arg_copy:
                arg_copy['open_'] = arg_copy.pop('open')
            for key in ['open_', 'high', 'low', 'close']:
                arg_copy[key] = Decimal(str(arg_copy[key]))
            if isinstance(arg_copy['date'], date):
                pass
            elif isinstance(arg_copy['date'], dict) and arg_copy['date'].get('datatype') == 'date':
                arg_copy['date'] = date.fromisoformat(arg_copy['date']['date'])
            else:
                arg_copy['date'] = date.fromisoformat(arg_copy['date'])
            return Stock(**arg_copy)
    return arg


class DecimalField(Field):
    """
    Custom field for handling Decimal values.
    """
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return str(value)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return Decimal(str(value))
        except (TypeError, ValueError) as error:
            raise ValidationError("Not a valid decimal value.") from error


class StockSchema(Schema):
    """
    StockSchema class to represent the Stock object.
    """
    symbol = fields.Str(required=True, validate=validate.Length(equal=4))
    date = fields.Date(required=True)
    open_ = DecimalField(data_key='open', required=True)
    high = DecimalField(required=True)
    low = DecimalField(required=True)
    close = DecimalField(required=True)
    volume = fields.Integer(required=True)
    datatype = fields.Constant('stock', dump_only=True)

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_stock(self, data, **kwargs):
        """Create a Stock object from the deserialized data."""
        return Stock(**data)


class TradeSchema(Schema):
    """
    TradeSchema class to represent the Trade object.
    """
    symbol = fields.Str(required=True, validate=validate.Length(equal=4))
    timestamp = fields.DateTime(required=True)
    order = fields.Str(required=True, validate=validate.OneOf(['buy', 'sell']))
    price = DecimalField(required=True)
    commission = DecimalField(required=True)
    volume = fields.Integer(required=True)
    datatype = fields.Constant('trade', dump_only=True)

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_trade(self, data, **kwargs):
        """Create a Trade object from the deserialized data."""
        return Trade(**data)


def serialize_with_marshmallow(obj):
    """
    Serialize the object with Marshmallow.
    :param obj: Object to serialize
    :return: JSON string
    """
    if isinstance(obj, Stock):
        schema = StockSchema()
        data = schema.dump(obj)
        if 'open_' in data:
            data['open'] = data.pop('open_')
        return json.dumps(data)
    elif isinstance(obj, Trade):
        return TradeSchema().dumps(obj)
    else:
        raise ValueError("Object must be either Stock or Trade")


def deserialize_with_marshmallow(json_str, schema):
    """
    Deserialize the object with Marshmallow.
    :param json_str: JSON string to deserialize
    :param schema: Schema to use for deserialization
    :return: Deserialized object
    """
    try:
        # Handle both string and dict inputs
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
        
        # For StockSchema, ensure we have the correct field name before loading
        if isinstance(schema, StockSchema):
            # If 'open_' exists, convert it to 'open'
            if 'open_' in data:
                data['open'] = data.pop('open_')
            # If neither field exists, raise error
            elif 'open' not in data:
                raise ValueError("Missing required field 'open'")
            
        # Use schema to load and validate the data
        return schema.load(data)
    except Exception as e:
        raise ValueError(f"Failed to deserialize: {str(e)}")
