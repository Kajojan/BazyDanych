import re
import os
from flask import Flask, jsonify, request,abort
from neo4j import GraphDatabase
from dotenv import load_dotenv


app = Flask(__name__)

load_dotenv()

uri = os.getenv('URI')
user = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, password), database="neo4j")

def getWorkers(tx, sort: str = '', sortType: str = '', filter: str = '', filterType: str = ''):
    query = "MATCH (m:Employee) RETURN m"
    if (sortType == 'asc'):
        if (sort == 'name'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.name"
        elif (sort == 'surname'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.surname"
        elif (sort == 'position'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.position"
    if (sortType == 'desc'):
        if (sort == 'name'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.name DESC"
        elif (sort == 'surname'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.surname DESC"
        elif (sort == 'position'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.position DESC"
    if (filterType == 'name'):
        query = f"MATCH (m:Employee) WHERE m.name CONTAINS '{filter}' RETURN m"
    if (filterType == 'surname'):
        query = f"MATCH (m:Employee) WHERE m.surname CONTAINS '{filter}' RETURN m"
    if (filterType == 'position'):
        query = f"MATCH (m:Employee) WHERE m.position CONTAINS '{filter}' RETURN m"
    results = tx.run(query).data()
    workers = [{'name': result['m']['name'],
               'surname': result['m']['surname']} for result in results]
    return workers


@app.route('/employees', methods=['GET'])
def getWorkersRoute():
    args = request.args
    sort = args.get("sort")
    sortType = args.get("sortType")
    filter = args.get("filter")
    filterType = args.get("filterType")
    with driver.session() as session:
        workers = session.execute_read(
            getWorkers, sort, sortType, filter, filterType)
    res = {'workers': workers}
    return jsonify(res)


def add_employee():
    req_data = request.get_json()
    first_name = req_data.get('first_name')
    last_name = req_data.get('last_name')
    position = req_data.get('position')
    department = req_data.get('department')

    if not first_name or not last_name or not position or not department:
        return jsonify({'message': 'Please provide first name, last name, position, and department'}), 400

    with driver.session() as session:
        check_query = f"MATCH (e:Employee) WHERE e.first_name = '{first_name}' AND e.last_name = '{last_name}' RETURN e"
        check_result = session.run(check_query)
        if check_result.single():
            return jsonify({'message': 'Employee with that name already exists'}), 400
        else:
            add_query = f"CREATE (e:Employee {{first_name: '{first_name}', last_name: '{last_name}', position: '{position}', department: '{department}'}}) RETURN e"
            result = session.run(add_query)
            employee = dict(result.single()["e"])
            return jsonify(employee)

@app.route("/employees", methods=["POST"])
def employees():
    return add_employee()

@app.route("/employees/<int:employee_id>", methods=["PUT"])
def update_employee(employee_id):
    req_data = request.get_json()
    first_name = req_data.get('first_name')
    last_name = req_data.get('last_name')
    position = req_data.get('position')
    department = req_data.get('department')

    with driver.session() as session:
        check_query = f"MATCH (e:Employee) WHERE ID(e) = {employee_id} RETURN e"
        check_result = session.run(check_query)
        if check_result.single():
            employee = check_result.single()["e"]
            if first_name:
                employee["first_name"] = first_name
            if last_name:
                employee["last_name"] = last_name
            if position:
                employee["position"] = position
            if department:
                employee["department"] = department
            session.write_transaction(lambda tx: tx.run(f"SET e = {employee} WHERE ID(e) = {employee_id}"))
            return jsonify(employee)
        else:
            abort(404, {'message': 'Employee not found'})
    
@app.route("/employees/<int:employee_id>", methods=["DELETE"])
def delete_employee(employee_id):
    with driver.session() as session:
        check_query = f"MATCH (e:Employee) WHERE ID(e) = {employee_id} RETURN e"
        check_result = session.run(check_query)
        if check_result.single():
            employee = check_result.single()["e"]
            department_name = employee.get("department")
            if department_name:
                check_manager_query = f"MATCH (d:Department {{name: '{department_name}'}})<-[:MANAGES]-(e:Employee) WHERE ID(e) = {employee_id} RETURN d"
                check_manager_result = session.run(check_manager_query)
                if check_manager_result.single():
                    reassign_query = f"MATCH (d:Department {{name: '{department_name}'}})<-[:MANAGES]-(e:Employee) WHERE ID(e) = {employee_id} SET d.manager = ''"
                    session.run(reassign_query)
            delete_query = f"MATCH (e:Employee) WHERE ID(e) = {employee_id} DETACH DELETE e"
            session.run(delete_query)
            return jsonify({'message': 'Employee has been deleted'})
        else:
            abort(404, {'message': 'Employee not found'})


@app.route("/employees/<int:employee_id>/subordinates", methods=["GET"])
def get_subordinates(employee_id):
    with driver.session() as session:
        query = f"MATCH (e:Employee)-[:MANAGES]->(s:Employee) WHERE ID(e) = {employee_id} RETURN s"
        result = session.run(query)
        subordinates = [record["s"] for record in result]
        if subordinates:
            return jsonify(subordinates)
        else:
            abort(404, {'message': 'Subordinates not found'})

@app.route("/employees/<int:employee_id>", methods=["GET"])
def get_employee(employee_id):
    with driver.session() as session:
        query = f"MATCH (e:Employee)-[:BELONGS_TO]->(d:Department) WHERE ID(e) = {employee_id} RETURN e, d"
        result = session.run(query)
        if result.single():
            employee = result.single()["e"]
            department = result.single()["d"]
            employee["department"] = department
            return jsonify(employee)
        else:
            abort(404, {'message': 'Employee not found'})


@app.route("/departments", methods=["GET"])
def get_departments():
    name = request.args.get("name")
    sort_by = request.args.get("sort_by")
    sort_order = request.args.get("sort_order")
    where_clause = ""
    order_clause = ""
    if name:
        where_clause = f"WHERE d.name CONTAINS '{name}'"
    if sort_by and sort_order:
        order_clause = f"ORDER BY d.{sort_by} {sort_order}"
    with driver.session() as session:
        query = f"MATCH (d:Department) {where_clause} {order_clause} RETURN d"
        result = session.run(query)
        departments = [record["d"] for record in result]
        return jsonify(departments)


@app.route("/departments/<int:department_id>/employees", methods=["GET"])
def get_employees(department_id):
    with driver.session() as session:
        query = f"MATCH (d:Department)-[:WORKS_IN]->(e:Employee) WHERE ID(d) = {department_id} RETURN e"
        result = session.run(query)
        employees = [record["e"] for record in result]
        if employees:
            return jsonify(employees)
        else:
            abort(404, {'message': 'Employees not found'})

if __name__ == "__main__":
    app.run()