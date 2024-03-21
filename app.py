# **********************************************************
# * CATEGORY  SOFTWARE
# * GROUP     ADMIN
# * AUTHOR    LANCE HAYNIE <LHAYNIE@SCCITY.ORG>
# **********************************************************
# Jira Error Logging
# Copyright Santa Clara City
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.#
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os, requests, json, time, yaml
from flask import Flask, jsonify, request, abort
from flask_restful import Resource, Api
from dotenv import load_dotenv

app = Flask(__name__)
api = Api(app)


class Logger(Resource):
    def get(self):
        args = request.args
        app = args.get("app", default="", type=str)
        level = args.get("level", default="", type=str)
        function = args.get("function", default="", type=str)
        msg = args.get("msg", default="", type=str)

        client = JiraClient(jira_api, jira_auth)

        if app == "":
            abort(400, description="No app provided!")

        if level == "":
            abort(400, description="No level provided!")

        if function == "":
            abort(400, description="No function provided!")

        if msg == "":
            abort(400, description="No msg provided!")

        return client.create_issue(app, level, function, msg)


class JiraClient:
    def __init__(self, api_url, auth):
        self.api_url = api_url
        self.auth = auth

    def fetch_issues(self):
        headers = {"Accept": "application/json"}
        query = {"jql": os.getenv("JIRA_JQL")}
        response = requests.get(
            self.api_url + "/rest/api/3/search",
            headers=headers,
            params=query,
            auth=self.auth,
        )

        if response.status_code == 200:
            data = json.loads(response.text)
            return data.get("issues", [])
        else:
            print(f"Failed to fetch Jira issues. Status code: {response.status_code}")
            return []

    def create_issue(self, app, level, function, msg):
        existing_issues = self.fetch_issues()
        new_issue_summary = f"APP: {app.upper()} - LEVEL: {level.upper()} - FUNCTION: {function.upper()}"
        summary_exists = any(
            issue["fields"]["summary"] == new_issue_summary for issue in existing_issues
        )

        if level.lower() == "info":
            priority = "Lowest"
        elif level.lower() == "debug":
            priority = "Low"
        elif level.lower() == "warning":
            priority = "Medium"
        elif level.lower() == "error":
            priority = "High"
        elif level.lower() == "critical":
            priority = "Highest"
        else:
            priority = "Medium"

        if not summary_exists:
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            payload = json.dumps(
                {
                    "fields": {
                        "description": {
                            "content": [
                                {
                                    "content": [{"text": f"{msg}", "type": "text"}],
                                    "type": "paragraph",
                                }
                            ],
                            "type": "doc",
                            "version": 1,
                        },
                        "issuetype": {"name": "Bug"},
                        "labels": ["ERROR", "JIRA-LOGGER"],
                        "priority": {"name": priority},
                        "project": {"key": os.getenv("JIRA_PROJECT")},
                        "components": [{"name": os.getenv("JIRA_COMPONENT")}],
                        "summary": new_issue_summary,
                    }
                }
            )
            response = requests.request(
                "POST",
                self.api_url + "/rest/api/3/issue",
                data=payload,
                headers=headers,
                auth=self.auth,
            )

            return json.loads(response.text)
        else:
            return jsonify(msg="An issue with the same summary already exists.")


@app.errorhandler(404)
def PageNotFound(e):
    return jsonify(error=str(e)), 404


@app.route("/", methods=["GET"])
def HttpRoot():
    return jsonify(
        application="Jira Issue Logger",
        copyright="Santa Clara City (UT)",
        author="Lance Haynie",
    )


api.add_resource(Logger, "/logger")

if __name__ == "__main__":
    from waitress import serve

    load_dotenv()

    jira_api = os.getenv("JIRA_API_URL")
    jira_auth = (os.getenv("JIRA_USER"), os.getenv("JIRA_API_KEY"))

    serve(app, host="0.0.0.0", port=5000, threads=100)
