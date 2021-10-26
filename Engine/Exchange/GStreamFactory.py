from .ExchangeFactory import *

class GStreamFactory():

    def CreateGStream( gstreamParams, granular = False ):
        exchange = ExchangeFactory.CreateExchange(gstreamParams)
        gstream_key = exchange.Add_GStream( gstreamParams['dataType'], gstreamParams['symbol'], gstreamParams['interval'], granular = granular )
        return exchange, gstream_key