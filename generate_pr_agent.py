from typing import TypedDict, List, Optional, Dict
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
import os
possible_changes = """[
        {
            'original_documentation_chunks': {
                'file_name': 'how-to-guides/data-source-plugins/fetch-data-from-frontend.md',
                'chunk_content': "= instanceSettings.url!; } async query(options: DataQueryRequest): Promise<DataQueryResponse> {\n  const response = getBackendSrv().fetch<TODO[]>({\n    // You can see above that `this.baseUrl` is set in the constructor\n
// in this example we assume the configured url is\n    // https://jsonplaceholder.typicode.com\n    /// if you inspect `this.baseUrl` you'll see the Grafana data proxy url\n    url: `${this.baseUrl}/todos`,\n  });\n  // backendSrv fetch returns an
observable object\n  // we should unwrap with rxjs\n  const responseData = await lastValueFrom(response);\n  const todos = responseData.data;\n\n  // we'll return the same todos for all queries in this example\n  // in a real data source each target should
fetch the data\n  // as necessary.\n  const data: PartialDataFrame[] = options.targets.map((target) => {\n    return {\n      refId: target.refId,\n      fields: [\n        {\n          name: 'Id',\n          type: FieldType.number,\n          values:
todos.map((todo) => todo.id),\n        },\n        {\n          name: 'Title',\n          type: FieldType.string,\n          values: todos.map((todo) => todo.title),\n        },\n      ],\n    };\n  });\n\n  return { data };\n}\n\nasync testDatasource()
{\n  return {\n    status: 'success',\n    message: 'Success',\n  };\n}\n}\n```\n\n:: note\nThe user must first configure the data source in the configuration page before the data source can query the endpoint via the data source. If the data source is not
configured, the data proxy won't know which endpoint to send the request to.\n::\n\n## How to use the data proxy in data source plugins with a custom configuration page\n\nIf you don't want to use the `DataSourceHttpSettings` component and instead create
your own configuration page you will have to do some additional setup",
                'distance': 0.819951593875885
            },
            'changes_description': "Update references to 'this.baseUrl' and reflect the new usage of 'proxyUrl' according to the code changes."
        }
    ]
)"""


DEFAULT_DOCS_PATH = os.path.join("..", "plugin-tools", "docusaurus", "docs")


class OriginalDocumentationChunks(TypedDict):
    file_name: str
    chunk_content: str
    distance: float


class DocumentationChange(TypedDict):
    original_documentation_chunks: OriginalDocumentationChunks
    changes_description: str


class DocumentationChangeList(TypedDict):
    data: List[DocumentationChange]


class PullRequestContent(TypedDict):
    file: str
    start_line: int
    end_line: int
    patch_diff: str


class DocumentContent(TypedDict):
    file_path: str
    content: str
    exists: bool


generate_pr_agent = Agent(
    GeminiModel('gemini-2.0-flash'),
    deps_type=None,
    system_prompt=(
        'You are an expert system on generating pull requests for documentation based on code changes',
        'You will analyze the code change (diff), analyze the related document content. Then you will'
        'If the code changes affect the document in a way that it requires changes then you will generate a pull request',
        'Do not change the document in any other way, changes must come purely from the related code changes'
        'Generate the patch_diff in a git compatible format'
        'use the `get_document` tool to get the full content of a document.'
    ),
    result_type=List[DocumentationChange],
)


@generate_pr_agent.tool
async def get_document(ctx: RunContext[str], file_name: str) -> DocumentContent:
    print("get_document", file_name)
    # check if file exists in DEFAULT_DOCS_PATH
    if not os.path.exists(os.path.join(DEFAULT_DOCS_PATH, file_name)):
        return {"file_path": file_name, "content": "", "exists": False}
    with open(os.path.join(DEFAULT_DOCS_PATH, file_name), "r") as f:
        return {"file_path": file_name, "content": f.read(), "exists": True}


if __name__ == "__main__":
    pass
