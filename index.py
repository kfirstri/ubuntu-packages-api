from flask import Flask
from flask_restplus import Resource, fields
from flask_restplus import Api
from requests import HTTPError
from werkzeug.contrib.fixers import ProxyFix
from bs4 import BeautifulSoup

import os
import requests

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version='0.1', title='Ubuntu Packages', prefix='/api')

package_result = api.model('PackageResult', {
    'file_path': fields.String,
    'file_name': fields.String,
    'package_name': fields.String
})


class PackageResult:
    def __init__(self, file_path: str, package: str):
        self.file_path = file_path
        self.package_name = package
        self.file_name = os.path.basename(file_path)


def get_package_name(file_name: str):
    query_url = f'https://packages.ubuntu.com/search?mode=exactfilename&suite=cosmic&section=all&arch=any&searchon=contents&keywords={file_name}'

    response = requests.get(query_url)

    try:
        response.raise_for_status()
    except HTTPError:
        return None

    # Parse results html
    html_data = BeautifulSoup(response.content)

    if not html_data.table:
        return None

    result_table_row = html_data.table.find_all('tr')

    results = []

    for row in result_table_row:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        # [executable_path, package_name]

        if not cols:
            continue

        results.append(PackageResult(cols[0], cols[1]))

    return results


@api.route('/executable/<string:file_name>')
class Package(Resource):
    @api.marshal_with(package_result)
    def get(self, file_name):
        return get_package_name(file_name)


if __name__ == '__main__':
    app.run(debug=True)
