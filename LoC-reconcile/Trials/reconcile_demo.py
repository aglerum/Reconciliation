"""
An example reconciliation service API for Google Refine 2.0.
See http://code.google.com/p/google-refine/wiki/ReconciliationServiceApi.
"""
import csv
# import re
from fuzzywuzzy import fuzz

from flask import Flask, request, jsonify, json
app = Flask(__name__)

match_threshold = 70

# Basic service metadata. There are a number of other documented options
# but this is all we need for a simple service.
metadata = {
    "name": "Presidential Reconciliation Service",
    "defaultTypes": [{"id": "/people/presidents", "name": "US President"}],
    }

# Read in person records from csv file.
reader = csv.DictReader(open('etdnaf_indirect_name_201910.csv', 'rb'))
records = [r for r in reader]

# CSV snippet
# Source,Family,IndirectName,Given,Fuller,Terms,Date,URI
# ETD_NAF,AbdelRazig,"AbdelRazig, Yassir",Yassir,,,,https://authorities.lib.fsu.edu/etd-naf/yabdelrazig
# Data needed: IndirectName (to match on) and URI


# The data we'll match against.
# presidents = [
#     "George Washington", "John Adams", "Thomas Jefferson", "James Madison",
#     "James Monroe", "John Quincy Adams", "Andrew Jackson", "Martin Van Buren",
#     "William Henry Harrison", "John Tyler", "James K. Polk", "Zachary Taylor",
#     "Millard  Fillmore", "Franklin Pierce", "James Buchanan",
#     "Abraham Lincoln", "Andrew Jackson", "Ulysses S. Grant",
#     "Rutherford B. Hayes", "James A. Garfield", "Chester A. Arthur",
#     "Grover Cleveland", "Benjamin Harrison", "William McKinley",
#     "Theodore Roosevelt", "William Howard Taft", "Woodrow Wilson",
#     "Warren G. Harding", "Calvin Coolidge", "Herbert Hoover",
#     "Franklin D. Roosevelt", "Harry S. Truman", "Dwight D. Eisenhower",
#     "John F. Kennedy", "Lyndon B. Johnson", "Richard Nixon", "Gerald Ford",
#     "Jimmy Carter", "Ronald Reagan", "George H. W. Bush", "Bill Clinton",
#     "George W. Bush", "Barack Obama",
#     ]


def search(query):
    """
    Do a simple fuzzy match, returning results in
    Refine reconciliation API format.
    """
    # pattern = re.compile(query, re.IGNORECASE)
    matches = []

    for r in records:
        score = fuzz.token_set_ratio(query, r['label'])

        if score > match_threshold:
            matches.append({
                "id": r['URL'],
                "name": r['IndirectName'],
                "score": score,
                "match": query == r['IndirectName'],
                "type": [{"id": "/people/person", "name": "Person"}]
            })

    return matches


def jsonpify(obj):
    """
    Like jsonify but wraps result in a JSONP callback if a 'callback'
    query param is supplied.
    """
    try:
        callback = request.args['callback']
        response = app.make_response("%s(%s)" % (callback, json.dumps(obj)))
        response.mimetype = "text/javascript"
        return response
    except KeyError:
        return jsonify(obj)


@app.route("/reconcile", methods=['POST', 'GET'])
def reconcile():
    # If a single 'query' is provided do a straightforward search.
    query = request.form.get('query')
    if query:
        # If the 'query' param starts with a "{" then it is a JSON object
        # with the search string as the 'query' member. Otherwise,
        # the 'query' param is the search string itself.
        if query.startswith("{"):
            query = json.loads(query)['query']
        results = search(query)
        return jsonpify({"result": results})

    # If a 'queries' parameter is supplied then it is a dictionary
    # of (key, query) pairs representing a batch of queries. We
    # should return a dictionary of (key, results) pairs.
    queries = request.form.get('queries')
    if queries:
        queries = json.loads(queries)
        results = {}
        for (key, query) in queries.items():
            results[key] = {"result": search(query['query'])}
        return jsonpify(results)

    # If neither a 'query' nor 'queries' parameter is supplied then
    # we should return the service metadata.
    return jsonpify(metadata)


if __name__ == '__main__':
    app.run(debug=True)
