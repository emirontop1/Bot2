-- main.lu
local ok_socket, socket = pcall(require, "socket")
local ok_ltn12, ltn12 = pcall(require, "ltn12")
local ok_dkjson, json = pcall(require, "dkjson")
local ok_http, http = pcall(require, "socket.http") -- optional, bazı kurulumlarda ayrı require gerekebilir

if not ok_socket then
    io.stderr:write("Missing module 'socket'. Please install 'luasocket' via luarocks.\\n")
    os.exit(1)
end
if not ok_dkjson then
    io.stderr:write("Missing module 'dkjson'. Please install 'dkjson' via luarocks.\\n")
    os.exit(1)
end

-- Basit HTTP server (tek-thread, minimal)
local server = assert(socket.bind("*", 8080))
server:settimeout(0.01)
print("Server listening on port 8080")

local function read_request(client)
    client:settimeout(1)
    local req = {}
    -- read request line
    local first, err = client:receive("*l")
    if not first then return nil, err end
    req.line = first
    req.headers = {}
    -- read headers
    while true do
        local line = client:receive("*l")
        if not line or line == "" then break end
        local k, v = line:match("^(.-):%s*(.*)")
        if k then req.headers[k:lower()] = v end
    end
    local body = ""
    if req.headers["content-length"] then
        local len = tonumber(req.headers["content-length"])
        if len and len > 0 then
            body = client:receive(len)
        end
    end
    req.body = body or ""
    return req
end

local function send_json(client, t)
    local out = json.encode(t)
    local resp = table.concat({
        "HTTP/1.1 200 OK",
        "Content-Type: application/json; charset=utf-8",
        "Content-Length: " .. tostring(#out),
        "",
        out
    }, "\r\n")
    client:send(resp)
end

while true do
    local client = server:accept()
    if client then
        local req, err = read_request(client)
        if req then
            -- basit route: POST /obfuscate { "code": "..." }
            local method, path = req.line:match("^(%S+)%s+(%S+)")
            if method == "POST" and path == "/obfuscate" then
                local ok, parsed = pcall(json.decode, req.body)
                if ok and type(parsed) == "table" and parsed.code then
                    -- placeholder: burada obfuscator fonksiyonunu çağır
                    local obfuscated = "-- obfuscated (placeholder)\\n" .. parsed.code
                    send_json(client, { obfuscated = obfuscated })
                else
                    send_json(client, { error = "invalid json body or missing 'code' field" })
                end
            else
                send_json(client, { status = "ok", info = "use POST /obfuscate" })
            end
        else
            -- if unable to read request, ignore
        end
        client:close()
    else
        -- short sleep to avoid busy loop
        socket.sleep(0.01)
    end
end
