{{ subject }}

{% if body %}{{ body }}
{% endif %}

{% if breaking_change %}BREAKING CHANGE: {{ breaking_change }}
{% endif %}

{% if issues %}{{ issues }}
{% endif %} 