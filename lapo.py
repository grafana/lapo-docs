import json
import docs_search_agent
import generate_patch_agent
import git_pr
from rich import print as rprint

from rag import DEFAULT_PLUGIN_TOOLS_REPO_PATH


LAPO_RCATA_SUPREMA = """
[
    Changes(
        original_documentation_chunk=RelatedDocumentationChunk(
            file_name='docusaurus/docs/how-to-guides/data-source-plugins/fetch-data-from-frontend.md',
            chunk_content="= instanceSettings.url!; } async query(options: DataQueryRequest): Promise<DataQueryResponse> { const response = getBackendSrv().fetch<TODO[]>({ // You 
can see above that `this.baseUrl` is set in the constructor // in this example we assume the configured url is // https://jsonplaceholder.typicode.com /// if you inspect 
`this.baseUrl` you'll see the Grafana data proxy url url: `${this.baseUrl}/todos`, }); // backendSrv fetch returns an observable object // we should unwrap with rxjs const 
responseData = await lastValueFrom(response);",
            distance=0.8226978778839111,
            diff="@@ -1,86 +1,86 @@\n import {\n   CoreApp,\n   DataFrame,\n   DataQueryRequest,\n   DataQueryResponse,\n   DataSourceApi,\n   DataSourceInstanceSettings,\n   
FieldType,\n   createDataFrame,\n } from '@grafana/data';\n import { getBackendSrv, isFetchError } from '@grafana/runtime';\n import { DataSourceResponse, defaultQuery, 
MyDataSourceOptions, MyQuery } from './types';\n import { lastValueFrom } from 'rxjs';\n \n export class DataSource extends DataSourceApi<MyQuery, MyDataSourceOptions> {\n-  
baseUrl: string;\n+  proxyUrl: string;"
        ),
        changes_description="Update the documentation to reflect the variable name change from 'baseUrl' to 'proxyUrl' in the example code. Replace all occurrences of 'baseUrl' 
with 'proxyUrl' in the text and code examples since this property has been renamed to better reflect its purpose as a proxy URL."
    )
]
"""


def lapo() -> None:
    pr_diff_hunk = git_pr.get_pr_diff_hunk(
        "https://github.com/grafana/grafana-plugin-examples/pull/482"
    )
    rprint(pr_diff_hunk)

    docs_search_response = docs_search_agent.agent.run_sync(
        docs_search_agent.question(pr_diff_hunk), deps=docs_search_agent.deps()
    )
    rprint("docs search agent result", docs_search_response.data)

    patch_agent_response = generate_patch_agent.generate_pr_agent.run_sync(
        json.dumps([x.model_dump() for x in docs_search_response.data]),
        deps=generate_patch_agent.Deps(docs_repo_path=DEFAULT_PLUGIN_TOOLS_REPO_PATH),
    )
    rprint(patch_agent_response)

    rprint(patch_agent_response.data)
    with open("test.patch", "w") as f:
        print("writing patch to test.patch")
        f.write(patch_agent_response.data.patch_diff)


if __name__ == "__main__":
    lapo()
