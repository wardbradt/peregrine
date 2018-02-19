from flask import Flask, render_template, flash, request, url_for
from async_build_markets import build_arbitrage_graph_for_exchanges
from async_build_markets import build_graph_for_exchanges
import networkx as nx
import ccxt


app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = 'peregrine-scout'

@app.route("/", methods=['GET', 'POST'])
def index():
    exchange_list = ccxt.exchanges
    image_path = ""
    if request.method == 'POST':
        selected_exchanges = request.form.getlist('exchange')

        print(selected_exchanges)

        flash(selected_exchanges)

        # G = build_graph_for_exchanges(['bittrex', 'bitstamp', 'quoinex'])
        G2 = build_arbitrage_graph_for_exchanges(selected_exchanges)

        # nx.drawing.nx_pydot.to_pydot(G).write_png('exchange_graph.png')
        png = nx.drawing.nx_pydot.to_pydot(G2).write_png('static/arbitrage_graph.png')

        image_path = url_for('static',filename='arbitrage_graph.png')

    # if request.method == 'POST':
    #     article=request.form['article']
    #
    #     if form.validate():
    #         flash(clf.predict([article])[0])
    #     else:
    #         flash('Error categorizing article.')
    return render_template('index.html', exchange_list = exchange_list, image_path=image_path)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
