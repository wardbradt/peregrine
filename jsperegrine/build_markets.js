// Note: this is untested
const fs = require('fs');


async function build_all_collections(exchange_list, write, ccxt_errors) {
    let temp = await get_collections(exchange_list);
    const collections = temp[0];
    const singularly_available_markets = temp[1];

    fs.writeFile('collections.json', JSON.stringify(collections), 'utf8');
    fs.writeFile('singularly_available_markets.json', JSON.stringify(singularly_available_markets), 'utf8');
}

async function get_collections(exchange_list) {
    let collections = {};
    let singularly_available_markets = {};

    for (var i = 0; i < exchange_list.length; i++) {
        var exchange = exchange_list[i];
        await exchange.loadMarkets();
        let symbols = exchange.symbols;
        for (var j = 0; j < symbols.length; j++) {
            var symbol = symbols[j];
            if (symbol in collections) {
                collections[symbol].push(exchange);
            } else if (symbol in singularly_available_markets) {
                collections[symbol] = [singularly_available_markets[symbol], exchange];
                delete singularly_available_markets[symbol];
            } else {
                singularly_available_markets[symbol] = exchange;
            }
        }
    }

    return [collections, singularly_available_markets]
}

async function add_exchange_to_collection(exchange) {
    await exchange.loadMarkets();
    var symbols = exchange.symbols;
    symbols.forEach()
}
// let all_exchanges = ccxt.exchanges;

function build_all_collections(exchange_list, write, ccxt_errors) {
    async.each(exchange_list, function(exchange) {

    }, callback);
}
