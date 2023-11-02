{% extends "html.tpl" %}
<style>
table {text-align: center;}
table thead th {text-align: center;}
</style>
{% block table %}
<h1>{{ table_title|default("") }}</h1>
{{ super() }}
{% endblock table %}
