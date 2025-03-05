from typing import TypedDict, List
from rich import print as rprint
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.gemini import GeminiModel
import os
import tempfile
import subprocess
import logfire
from patch_validator_agent import validate_patch_agent


def scrubbing_callback(m: logfire.ScrubMatch):
    if (
        m.path == ('message', 'prompt')
        and m.pattern_match.group(0) == 'credential'
    ):
        return m.value

    if (
        m.path == ('attributes', 'prompt')
        and m.pattern_match.group(0) == 'credential'
    ):
        return m.value


logfire.configure(scrubbing=logfire.ScrubbingOptions(callback=scrubbing_callback))

possible_changes = """
AgentRunResult(
    data=[
        Changes(
            original_documentation_chunks=RelatedDocumentationChunk(
                file_name='how-to-guides/data-source-plugins/convert-a-frontend-datasource-to-backend.md',
                chunk_content='context.Context, _ *backend.CheckHealthRequest) (*backend.CheckHealthResult, error) { resp, err := d.httpClient.Get(d.settings.URL + "/v1/users") if err != nil { // Log the error here return &backend.CheckHealthResult{
Status: backend.HealthStatusError, Message: "request error", }, nil } if resp.StatusCode != http.StatusOK { return &backend.CheckHealthResult{ Status: backend.HealthStatusError, Message: fmt.Sprintf("got response code %d", resp.StatusCode), }, nil } return
&backend.CheckHealthResult{ Status: backend.HealthStatusOk, Message: "Data source is working", }, nil } ``` :::note This example covers an HTTP-only data source. So, if your data source requires a database connection, you can use the Go client for the
database and execute a simple query like `SELECT 1` or a `ping` function. :::\n\n### Query\n\nThe next step is to move the query logic. This will significantly vary depending on how the plugin queries the data source and transforms the response into
[frames](../../key-concepts/data-frames). In this guide, you\'ll see how to migrate a simple example.\n\nOur data source is returning a JSON object with a list of `datapoints` when hitting the endpoint `/metrics`. The frontend `query` method transforms
those `datapoints` into frames:\n\n```typescript title="src/DataSource.ts"\nexport class DataSource extends DataSourceApi<MyQuery, MyDataSourceOptions> {\n  async query(options: DataQueryRequest<MyQuery>): Promise<DataQueryResponse> {\n    const response =
await lastValueFrom(\n      getBackendSrv().fetch<DataSourceResponse>({\n        url: `${this.url}/metrics`,\n        method: \'GET\',\n      })\n    );\n\n    const df: DataFrame = {\n      length: response.data.datapoints.length,\n      refId:
options.targets[0].refId,\n      fields: [\n        { name: \'Time\', values: [], type: FieldType.time, config: {} },\n        {\n          name: \'Value\',\n          values: [],\n          type: FieldType.number,\n          config: {},\n        },\n
],\n    };\n\n    response.data.datapoints.forEach((datapoint: any) => {\n      df.fields[0].values.push(datapoint.time);\n      df.fields[1].values.push(datapoint.value);\n    });\n\n    return {\n      data: [df]\n',
                distance=0.7836843132972717,
                diff="\n@@ -1,86 +1,86 @@\n import {\n   CoreApp,\n   DataFrame,\n   DataQueryRequest,\n   DataQueryResponse,\n   DataSourceApi,\n   DataSourceInstanceSettings,\n   FieldType,\n   createDataFrame,\n } from '@grafana/data';\n import {
getBackendSrv, isFetchError } from '@grafana/runtime';\n import { DataSourceResponse, defaultQuery, MyDataSourceOptions, MyQuery } from './types';\n import { lastValueFrom } from 'rxjs';\n \n export class DataSource extends DataSourceApi<MyQuery,
MyDataSourceOptions> {\n-  baseUrl: string;\n+  proxyUrl: string;\n \n   constructor(instanceSettings: DataSourceInstanceSettings<MyDataSourceOptions>) {\n     super(instanceSettings);\n \n-    this.baseUrl = instanceSettings.url!;\n+    this.proxyUrl =
instanceSettings.url!;\n   }\n \n   getDefaultQuery(_: CoreApp): Partial<MyQuery> {\n     return defaultQuery;\n   }\n \n   filterQuery(query: MyQuery): boolean {\n     return !!query.queryText;\n   }\n \n   async query(options: DataQueryRequest<MyQuery>):
Promise<DataQueryResponse> {\n     const { range } = options;\n     const from = range!.from.valueOf();\n     const to = range!.to.valueOf();\n \n     // Return a constant for each query.\n     const data = options.targets.map((target) => {\n-      const
df: DataFrame = createDataFrame({        \n+      const df: DataFrame = createDataFrame({\n         refId: target.refId,\n         fields: [\n           { name: 'Time', values: [from, to], type: FieldType.time, config: {} },\n           { name: 'Value',
values: [target.constant, target.constant], type: FieldType.number, config: {} },\n         ],\n       });\n       return df;\n     });\n \n     return { data };\n   }\n \n   async request(url: string, params?: string) {\n     const response =
getBackendSrv().fetch<DataSourceResponse>({\n-      url: `${this.baseUrl}${url}${params?.length ? `?${params}` : ''}`,\n+      url: `${this.proxyUrl}${url}${params?.length ? `?${params}` : ''}`,\n     });\n     return lastValueFrom(response);\n   }\n \n
/**\n    * Checks whether we can connect to the API.\n    */\n   async testDatasource() {\n     const defaultErrorMessage = 'Cannot connect to API';\n \n     try {\n       const response = await this.request('/health');\n       if (response.status === 200)
{\n         return {\n           status: 'success',\n           message: 'Success',\n         };\n       } else {\n         return {\n           status: 'error',\n           message: response.statusText ? response.statusText : defaultErrorMessage,\n
};\n       }\n     } catch (err) {\n       let message = defaultErrorMessage;\n       if (typeof err === 'string') {\n         message = err;\n       } else if (isFetchError(err)) {\n         message = `Fetch error: ${err.data.error?.message ??
err.statusText}`;\n       }\n       return {\n         status: 'error',\n"
            ),
            changes_description="Update the documentation snippet to reference 'this.proxyUrl' instead of 'this.url' or 'this.baseUrl'. Ensure that any code examples reflect the renamed property."
        ),
        Changes(
            original_documentation_chunks=RelatedDocumentationChunk(
                file_name='e2e-test-a-plugin/test-a-data-source-plugin/configuration-editor.md',
                chunk_content='async ({ createDataSourceConfigPage, readProvisionedDataSource, selectors, }) => {\n  const ds = await readProvisionedDataSource({ fileName: \'datasources.yml\' });\n  const configPage = await createDataSourceConfigPage({
type: ds.type });\n  const healthCheckPath = `${selectors.apis.DataSource.proxy(configPage.datasource.uid)}/test`;\n\n  await page.route(healthCheckPath, async (route) =>\n    await route.fulfill({\n      status: 200,\n      body: \'OK\'\n    })\n\n  //
construct a custom health check url using the Grafana data source proxy\n  const healthCheckPath = `${selectors.apis.DataSource.proxy(\n    configPage.datasource.uid,\n    configPage.datasource.id.toString()\n  )}/third-party-service-path`;\n\n  await
expect(configPage.saveAndTest({ path: healthCheckPath })).toBeOK();\n});\n```  \n\nAdditionally, you can assert that a success alert box is displayed on the page.\n\n```ts title="configurationEditor.spec.ts"\ntest(\'"Save & test" should display success
alert box when config is valid\', async ({ createDataSourceConfigPage, readProvisionedDataSource, page, }) => {\n  const ds = await readProvisionedDataSource({ fileName: \'datasources.yml\' });\n  const configPage = await createDataSourceConfigPage({ type:
ds.type });\n\n  // construct a custom health check url using the Grafana data source proxy\n  const healthCheckPath = `${selectors.apis.DataSource.proxy(\n    configPage.datasource.uid,\n    configPage.datasource.id.toString()\n
)}/third-party-service-path`;\n\n  await page.route(healthCheckPath, async (route) =>\n    await route.fulfill({\n      status: 200,\n      body: \'OK\',\n    })\n  );\n\n  await expect(configPage.saveAndTest({ path: healthCheckPath })).toBeOK();\n  await
expect(configPage).toHaveAlert(\'success\');\n});\n```\n\n### Testing a provisioned data source\n\nSometimes you may want to open the configuration editor for an already existing data source instance to verify configuration work as
expected.\n\n```ts\ntest(\'provisioned data source with valid credentials should return a 200 status code\', async ({ readProvisionedDataSource, gotoDataSourceConfigPage, }) => {\n  const datasource = await readProvisionedDataSource({ fileName:
\'datasources.yml\' });\n  const configPage = await gotoDataSourceConfigPage(datasource.uid);\n\n  await expect(configPage.saveAndTest()).toBeOK();\n});\n```',
                distance=0.8148545026779175,
                diff="\n@@ -1,86 +1,86 @@\n import {\n   CoreApp,\n   DataFrame,\n   DataQueryRequest,\n   DataQueryResponse,\n   DataSourceApi,\n   DataSourceInstanceSettings,\n   FieldType,\n   createDataFrame,\n } from '@grafana/data';\n import {
getBackendSrv, isFetchError } from '@grafana/runtime';\n import { DataSourceResponse, defaultQuery, MyDataSourceOptions, MyQuery } from './types';\n import { lastValueFrom } from 'rxjs';\n \n export class DataSource extends DataSourceApi<MyQuery,
MyDataSourceOptions> {\n-  baseUrl: string;\n+  proxyUrl: string;\n \n   constructor(instanceSettings: DataSourceInstanceSettings<MyDataSourceOptions>) {\n     super(instanceSettings);\n \n-    this.baseUrl = instanceSettings.url!;\n+    this.proxyUrl =
instanceSettings.url!;\n   }\n \n   getDefaultQuery(_: CoreApp): Partial<MyQuery> {\n     return defaultQuery;\n   }\n \n   filterQuery(query: MyQuery): boolean {\n     return !!query.queryText;\n   }\n \n   async query(options: DataQueryRequest<MyQuery>):
Promise<DataQueryResponse> {\n     const { range } = options;\n     const from = range!.from.valueOf();\n     const to = range!.to.valueOf();\n \n     // Return a constant for each query.\n     const data = options.targets.map((target) => {\n-      const
df: DataFrame = createDataFrame({        \n+      const df: DataFrame = createDataFrame({\n         refId: target.refId,\n         fields: [\n           { name: 'Time', values: [from, to], type: FieldType.time, config: {} },\n           { name: 'Value',
values: [target.constant, target.constant], type: FieldType.number, config: {} },\n         ],\n       });\n       return df;\n     });\n \n     return { data };\n   }\n \n   async request(url: string, params?: string) {\n     const response =
getBackendSrv().fetch<DataSourceResponse>({\n-      url: `${this.baseUrl}${url}${params?.length ? `?${params}` : ''}`,\n+      url: `${this.proxyUrl}${url}${params?.length ? `?${params}` : ''}`,\n     });\n     return lastValueFrom(response);\n   }\n \n
/**\n    * Checks whether we can connect to the API.\n    */\n   async testDatasource() {\n     const defaultErrorMessage = 'Cannot connect to API';\n \n     try {\n       const response = await this.request('/health');\n       if (response.status === 200)
{\n         return {\n           status: 'success',\n           message: 'Success',\n         };\n       } else {\n         return {\n           status: 'error',\n           message: response.statusText ? response.statusText : defaultErrorMessage,\n
};\n       }\n     } catch (err) {\n       let message = defaultErrorMessage;\n       if (typeof err === 'string') {\n         message = err;\n       } else if (isFetchError(err)) {\n         message = `Fetch error: ${err.data.error?.message ??
err.statusText}`;\n       }\n       return {\n         status: 'error',\n"
            ),
            changes_description="No direct references to 'baseUrl' in the snippet, but ensure references are consistent with 'proxyUrl' if explaining the data source proxy usage."
        ),
        Changes(
            original_documentation_chunks=RelatedDocumentationChunk(
                file_name='how-to-guides/data-source-plugins/fetch-data-from-frontend.md',
                chunk_content="= instanceSettings.url!;\n  }\n\n  async query(options: DataQueryRequest): Promise<DataQueryResponse> {\n    const response = getBackendSrv().fetch<TODO[]>({\n      // You can see above that `this.baseUrl` is set in the
constructor\n      // in this example we assume the configured url is\n      // https://jsonplaceholder.typicode.com\n      /// if you inspect `this.baseUrl` you'll see the Grafana data proxy url\n      url: `${this.baseUrl}/todos`,\n    });\n\n    //
backendSrv fetch returns an observable object\n    // we should unwrap with rxjs\n    const responseData = await lastValueFrom(response);\n    const todos = responseData.data;\n\n    // we'll return the same todos for all queries in this example\n    // in
a real data source each target should fetch the data\n    // as necessary.\n    const data: PartialDataFrame[] = options.targets.map((target) => {\n      return {\n        refId: target.refId,\n        fields: [\n          { name: 'Id', type:
FieldType.number, values: todos.map((todo) => todo.id) },\n          { name: 'Title', type: FieldType.string, values: todos.map((todo) => todo.title) },\n        ],\n      };\n    });\n\n    return { data };\n  }\n\n  async testDatasource() {\n    return
{\n      status: 'success',\n      message: 'Success',\n    };\n  }\n}\n```\n\n:: note\nThe user must first configure the data source in the configuration page before the data source can query the endpoint via the data source. If the data source is not
configured, the data proxy won't know which endpoint to send the request to.\n::\n\n## How to use the data proxy in data source plugins with a custom configuration page\n\nIf you don't want to use the `DataSourceHttpSettings` component and instead create
your own configuration page you will have to do some additional setup",
                distance=0.819951593875885,
                diff="\n@@ -1,86 +1,86 @@\n import {\n   CoreApp,\n   DataFrame,\n   DataQueryRequest,\n   DataQueryResponse,\n   DataSourceApi,\n   DataSourceInstanceSettings,\n   FieldType,\n   createDataFrame,\n } from '@grafana/data';\n import {
getBackendSrv, isFetchError } from '@grafana/runtime';\n import { DataSourceResponse, defaultQuery, MyDataSourceOptions, MyQuery } from './types';\n import { lastValueFrom } from 'rxjs';\n \n export class DataSource extends DataSourceApi<MyQuery,
MyDataSourceOptions> {\n-  baseUrl: string;\n+  proxyUrl: string;\n \n   constructor(instanceSettings: DataSourceInstanceSettings<MyDataSourceOptions>) {\n     super(instanceSettings);\n \n-    this.baseUrl = instanceSettings.url!;\n+    this.proxyUrl =
instanceSettings.url!;\n   }\n \n   getDefaultQuery(_: CoreApp): Partial<MyQuery> {\n     return defaultQuery;\n   }\n \n   filterQuery(query: MyQuery): boolean {\n     return !!query.queryText;\n   }\n \n   async query(options: DataQueryRequest<MyQuery>):
Promise<DataQueryResponse> {\n     const { range } = options;\n     const from = range!.from.valueOf();\n     const to = range!.to.valueOf();\n \n     // Return a constant for each query.\n     const data = options.targets.map((target) => {\n-      const
df: DataFrame = createDataFrame({        \n+      const df: DataFrame = createDataFrame({\n         refId: target.refId,\n         fields: [\n           { name: 'Time', values: [from, to], type: FieldType.time, config: {} },\n           { name: 'Value',
values: [target.constant, target.constant], type: FieldType.number, config: {} },\n         ],\n       });\n       return df;\n     });\n \n     return { data };\n   }\n \n   async request(url: string, params?: string) {\n     const response =
getBackendSrv().fetch<DataSourceResponse>({\n-      url: `${this.baseUrl}${url}${params?.length ? `?${params}` : ''}`,\n+      url: `${this.proxyUrl}${url}${params?.length ? `?${params}` : ''}`,\n     });\n     return lastValueFrom(response);\n   }\n \n
/**\n    * Checks whether we can connect to the API.\n    */\n   async testDatasource() {\n     const defaultErrorMessage = 'Cannot connect to API';\n \n     try {\n       const response = await this.request('/health');\n       if (response.status === 200)
{\n         return {\n           status: 'success',\n           message: 'Success',\n         };\n       } else {\n         return {\n           status: 'error',\n           message: response.statusText ? response.statusText : defaultErrorMessage,\n
};\n       }\n     } catch (err) {\n       let message = defaultErrorMessage;\n       if (typeof err === 'string') {\n         message = err;\n       } else if (isFetchError(err)) {\n         message = `Fetch error: ${err.data.error?.message ??
err.statusText}`;\n       }\n       return {\n         status: 'error',\n"
            ),
            changes_description="Replace mentions of 'this.baseUrl' with 'this.proxyUrl' in the code snippet and commentary, aligning with the new property name."
        )
    ]
)

"""


DEFAULT_DOCS_PATH = os.path.join("..", "plugin-tools", "docusaurus", "docs")


class PullRequestContent(BaseModel):
    reasoning: str = Field(
        description="The reason behind the pull request changes",
    )
    patch_diff: str = Field(
        description="The patch diff for the pull request",
    )


class DocumentContent(TypedDict):
    file_path: str
    content: str
    exists: bool


generate_pr_agent = Agent(
    GeminiModel('gemini-2.0-flash'),
    retries=3,
    deps_type=None,
    system_prompt=(
        'You are an expert system on generating pull requests for documentation based on code changes',
        'You will analyze the presented list of POSSIBLE affected documents by a code change (diff)'
        'think carefully if the code change (diff) affects the document related  content'
        'you can use the full document content to better decide'
        'If the code changes affect the document in a way that it requires changes then you will generate a pull request',
        'to update the document.'
        'you must only change the content of the document that is affected by the code change (diff)',
        'Generate the patch for git if multiple patches for multiple files are generated, concat them all in one'
        'use the `get_document` tool to get the full content of a document.'
        'use the `validate_patch` tool to validate the generated patch. it should return OK if the patch is valid'
    ),
    result_type=PullRequestContent,
)


@generate_pr_agent.tool(retries=5)
async def get_document(ctx: RunContext[str], file_name: str) -> DocumentContent:
    print("get_document", file_name)
    # check if file exists in DEFAULT_DOCS_PATH
    if not os.path.exists(os.path.join(DEFAULT_DOCS_PATH, file_name)):
        return {"file_path": file_name, "content": "", "exists": False}
    with open(os.path.join(DEFAULT_DOCS_PATH, file_name), "r") as f:
        return {"file_path": file_name, "content": f.read(), "exists": True}


@generate_pr_agent.tool(retries=10)
async def validate_patch(ctx: RunContext[str], patch: str) -> str:
    print("validate_patch", patch)
    # write patch to /home/test.patch
    with open("/home/academo/test.patch", "w") as f:
        print("writing patch to /home/academo/test.patch")
        f.write(patch)

    # store patch in a temporal file
    with tempfile.NamedTemporaryFile("w") as f:
        f.write(patch)
        f.flush()
        print("patch", f.name)
        try:
            subprocess.check_output(["git", "apply", "--check", f.name],
                                    cwd=DEFAULT_DOCS_PATH).decode("utf-8")
            return "OK"
        except Exception as e:
            print("error with patch, checking with agent", e.output)
            r = await validate_patch_agent.run(
                'determine why this patch is invalid\n\n' + patch
            )
            print("patch validator says", r.data)
            if "PATCH_VALID" in r.data:
                return "OK"
            raise ModelRetry(r.data)

if __name__ == "__main__":
    response = generate_pr_agent.run_sync(
        possible_changes,
    )
    rprint(response)
    pass
