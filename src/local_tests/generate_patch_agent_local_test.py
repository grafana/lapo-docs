from src.tools.search_replace.search_replace_apply import generate_git_patch_from_search_replace
from src.rag.rag import DEFAULT_PLUGIN_TOOLS_REPO_PATH
from src.agents import docs_search_agent
from src.agents import generate_patch_agent
import sys
import logging
import json
import textwrap
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))


logger = logging.getLogger(__name__)


def main() -> None:
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    json_data = textwrap.dedent("""
            [
                Changes(
                    original_documentation_chunk=RelatedDocumentationChunk(
                        file_name='docusaurus/docs/how-to-guides/data-source-plugins/fetch-data-from-frontend.md',
                        chunk_content='Once the user has entered the endpoint details in the data source configuration page, you can query the data proxy URL that is passed in the data source instance
            settings (`DataSourceInstanceSettings.url`).\n\n```typescript title="src/dataSource.ts"\nimport {\n  DataQueryRequest,\n  DataQueryResponse,\n  DataSourceApi,\n  DataSourceInstanceSettings,\n
            FieldType,\n  PartialDataFrame,\n} from \'@grafana/data\';\nimport { getBackendSrv } from \'@grafana/runtime\';\nimport { lastValueFrom } from \'rxjs\';\n\ntype TODO = {\n  title: string;\n
            id: number;\n};\n\nexport class DataSource extends DataSourceApi {\n  baseUrl: string;\n  constructor(instanceSettings: DataSourceInstanceSettings) {\n    super(instanceSettings);\n    //
            notice we are storing the URL from the instanceSettings\n    this.baseUrl = instanceSettings.url!;\n  }\n',
                        distance=0.4344494640827179,
                        diff="@@ -1,86 +1,86 @@\n import {\n   CoreApp,\n   DataFrame,\n   DataQueryRequest,\n   DataQueryResponse,\n   DataSourceApi,\n   DataSourceInstanceSettings,\n   FieldType,\n
            createDataFrame,\n } from '@grafana/data';\n import { getBackendSrv, isFetchError } from '@grafana/runtime';\n import { DataSourceResponse, defaultQuery, MyDataSourceOptions, MyQuery } from
            './types';\n import { lastValueFrom } from 'rxjs';\n \n export class DataSource extends DataSourceApi<MyQuery, MyDataSourceOptions> {\n-  baseUrl: string;\n+  proxyUrl: string;\n \n
            constructor(instanceSettings: DataSourceInstanceSettings<MyDataSourceOptions>) {\n     super(instanceSettings);\n \n-    this.baseUrl = instanceSettings.url!;\n+    this.proxyUrl =
            instanceSettings.url!;\n   }"
                    ),
                    changes_description='Update the code example to use `proxyUrl` instead of `baseUrl` to align with the changes in the source code. The variable name has been changed from `baseUrl` to
            `proxyUrl` to better reflect its purpose as a proxy URL.'
                )
            ]
            """)

    patch_agent_response = generate_patch_agent.generate_patch_agent.run_sync(
        json_data, deps=generate_patch_agent.Deps(docs_repo_path=DEFAULT_PLUGIN_TOOLS_REPO_PATH)
    )

    patch = patch_agent_response.data.patch_diff
    logger.info("------")
    logger.info(patch)
    logger.info("------")
    logger.info(generate_git_patch_from_search_replace(DEFAULT_PLUGIN_TOOLS_REPO_PATH, patch))


if __name__ == "__main__":
    main()
