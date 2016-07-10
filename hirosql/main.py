import click
import jinja2
import sqlalchemy as sql
from bottle import request, post, redirect, route, run

DATABASE_URL = None


def get_conn(database_name=None):
    url = DATABASE_URL
    if database_name:
        url += "/" + database_name
    engine = sql.create_engine(url, **{"encoding": "utf-8", "echo": True})
    conn = engine.connect()
    return conn


def build_select(table_name):
    where = build_where()
    return "select * from {table_name} {where};".format(**locals())


def build_delete(table_name):
    where = build_where()
    return "delete from {table_name} {where};".format(**locals())


def build_update(table_name):
    where = build_where()
    set_ = " set "
    if request.forms:
        set_ += ",".join([u" `%s`='%s' " % (k, v) for k, v in request.forms.allitems() if v != ''])
    return "update {table_name} {set_} {where};".format(**locals())


def build_where():
    where = ""
    if request.params:
        where = "where " + " or ".join("`%s`='%s'" % (k, v) for k, v in request.query.allitems())
    return where


TEMPLATE_TABLE = u"""
<script type="text/javascript" src="//code.jquery.com/jquery-2.2.0.min.js"></script>
<script type="text/javascript">$(function(){
var f=$("form[method=get]");
$("input").on("click", function(evt){ var i=$(this); var input=$("<input>").val(i.val()).attr("name", i.attr("name")); f.append(input)});
})</script>
<a href="/">top</a><br/>
<a href="/{{ database_name }}">{{ database_name }}</a><br/>
<a href="{{ request.path }}">{{ request.path }}</a><br/>
{{ query }}</br>
{{ delete }}</br>
<form method="post" action="{{ request.path + '/delete?' + request.query_string }}"
      onsubmit="return confirm('Do you really want to delete this ?');">
<input type="submit" value="delete"></form>

<form method="get" action="{{ request.path }}"><input type="submit" value="filter"></form>
<table>

<tr>{% for k in keys %}<td>{{ k }}</td>{% endfor %}<td>action</td></tr>

<tr>
<form id="update" method="post" action="{{ url_update }}"
      onsubmit="return confirm('Do you really want to delete this ?');">
    {% for k in keys %}
      <td><input name='{{ k }}' value=''></td>
    {% endfor %}
    <td><input type="submit" value="update"></td>
</form>
<td onclick="$.post('{{ url_update_query }}', $('form#update').serializeArray()).done(function(data){ alert(data); })" >confirm</td>
</tr>

{% for row in rows %}
<tr>
  {% for r in row %}
    {% if r is none %}{% set r = '' %}{% endif %}
    <td><input type="text" name='{{ keys[loop.index0] }}' value='{{ r }}' /></td>
  {% endfor %}
</tr>
{% endfor %}
</table>
"""


@route("/")
def index():
    rows = get_conn().execute("show databases;")
    return jinja2.Template(u"""
<ul>
  {% for (db, ) in rows %}
    <li><a href="/{{ db }}">{{ db }}</a></li>
  {% endfor %}
</ul>
    """).render(rows=rows)


@route("/<database_name>")
def database(database_name):
    rows = get_conn(database_name).execute("show tables;")
    return jinja2.Template(u"""
<ul>
  {% for (db, ) in rows %}
    <li><a href="/{{ database_name }}/{{ db }}">{{ db }}</a></li>
  {% endfor %}
</ul>
    """).render(rows=rows, database_name=database_name)


@post("/<database_name>/<table_name>/update")
def update_rows(database_name, table_name):
    if not all([v == '' for  k, v in request.forms.allitems()]):
        get_conn(database_name).execute(build_update(table_name))
    redirect("/%s/%s" % (database_name, table_name))


@post("/<database_name>/<table_name>/update/query")
def update_rows_query(database_name, table_name):
    return build_update(table_name)


@post("/<database_name>/<table_name>/delete")
def delete_rows(database_name, table_name):
    if request.params:
        get_conn(database_name).execute(build_delete(table_name))
    redirect("/%s/%s" % (database_name, table_name))


@route("/<database_name>/<table_name>")
def table(database_name, table_name):
    query = build_select(table_name)
    e = get_conn(database_name).execute(query)
    keys = e.keys()
    rows = e.fetchall()
    url_update = request.path + '/update?' + request.query_string
    url_update_query = request.path + '/update/query?' + request.query_string
    return jinja2.Template(TEMPLATE_TABLE).render(
        database_name=database_name,
        url_update=url_update,
        url_update_query=url_update_query,
        rows=rows,
        keys=keys,
        query=query,
        delete=build_delete(table_name),
        request=request
    )


@click.group()
def cli():
    pass


@cli.command()
@click.argument('url')
@click.option("-p", "--port", default=5001)
def start(url, port):
    global DATABASE_URL
    DATABASE_URL = url
    run(host="0.0.0.0", debug=True, port=port)


if __name__ == "__main__":
    cli()
