# Session 8: Model Context Protocol (MCP)

### [Quicklinks]()


| Session Sheet                                                             | Recording | Slides | Repo          | Homework | Feedback |
| ------------------------------------------------------------------------- | --------- | ------ | ------------- | -------- | -------- |
| [MCP Servers](../00_Docs/Session_Sheets/17_MCP_Servers_and_A2A/README.md) |           |        | You are here! |          |          |


## Useful Resources

**MCP (Model Context Protocol)**

- [MCP Official Docs](https://modelcontextprotocol.io/) — Spec, tutorials, and guides
- [MCP-UI](https://mcpui.dev/) — Official standard for interactive UI in MCP
- [MCP Auth Guide (Auth0)](https://auth0.com/blog/mcp-specs-update-all-about-auth/) — Deep dive into MCP auth spec updates

## Main Assignment

In this session, you will build an MCP server with OAuth authentication — a cat
shop application that exposes tools for browsing products, managing a cart, and
checking out.

The main entry point is:

```text
server.py
```

The server implementation lives in:

```text
app/
```

Available MCP tools:

- `list_products`
- `get_product`
- `add_to_cart`
- `view_cart`
- `remove_from_cart`
- `checkout`

## Setup

From this folder:

```bash
uv sync
```

Copy the example env file and fill in your OpenAI API key:

```bash
cp .env.example .env
```

## Running the MCP Server

Run the server locally:

```bash
uv run server.py
```

The server starts on `http://localhost:8000`.

### Expose the server with ngrok

In a separate terminal, start an ngrok tunnel:

```bash
ngrok http 8000
```

Copy the ngrok forwarding URL (e.g. `https://xxxx-xx-xx-xx-xx.ngrok-free.app`) and
restart the server with it:

```bash
ISSUER_URL=https://xxxx-xx-xx-xx-xx.ngrok-free.app uv run server.py
```

> **Note:** The `ISSUER_URL` must match the public URL clients use to reach the
> server, otherwise OAuth authentication will fail.

## Outline

### Breakout Room #1

- Set up the MCP server with OAuth and the product database
- Explore the MCP tools: `list_products`, `get_product`, `add_to_cart`, `view_cart`, `remove_from_cart`, `checkout`

### Breakout Room #2

- Connect an MCP client to the server
- Build an end-to-end interaction flow using the MCP tools

## Ship

The completed MCP server and client integration!

### Deliverables

- A short Loom of either:
  - the MCP server you built and a demo of the client interacting with it; or
  - the notebook you created for the Advanced Build

## Share

Make a social media post about your final application!

### Deliverables

- Make a post on any social media platform about what you built!

Here's a template to get you started:

```
🚀 Exciting News! 🚀

I am thrilled to announce that I have just built and shipped an MCP server with OAuth authentication! 🎉🤖

🔍 Three Key Takeaways:
1️⃣
2️⃣
3️⃣

Let's continue pushing the boundaries of what's possible in the world of AI and tool integration. Here's to many more innovations! 🚀
Shout out to @AIMakerspace !

#MCP #ModelContextProtocol #OAuth #Innovation #AI #TechMilestone

Feel free to reach out if you're curious or would like to collaborate on similar projects! 🤝🔥
```

## Submitting Your Homework [OPTIONAL]

Follow these steps to prepare and submit your homework assignment:

1. Review the MCP server code in `server.py` and the `app/` directory
2. Run the MCP server locally using `uv run server.py`
3. Connect to the server using an MCP client (e.g., Claude Desktop, or a custom client)
4. Test all available tools: browsing products, adding to cart, viewing cart, removing items, and checkout
5. Record a Loom video reviewing what you have learned from this session

## Questions

### Question #1

Why is OAuth important for MCP servers, and what security considerations should you keep in mind when exposing tools to AI clients?

#### Answer

OAuth is important for MCP serviers because MCP tools are not read only APIs, rather they are able to perform real actions on behalf of the a user. In the Cat Shop server, tools like add_to_cart, remove_from_cart, and checkout change application state and can create orders. If a server is reachable over the network without authetnication, anyone who discovers the endpoint could invoke those tools directly.   

OAuth solves this by requiring clients to authenticate and obtain access tokens before calling protected MCP endpoints i.e. unauthenticated requests returns 401 unauthorized. Once user goes through OAuth flow discovery, user sign in on the log in page > token exchange occurs and authorizes MCP requets. 

OAuth also provides identity and scoped access (read/write) so the server can enforce permissions instead of trusting every caller. 

When exposting MCP tooks to AI clients, serveral security considerations matter:

1. Public exposure increases attack surface. Using ngrok makes the server reachable from the public internet, so authentication is essential. without it, tool endpoints would be open to abuse.
2. AI clients can invoke tools automatically. LLM may call tools based on user prompts so tools must be designed carefully i.e. checkout should only run when the user clearly intends to place an order, and the server should validate user identity and cart state server side
3. Token and URL correctness matter. ISSUER_URL must match the public URL clients use. if not, oauth redirects and token valiation can fail or behave insecurely
4. Use HTTPS for remote access.
5. Scope and least privilege. Clients should receive only the scopes they need. broader scopes increase damange if a token is leaded or misused.

OAuth turns a publicly reachable MCP server from an open remote control API into authenticated user aware system - which is necessary when AI clients can call powerful tools over the network. 

Question #2

What is Streamable HTTP transport in MCP, and why might you expose a server publicly with OAuth instead of using a local stdio connection?

#### Answer

Streamable HTTP is an MCP transport that communicates over HTTP instead of local process pipes. In this project, the server runs with mcp.run(transport='streamable-http") and exposes the MCP endpoints at /mcp. Clients send MCP requests as HTTP messages (for example, POST /mcp, GET /mcp), and the connection supports streaming session behavior rather than a single request/response exchange.  For example, in my server logs, I saw session creation, tool calls (CallToolRequest), and session termination which reflects this HTTP-based, session oriented transport model. 

By contrast, local stdio connection transport runs the MCP server as a local subprocess and communicates throough stdin/stdout. That works well when the MCP client and server are on the same machine i.e. desktop app launching a local tool server - but does not naturally support remote access over a network.

I would expose a server publicly with OAuth instead of using a local stdio connection for the following reasons

1. client is remote. My langchain client connected to the server through an ngrok URL as the client and server were not tied to the same local process boundary
2. need shared or multi client access. A public HTTP endpoint allows multiple clients or teammates to connect to the same MCP server, which is difficult with stdio's one local process model
3. need to integrate with cloud or agent systems. remote agents, hosted apps or browser based clients typically need a network protocol (HTTP) rather than local pipes
4. security is mandatory. once a server is reachable from the internet, stdio's implicit local trust is not sufficient. OAuth provides authentication, authorization scopes, and token based access control before tool execution

In this session using streamable HTTP + ngrok + OAuth enabled a realistic production like pattern: a remotely reachable MCP server where only authenticated clients can invoke tools. stdio would have been easier for local only use but would not support remote, authenticated client server architecture needed for this cat shop project. 

## Activity 1: Extend the MCP Server

Add at least one new tool to the cat shop MCP server (e.g., `search_products`, `update_cart_quantity`, or `get_order_history`). Ensure the new tool integrates properly with the existing database and OAuth authentication. Demo the new tool through an MCP client and include it in your Loom video.

## Advanced Activity: Build a Custom MCP Client

Build a custom MCP client that connects to the cat shop server over Streamable HTTP, authenticates via OAuth, and orchestrates a multi-step shopping flow (browse → add to cart → checkout). Compare the developer experience of MCP-based tool integration vs. traditional REST API calls.

Include your findings and a demo in your Loom video.