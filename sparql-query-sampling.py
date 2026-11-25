from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd

endpoint = "https://query.knowledgepixels.com/repo/full"

query = """
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix np: <http://www.nanopub.org/nschema#>
prefix npa: <http://purl.org/nanopub/admin/>
prefix npx: <http://purl.org/nanopub/x/>
prefix nt: <https://w3id.org/np/o/ntemplate/>
prefix bio: <https://w3id.org/spaces/biodiversity/r/ontology/>
prefix biolink: <https://w3id.org/biolink/vocab/>
prefix kpxl: <https://w3id.org/kpxl/biodiv/terms/>

SELECT DISTINCT
  ?np ?label ?timepoint ?coordinates
  ?ecosystem ?ecosystem_label
  ?material ?material_label
  ?purpose ?purpose_label
WHERE {

  # only NPs made from the sampling template (both versions)
  VALUES ?template {
    <https://w3id.org/np/RAQk2rmXkH7-AmWaQ4iyYY9VRAvM8a1hJGIEniWSDsgrU/template>
    <https://w3id.org/np/RAFIi2Ws-FYlGAnPFyGvmTtzzhSwOzjj6PYnj_RwqMrzc/template>
  }

  graph npa:graph {
    ?np npa:hasValidSignatureForPublicKey ?pubkey .
    filter not exists { ?npx npx:invalidates ?np ; npa:hasValidSignatureForPublicKey ?pubkey . }
    ?np np:hasAssertion ?assertion .
    ?np np:hasPublicationInfo ?pubinfo .
    ?np npx:introduces ?sample .
    optional { ?np rdfs:label ?label }
  }

  graph ?pubinfo {
    ?np nt:wasCreatedFromTemplate ?template .
  }

  graph ?assertion {
    ?sample a bio:Sample .
    optional { ?sample biolink:timepoint ?timepoint }
    optional {
      ?sample bio:hasSamplingLocation ?loc .
      optional { ?loc kpxl:hasLocationCoordinates ?coordinates }
      optional { ?loc bio:hasEcosystem ?ecosystem }
    }
    optional { ?sample bio:hasSampleMaterial ?mat . ?mat a ?material }
    optional { ?sample bio:hasSamplingPurpose ?purpose }
  }

  # labels stored in pubinfo
  optional { graph ?pubinfo { ?ecosystem nt:hasLabelFromApi ?ecosystem_label } }
  optional { graph ?pubinfo { ?material nt:hasLabelFromApi ?material_label } }
  optional { graph ?pubinfo { ?purpose nt:hasLabelFromApi ?purpose_label } }
}
"""

# the columns we want in the CSV (same names as the variables in SELECT)
columns = [
    "np",
    "label",
    "timepoint",
    "coordinates",
    "ecosystem",
    "ecosystem_label",
    "material",
    "material_label",
    "purpose",
    "purpose_label",
]

sparql = SPARQLWrapper(endpoint)
sparql.setQuery(query)
sparql.setReturnFormat(JSON)

results = sparql.query().convert()

rows = []

for result in results["results"]["bindings"]:
    row = {}
    for column in columns:
        row[column] = result.get(column, {}).get("value")
    rows.append(row)

df = pd.DataFrame(rows)

# no drop_duplicates here: one NP can have several rows
# (e.g. two sampling purposes) - we handle that in the formatting step
print(f"{len(df)} rows, {df['np'].nunique()} distinct nanopublications")

df.to_csv("sparql-query-sampling.csv", index=False)
